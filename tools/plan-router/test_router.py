"""Deterministic fake-client checks: no providers, accounts or inference involved."""
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
from unittest import mock
import subprocess
import sys
import tempfile
import time
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('router', HERE / 'router.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
FUTURE = '2099-01-01T00:00:00Z'
PAST = '2000-01-01T00:00:00Z'


class RouterTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='plan-router-test-', dir='/tmp')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.state = r.private_dir(self.base / 'private')
        self.workspace = self.base / 'workspace'
        self.workspace.mkdir()
        self.prompt = self.base / 'prompt.txt'
        self.prompt.write_text('verbatim prompt $dollars `backticks`\nsecond line')
        self.fake = self.base / 'fake.py'
        self.fake.write_text('''import json, os, pathlib, subprocess, sys, time
args=sys.argv[1:]
if args[0]=='auth':
    print(json.dumps({'authMethod':'claude.ai','loggedIn':True,'apiProvider':'firstParty'})); sys.exit(0)
if args[0]=='bad-auth':
    print(json.dumps({'authMethod':'api_key'})); sys.exit(0)
if args[0]=='sleep':
    child=subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(60)'])
    pathlib.Path('child-pid').write_text(str(child.pid))
    time.sleep(60)
if args[0]=='wait':
    pathlib.Path('started').write_text('yes'); time.sleep(60)
if args[0]=='fail':
    pathlib.Path('partial-work').write_text('keep me'); print('quota reached'); sys.exit(1)
if args[0]=='argument':
    value=args[1]
else:
    value=sys.stdin.read()
print(json.dumps({'usage':{'input_tokens':7, 'output_tokens':3},'received':value, 'secret_present':'OPENAI_API_KEY' in os.environ}))
''')
        self.plan = {'id': 'first', 'provider': 'claude', 'model': 'frontier-test',
                     'argv': [sys.executable, str(self.fake), 'ok', '--model', 'frontier-test'],
                     'auth': {'argv': [sys.executable, str(self.fake), 'auth']},
                     'timeout_seconds': 3, 'generic_fallback': True,
                     'subscription_only': {'verified': True, 'expires_at': FUTURE, 'evidence': 'fake test fixture'}}
        self.config = self.base / 'config.json'
        self.write_config([self.plan])
        self.ready('first')

    def write_config(self, plans):
        self.config.write_text(json.dumps({'default_plan': 'first', 'plans': plans}))

    def ready(self, name):
        obs = r.observations(self.state)
        obs[name] = {window: {'observed_at': r.stamp(), 'expires_at': FUTURE,
                             'reset_at': FUTURE, 'status': 'ready', 'used_percent': 5}
                     for window in ('weekly', 'short')}
        r.save(self.state / 'observations.json', obs)

    def command(self, *args):
        return [sys.executable, str(HERE / 'router.py'), '--config', str(self.config),
                '--state-dir', str(self.state), *args]

    def call(self, *args):
        return subprocess.run(self.command(*args), capture_output=True, text=True, timeout=10)

    def run_args(self, *extra):
        return ['run', '--workspace', str(self.workspace), '--prompt-file', str(self.prompt), *extra]

    def receipts(self):
        return [json.loads(p.read_text()) for p in self.state.glob('jobs/*/receipt.json')]

    def test_stdin_scrub_tokens_and_private_logs(self):
        with mock.patch.dict(os.environ, {'OPENAI_API_KEY': 'fake-do-not-use', 'GOOGLE_APPLICATION_CREDENTIALS': '/fake'}):
            output = self.call(*self.run_args())
        self.assertEqual(output.returncode, 0, output.stderr)
        result = json.loads(output.stdout)
        self.assertEqual(result['tokens'], {'input_tokens': 7, 'output_tokens': 3})
        body = json.loads((Path(result['logs']) / 'stdout').read_text())
        self.assertEqual(body['received'], self.prompt.read_text())
        self.assertFalse(body['secret_present'])
        self.assertEqual((Path(result['logs']) / 'stdout').stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o700)

    def test_quota_thresholds_unknown_and_expiry_fail_closed(self):
        obs = r.observations(self.state)
        for window, value in [('weekly', 80), ('short', 100)]:
            changed = copy.deepcopy(obs)
            changed['first'][window]['used_percent'] = value
            self.assertIn('threshold', r.gate(self.plan, changed, time.time()))
        changed = copy.deepcopy(obs)
        changed['first']['weekly']['expires_at'] = PAST
        self.assertIn('stale', r.gate(self.plan, changed, time.time()))
        self.assertIn('unknown', r.gate(self.plan, {}, time.time()))
        plan = copy.deepcopy(self.plan)
        plan['subscription_only']['verified'] = False
        self.assertIn('verification', r.gate(plan, obs, time.time()))

    def test_explicit_generic_fallback_auth_only(self):
        second = copy.deepcopy(self.plan)
        second['id'] = 'second'
        self.ready('second')
        self.plan['auth']['argv'][-1] = 'bad-auth'
        self.write_config([self.plan, second])
        self.assertNotEqual(self.call(*self.run_args()).returncode, 0)
        self.assertNotEqual(self.call(*self.run_args('--allow-fallback')).returncode, 0)
        result = self.call(*self.run_args('--generic', '--allow-fallback'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['plan'], 'second')
        self.assertEqual(len(self.receipts()), 1)

    def test_partial_tool_work_never_falls_back(self):
        second = copy.deepcopy(self.plan)
        second['id'] = 'second'
        self.ready('second')
        self.plan['argv'][2] = 'fail'
        self.write_config([self.plan, second])
        result = self.call(*self.run_args('--generic', '--allow-fallback'))
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue((self.workspace / 'partial-work').exists())
        self.assertEqual([x['plan'] for x in self.receipts()], ['first'])

    def test_timeout_kills_owned_group_and_does_not_fallback(self):
        second = copy.deepcopy(self.plan)
        second['id'] = 'second'
        self.ready('second')
        self.plan.update(timeout_seconds=0.25)
        self.plan['argv'][2] = 'sleep'
        self.write_config([self.plan, second])
        result = self.call(*self.run_args('--generic', '--allow-fallback'))
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(self.receipts()[0]['status'], 'timeout')
        self.assertEqual(len(self.receipts()), 1)
        pid = int((self.workspace / 'child-pid').read_text())
        # An orphan can briefly be a zombie; it must not be running.
        path = Path('/proc') / str(pid) / 'stat'
        if path.exists():
            self.assertEqual(path.read_text().split()[2], 'Z')

    def test_two_process_workspace_lock(self):
        self.plan['argv'][2] = 'wait'
        self.write_config([self.plan])
        proc = subprocess.Popen(self.command(*self.run_args()), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 5
            while not (self.workspace / 'started').exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue((self.workspace / 'started').exists())
            result = self.call(*self.run_args())
            self.assertIn('already has', result.stderr)
            self.assertNotEqual(result.returncode, 0)
        finally:
            proc.terminate()
            proc.communicate(timeout=5)

    def test_prompt_argument_and_observation_validation(self):
        self.plan['argv'] = [sys.executable, str(self.fake), 'argument', '{prompt}', '--model', 'frontier-test']
        self.write_config([self.plan])
        result = self.call(*self.run_args())
        self.assertEqual(result.returncode, 0, result.stderr)
        logs = Path(json.loads(result.stdout)['logs'])
        self.assertEqual(json.loads((logs / 'stdout').read_text())['received'], self.prompt.read_text())
        result = self.call('observe', '--plan', 'first', '--window', 'weekly', '--used-percent', 'nan', '--reset-at', FUTURE, '--expires-at', FUTURE, '--source', 'fake')
        self.assertNotEqual(result.returncode, 0)


    def test_unknown_quota_one_admission_and_known_limit_wins(self):
        self.plan['allow_unknown_once'] = True
        self.write_config([self.plan])
        obs = {'first': {'availability': {'observed_at': r.stamp(), 'expires_at': FUTURE,
                                         'status': 'ready', 'source': 'fake successful request'}}}
        r.save(self.state / 'observations.json', obs)
        first = self.call(*self.run_args())
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self.call(*self.run_args())
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual(len(self.receipts()), 1)
        self.ready('first')
        obs = r.observations(self.state)
        obs['first']['availability'] = {'observed_at': r.stamp(), 'expires_at': FUTURE, 'status': 'ready'}
        obs['first']['weekly']['used_percent'] = 80
        self.assertIn('threshold', r.gate(self.plan, obs, time.time()))

    def test_native_refresh_selects_model_pool(self):
        meter = self.base / 'meter.py'
        meter.write_text("print('Gemini Models\\tWeekly Limit Remaining\\t94%\\t2099-01-01T00:00:00Z'); print('Gemini Models\\tFive Hour Limit Remaining\\t91%\\t2099-01-01T00:00:00Z'); print('Claude and GPT models\\tWeekly Limit Remaining\\t1%\\t2099-01-01T00:00:00Z')".replace('\\t', '\\t'))
        self.plan.update(refresh_argv=[sys.executable, str(meter)], refresh_group='Gemini Models')
        self.write_config([self.plan])
        result = self.call('refresh', '--plan', 'first')
        self.assertEqual(result.returncode, 0, result.stderr)
        obs = r.observations(self.state)['first']
        self.assertEqual(obs['weekly']['used_percent'], 6)
        self.assertEqual(obs['short']['used_percent'], 9)
        self.assertLess(r.epoch(obs['weekly']['expires_at']), time.time() + 901)

    def test_codex_native_status_stderr_and_no_api_acceptance(self):
        path = self.base / 'native.stdout'
        path.write_text('')
        path.with_suffix('.stderr').write_text('Logged in using ChatGPT')
        self.assertTrue(r.auth_ok({'provider': 'codex'}, path))
        path.with_suffix('.stderr').write_text('Logged in using API key')
        self.assertFalse(r.auth_ok({'provider': 'codex'}, path))

    def test_structured_zero_exit_error_is_not_completed(self):
        path = self.base / 'result.json'
        for result in ({'type':'result','is_error':True,'result':'quota exceeded'},
                       {'type':'turn.failed','error':{'message':'quota'}},
                       {'status':'ERROR','response':'request failed'},
                       {'type':'result','subtype':'error_max_turns'}):
            path.write_text(json.dumps(result))
            self.assertTrue(r.result_error(path))
        path.write_text(json.dumps({'type':'result','is_error':False,'result':'30'}))
        self.assertFalse(r.result_error(path))
        with mock.patch.dict(os.environ, {'CURSOR_AUTH_TOKEN':'fake', 'GROK_API_KEY':'fake'}):
            self.assertNotIn('CURSOR_AUTH_TOKEN', r.environment(self.plan))
            self.assertNotIn('GROK_API_KEY', r.environment(self.plan))
        path = self.base / 'auth.stdout'
        path.write_text(json.dumps({'authMethod':'oauth_token','loggedIn':False,'apiProvider':'firstParty'}))
        self.assertFalse(r.auth_ok(self.plan, path))

    def test_native_auth_and_config_guards(self):
        for method, expected in [('api_key', False), ('claude.ai', True), ('oauth_token', True)]:
            path = self.base / 'auth.stdout'
            path.write_text(json.dumps({'authMethod': method,'loggedIn':True,'apiProvider':'firstParty'}))
            self.assertEqual(r.auth_ok(self.plan, path), expected)
        self.plan['argv'] += ['--dangerously-skip-permissions']
        self.write_config([self.plan])
        with self.assertRaisesRegex(ValueError, 'bypass'):
            r.config(self.config)
        repo = self.base / 'repo'
        (repo / '.git').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'Git'):
            r.private_dir(repo / 'logs', repo)


if __name__ == '__main__':
    from unittest import mock
    unittest.main()
