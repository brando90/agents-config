"""Tests for plan-attest-auto with a fake claude that prints stream-json events. Run: python3 test_attest_auto.py"""
import json, os, subprocess, sys, tempfile, unittest, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))
ROUTER = os.environ.get('PLAN_ROUTER_PY', os.path.join(HERE, 'router.py'))
TOOL = os.path.join(HERE, 'plan-attest-auto.py')

def fake(d, status='allowed', overage='rejected', using=False, util=0.26, rc=0, result=True):
    p = os.path.join(d, 'fakeclaude')
    ev = [{'type': 'rate_limit_event', 'rate_limit_info': {'status': status, 'rateLimitType': 'five_hour', 'resetsAt': 4102444800, 'overageStatus': overage, 'isUsingOverage': using, 'unifiedWindows': {'five_hour': {'utilization': util}}}}]
    if result: ev.append({'type': 'result', 'is_error': False, 'result': 'OK'})
    open(p, 'w').write('#!/bin/sh\ncat >/dev/null\ncat <<"EOF"\n' + '\n'.join(json.dumps(e) for e in ev) + '\nEOF\nexit %d\n' % rc); os.chmod(p, 0o755); return p

class T(unittest.TestCase):
    def setup(self, left_hours, **kw):
        d = tempfile.mkdtemp(); self.d = d
        exp = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=left_hours)).isoformat()
        c = {'plans': [{'id': 'stanford-claude', 'enabled': True, 'argv': [fake(d, **kw), '-p', '--max-turns', '8'], 'subscription_only': {'verified': True, 'evidence': 'old', 'expires_at': exp}},
                       {'id': 'other', 'enabled': True, 'subscription_only': {'verified': True, 'evidence': 'keep', 'expires_at': exp}}]}
        self.cfg = os.path.join(d, 'config.json'); json.dump(c, open(self.cfg, 'w'))
        self.env = dict(os.environ, PLAN_ROUTER_PY=ROUTER, PLAN_ATTEST_LOG=os.path.join(d, 'log.jsonl'))
    def run_tool(self, *a):
        return subprocess.run([sys.executable, TOOL, '--config', self.cfg, *a], capture_output=True, text=True, env=self.env)
    def plan(self, i=0): return json.load(open(self.cfg))['plans'][i]
    def exp(self, i=0): return dt.datetime.fromisoformat(self.plan(i)['subscription_only']['expires_at']).timestamp() - dt.datetime.now(dt.timezone.utc).timestamp()

    def test_expired_is_renewed_for_24h(self):
        self.setup(-1); r = self.run_tool(); self.assertEqual(r.returncode, 0, r.stderr)
        self.assertGreater(self.exp(), 23.9 * 3600); self.assertIn('overageStatus rejected', self.plan()['subscription_only']['evidence'])
        self.assertEqual(self.plan(1)['subscription_only']['evidence'], 'keep')
    def test_past_expiry_lane_gate_opens(self):  # lapses after 24 h, is renewed before the next job
        self.setup(0.5); r = self.run_tool(); self.assertEqual(r.returncode, 0); self.assertGreater(self.exp(), 23.9 * 3600)
    def test_fresh_not_touched(self):
        self.setup(20); before = open(self.cfg).read(); r = self.run_tool(); self.assertEqual(r.returncode, 0); self.assertEqual(open(self.cfg).read(), before)
    def test_overage_not_rejected_blocks(self):
        for kw in ({'overage': 'allowed'}, {'using': True}, {'status': 'allowed_warning'}, {'util': 0.85}, {'result': False}, {'rc': 1}):
            self.setup(-1, **kw); r = self.run_tool(); self.assertEqual(r.returncode, 1, kw); self.assertLess(self.exp(), 0, kw)
    def test_unexpired_but_blocked_returns_ok_and_keeps_old(self):
        self.setup(2, overage='allowed'); r = self.run_tool(); self.assertEqual(r.returncode, 0); self.assertLess(self.exp(), 2.1 * 3600)
    def test_disabled_plan_not_renewed(self):
        self.setup(-1); c = json.load(open(self.cfg)); c['plans'][0]['enabled'] = False; json.dump(c, open(self.cfg, 'w'))
        r = self.run_tool(); self.assertEqual(r.returncode, 1); self.assertLess(self.exp(), 0)
    def test_failed_try_not_repeated_within_10_min(self):
        self.setup(-1, overage='allowed'); self.run_tool(); n = len(open(self.env['PLAN_ATTEST_LOG']).read().splitlines())
        r = self.run_tool(); self.assertEqual(r.returncode, 1); self.assertIn('not trying again', r.stderr)
        self.assertEqual(len(open(self.env['PLAN_ATTEST_LOG']).read().splitlines()), n)
if __name__ == '__main__': unittest.main()
