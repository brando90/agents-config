#!/usr/bin/env python3
"""Tests for plan-rr (wait rule, difficulty tags, personal spare line) and codex-usage.py --gate (2026-11-24, AT-3455).

Runs against a fake HOME with a stub router, a stub codex-usage and a fake `codex app-server`; no account, key or network is touched.
Run: python3 -m unittest tools/plan-router/test_plan_rr.py   (from the agents-config root)
"""
import json, os, stat, subprocess, sys, tempfile, textwrap, time, unittest, datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
RR = HERE / 'plan-rr.py'
USAGE = HERE / 'codex-usage.py'
NON_PERSONAL = ('vals-codex,stanford-codex,stanford-claude,vals-claude-opus,pi:stanford-stair-bm,pi:koyejolab-openai-bm,'
                'native:cursor,native:grok,pi:vals-openai-bm,pi:allen-google-veribench')


def iso(offset_seconds):
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=offset_seconds)).isoformat()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        (self.home / '.local/lib/plan-router').mkdir(parents=True)
        (self.home / '.local/bin').mkdir(parents=True)
        (self.home / '.local/state/plan-router').mkdir(parents=True)
        (self.home / '.local/lib/plan-router/router.py').write_text(textwrap.dedent('''
            import json, sys
            a = sys.argv
            if 'run' in a:
                print(json.dumps({"plan": a[a.index('--plan') + 1], "status": "completed"}))
            elif 'refresh' in a:
                pass
        '''))
        self.prompt = self.home / 'job.md'; self.prompt.write_text('Reply ok.')
        self.ws = self.home / 'ws'; self.ws.mkdir()
        self.set_codex_usage({})

    def tearDown(self):
        self.tmp.cleanup()

    def set_codex_usage(self, used):
        """used: {'personal-codex': 10, ...} percent used of the weekly window; resets in two days."""
        script = textwrap.dedent('''
            import json, sys, time
            home = sys.argv[sys.argv.index('--home') + 1]
            used = %r
            name = {'.codex': 'personal-codex', '.codex-stanford': 'stanford-codex', '.codex-vals-skampere1': 'vals-codex'}[home.rstrip('/').split('/')[-1]]
            u = used.get(name, 1)
            print(json.dumps({"account": "x", "plan": "pro", "credits": {"hasCredits": False}, "ordinaryUsageAllowed": u < 100,
                              "rateLimitReachedType": None if u < 100 else "rate_limit_reached", "observed_at": "now",
                              "primary": {"usedPercent": u, "windowDurationMins": 10080, "resetsAt": time.time() + 172800}}))
        ''') % (used,)
        p = self.home / '.local/bin/codex-usage.py'; p.write_text(script)

    def observe_claude(self, plan, utilization, blocked_in=None):
        path = self.home / '.local/state/plan-router/observations.json'
        obs = json.loads(path.read_text()) if path.exists() else {}
        item = {'status': 'allowed', 'utilization': utilization, 'resets_at': iso(blocked_in or 3600),
                'blocked_until': iso(blocked_in) if blocked_in else None}
        obs.setdefault(plan, {}).setdefault('limit_events', {})['five_hour'] = item
        path.write_text(json.dumps(obs))

    def rr(self, *args, skip=NON_PERSONAL):
        env = dict(os.environ, HOME=str(self.home))
        cmd = [sys.executable, str(RR), '--prompt-file', str(self.prompt), '--workspace', str(self.ws), '--skip', skip, *args]
        return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60)


class WaitRule(Base):
    def test_medium_waits_for_a_lane_back_within_3_hours(self):
        self.observe_claude('vals-claude-opus', 0.85, blocked_in=1800)
        r = self.rr()
        self.assertEqual(r.returncode, 5, r.stderr)
        self.assertIn('WAIT until', r.stderr)
        self.assertIn('vals-claude-opus', r.stderr)
        self.assertTrue(list((self.home / '.local/state/plan-router/queue').glob('*.json')))

    def test_medium_uses_personal_when_nothing_returns_within_3_hours(self):
        self.observe_claude('vals-claude-opus', 0.85, blocked_in=5 * 3600)
        r = self.rr()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('ran personal-codex', r.stderr)

    def test_urgent_goes_personal_at_once(self):
        self.observe_claude('vals-claude-opus', 0.85, blocked_in=1800)
        r = self.rr('--urgent')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('ran personal-codex', r.stderr)

    def test_resume_before_time_stays_queued(self):
        self.observe_claude('vals-claude-opus', 0.85, blocked_in=1800)
        self.rr()
        qid = next((self.home / '.local/state/plan-router/queue').glob('*.json')).stem
        env = dict(os.environ, HOME=str(self.home))
        r = subprocess.run([sys.executable, str(RR), '--resume', qid], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 5, r.stderr)
        self.assertIn('still queued', r.stderr)


class Difficulty(Base):
    def test_light_never_uses_personal(self):
        r = self.rr('--difficulty', 'light', skip=NON_PERSONAL + ',personal-agy')
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertNotIn('ran personal', r.stderr)

    def test_light_order_starts_with_small_lanes(self):
        env = dict(os.environ, HOME=str(self.home))
        r = subprocess.run([sys.executable, str(RR), '--order', '--difficulty', 'light'], capture_output=True, text=True, env=env)
        lines = r.stdout.splitlines()[1:]
        self.assertTrue(lines[0].startswith('native:cursor'))
        self.assertFalse(any(l.startswith(('personal-codex', 'personal-claude')) for l in lines))

    def test_heavy_order_includes_cursor_and_grok_but_not_the_small_keys(self):
        env = dict(os.environ, HOME=str(self.home))
        r = subprocess.run([sys.executable, str(RR), '--order', '--difficulty', 'heavy'], capture_output=True, text=True, env=env)
        names = [l.split()[0] for l in r.stdout.splitlines()[1:]]
        self.assertIn('native:cursor', names)
        self.assertIn('native:grok', names)
        self.assertNotIn('pi:koyejolab-openai-bm', names)
        self.assertLess(names.index('stanford-claude'), names.index('native:cursor'))
        self.assertLess(names.index('native:grok'), names.index('personal-codex'))

    def test_heavy_without_urgent_does_not_use_personal(self):
        r = self.rr('--difficulty', 'heavy')
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertNotIn('ran personal', r.stderr)

    def test_heavy_waits_for_the_first_strong_lane_back_even_beyond_3_hours(self):
        self.observe_claude('stanford-claude', 0.9, blocked_in=5 * 3600)
        r = self.rr('--difficulty', 'heavy')
        self.assertEqual(r.returncode, 5, r.stderr)
        self.assertIn('stanford-claude', r.stderr)

    def test_heavy_urgent_may_use_personal(self):
        r = self.rr('--difficulty', 'heavy', '--urgent')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('ran personal-codex', r.stderr)

    def test_medium_skips_a_personal_lane_that_is_half_used(self):
        self.set_codex_usage({'personal-codex': 60})
        self.observe_claude('personal-claude', 0.2)
        r = self.rr()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('skipped personal-codex', r.stderr)
        self.assertIn('ran personal-claude', r.stderr)


class Agy(Base):
    SKIP_ALL_BUT_AGY = NON_PERSONAL + ',personal-codex,personal-claude'

    def test_light_and_medium_orders_end_with_agy_and_heavy_has_none(self):
        env = dict(os.environ, HOME=str(self.home))
        for d, expect in (('light', True), ('medium', True), ('heavy', False)):
            r = subprocess.run([sys.executable, str(RR), '--order', '--difficulty', d], capture_output=True, text=True, env=env)
            names = [l.split()[0] for l in r.stdout.splitlines()[1:]]
            self.assertEqual('personal-agy' in names, expect, d)
            if expect: self.assertEqual(names[-1].split()[0], 'personal-agy')

    def test_plain_prompt_is_not_refused_for_lacking_a_voice_header(self):
        r = self.rr('--difficulty', 'light', skip=self.SKIP_ALL_BUT_AGY)
        self.assertNotIn('MY VOICE', r.stderr)
        self.assertNotIn('skipped personal-agy heavy', r.stderr)

    def test_daily_cap_of_10_stops_agy(self):
        log = self.home / '.local/state/plan-router/agy-log.jsonl'
        log.write_text(''.join(json.dumps({'day': dt.date.today().isoformat(), 'model': 'x'}) + '\n' for _ in range(10)))
        r = self.rr('--difficulty', 'light', skip=self.SKIP_ALL_BUT_AGY)
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn('daily cap of 10', r.stderr)


def fake_codex(home, used):
    """A fake `codex app-server --stdio` that answers account/read and account/rateLimits/read."""
    bin_dir = home / 'fakebin'; bin_dir.mkdir()
    exe = bin_dir / 'codex'
    exe.write_text('#!/usr/bin/env python3\n' + textwrap.dedent('''
        import json, sys, time
        for line in sys.stdin:
            m = json.loads(line)
            if m.get('method') == 'initialize':
                print(json.dumps({'id': m['id'], 'result': {}}), flush=True)
            elif m.get('method') == 'account/read':
                print(json.dumps({'id': m['id'], 'result': {'account': {'type': 'chatgpt', 'email': 'me@example.com', 'planType': 'pro'}}}), flush=True)
            elif m.get('method') == 'account/rateLimits/read':
                row = {'usedPercent': %d, 'windowDurationMins': 10080, 'resetsAt': time.time() + 86400}
                print(json.dumps({'id': m['id'], 'result': {'ordinaryUsageAllowed': True, 'rateLimitsByLimitId': {'codex': {
                    'primary': row, 'credits': {'hasCredits': False, 'unlimited': False, 'balance': '0'}, 'rateLimitReachedType': None}}}}), flush=True)
    ''') % used)
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    return bin_dir


class GateScript(unittest.TestCase):
    def run_gate(self, used, expect='me@example.com'):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t); bin_dir = fake_codex(t, used)
            env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ['PATH'])
            return subprocess.run([sys.executable, str(USAGE), '--home', str(t), '--gate', '80', '--expect', expect], capture_output=True, text=True, env=env, timeout=40)

    def test_under_reserve_passes_with_the_login_line_the_router_looks_for(self):
        r = self.run_gate(40)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('Logged in using ChatGPT', r.stdout)

    def test_at_or_over_80_percent_is_blocked(self):
        for used in (80, 100):
            r = self.run_gate(used)
            self.assertEqual(r.returncode, 1)
            self.assertIn('reserve', r.stderr)

    def test_wrong_account_is_blocked(self):
        r = self.run_gate(10, expect='other@example.com')
        self.assertEqual(r.returncode, 1)
        self.assertIn('unexpected account', r.stderr)


if __name__ == '__main__':
    unittest.main()
