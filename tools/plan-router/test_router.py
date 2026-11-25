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
if args[0]=='cursor-auth':
    print('Logged in as test@example.invalid'); sys.exit(0)
if args[0]=='grok-auth':
    print('You are logged in with grok.com.'); sys.exit(0)
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
        self.config.write_text(json.dumps({'default_plan': 'first' if any(p['id'] == 'first' for p in plans) else plans[0]['id'], 'plans': plans}))

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
        self.plan.update(timeout_seconds=1.5)
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

    def test_native_success_can_renew_unknown_availability_but_failure_cannot(self):
        self.plan.update(allow_unknown_once=True, renew_availability_on_success=True)
        self.write_config([self.plan])
        obs = {'first': {'availability': {'observed_at': r.stamp(), 'expires_at': FUTURE,
                                         'status': 'ready', 'source': 'native success'}}}
        r.save(self.state / 'observations.json', obs)
        for _ in range(2):
            result = self.call(*self.run_args())
            self.assertEqual(result.returncode, 0, result.stderr)
        self.plan['argv'][2] = 'fail'
        self.write_config([self.plan])
        self.assertEqual(self.call(*self.run_args()).returncode, 1)
        result = self.call(*self.run_args())
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.receipts()), 3)
        self.assertEqual(sorted(x['status'] for x in self.receipts()), ['completed', 'completed', 'failed'])

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

    def test_native_refresh_treats_disabled_window_as_used(self):
        meter = self.base / 'meter.py'
        meter.write_text("print('Claude and GPT models\\tWeekly Limit Remaining\\t0%\\t2099-01-01T00:00:00Z'); print('Claude and GPT models\\tFive Hour Limit Remaining\\tdisabled\\t')")
        self.plan.update(refresh_argv=[sys.executable, str(meter)], refresh_group='Claude and GPT models')
        self.write_config([self.plan])
        self.assertEqual(self.call('status', '--refresh').returncode, 0)
        obs = r.observations(self.state)['first']
        self.assertEqual(obs['short']['used_percent'], 100)
        self.assertEqual(obs['weekly']['used_percent'], 100)

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

    def test_mixed_native_auth_failure_overrides_positive_status(self):
        path = self.base / 'auth.stdout'
        path.with_suffix('.stderr').write_text('')
        for provider, positive in [('cursor', 'Logged in as test@example.invalid'),
                                   ('grok', 'You are logged in with grok.com')]:
            plan = {'provider': provider, 'auth': {'match': 'Logged in as|logged in with'}}
            path.write_text(positive)
            self.assertTrue(r.auth_ok(plan, path))
            for failure in ['Authentication required', 'not signed in',
                            'unable to fetch user details', 'invalid session']:
                with self.subTest(provider=provider, failure=failure):
                    path.with_suffix('.stderr').write_text(failure)
                    self.assertFalse(r.auth_ok(plan, path))
            path.with_suffix('.stderr').write_text('')

    def test_cursor_native_token_counters_do_not_double_count_model_usage(self):
        path = self.base / 'cursor.stdout'
        path.write_text(json.dumps({
            'type': 'result', 'subtype': 'success',
            'usage': {'inputTokens': 14045, 'outputTokens': 1128,
                      'cacheReadTokens': 6144, 'cacheWriteTokens': 0},
            'modelUsage': {'selected': {'inputTokens': 14045, 'outputTokens': 1128}}}))
        self.assertEqual(r.token_usage(path), {'input_tokens': 14045, 'output_tokens': 1128,
                                             'cache_read_input_tokens': 6144,
                                             'cache_creation_input_tokens': 0})

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

    def catalog_config(self):
        self.plan['models'] = [
            {'id': name, 'label': name, 'family': family, 'effort': effort,
             'refresh_group': pool, 'quota_group': pool,
             'frontier': frontier, 'enabled': True, 'verified': True}
            for name, family, effort, pool, frontier in [
                ('frontier-test', 'argon', 'medium', 'gemini', True),
                ('argon-high', 'argon', 'high', 'gemini', True),
                ('argon-low', 'argon', 'low', 'gemini', True),
                ('fast-medium', 'fast', 'medium', 'other', False)]]
        data = {'default_plan': 'first', 'plans': [self.plan],
                'difficulty_defaults': {'easy': 'fast-medium', 'medium': 'frontier-test',
                                        'hard': 'argon-high', 'multistep': 'argon-high'},
                'frontier_difficulty_defaults': {'easy': 'argon-low', 'medium': 'frontier-test',
                                                 'hard': 'argon-high', 'multistep': 'argon-high'}}
        self.config.write_text(json.dumps(data))
        self.ready('gemini')
        self.ready('other')
        return data

    def test_difficulty_selection_generic_only_and_scientific_pin(self):
        self.catalog_config()
        self.prompt.write_text('Prove the theorem and explain the root cause')
        result = self.call(*self.run_args())
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt['model'], 'frontier-test')
        self.assertIsNone(receipt['difficulty'])
        result = self.call(*self.run_args('--generic'))
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual((receipt['model'], receipt['effort'], receipt['difficulty']), ('argon-high', 'high', 'hard'))
        self.assertIn('keyword heuristic', receipt['selection_reason'])
        self.assertNotEqual(self.call(*self.run_args('--difficulty', 'easy')).returncode, 0)

    def test_explicit_plan_pin_and_model_family_effort_overrides(self):
        self.catalog_config()
        self.prompt.write_text('Prove a theorem')
        for flags, expected, effort in [(['--generic', '--plan', 'first'], 'frontier-test', 'medium'),
                                        (['--model', 'argon-low'], 'argon-low', 'low'),
                                        (['--model', 'argon'], 'frontier-test', 'medium'),
                                        (['--model', 'argon', '--effort', 'high'], 'argon-high', 'high'),
                                        (['--effort', 'low'], 'argon-low', 'low')]:
            result = self.call(*self.run_args(*flags))
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads(result.stdout)
            self.assertEqual((receipt['model'], receipt['effort']), (expected, effort))
        self.assertNotEqual(self.call(*self.run_args('--generic', '--plan', 'first', '--difficulty', 'hard')).returncode, 0)

    def test_unsupported_effort_and_unverified_model_never_launch(self):
        data = self.catalog_config()
        self.assertIn('unsupported', self.call(*self.run_args('--model', 'argon', '--effort', 'extreme')).stderr)
        self.assertEqual(self.receipts(), [])
        data['plans'][0]['models'][1]['verified'] = False
        self.config.write_text(json.dumps(data))
        result = self.call(*self.run_args('--model', 'argon-high'))
        self.assertIn('unverified', result.stderr)
        self.assertEqual(self.receipts(), [])

    def test_frontier_filter_changes_defaults_but_rejects_explicit_nonfrontier(self):
        self.catalog_config()
        self.prompt.write_text('Fix a typo')
        generic = self.call(*self.run_args('--generic', '--frontier-only'))
        self.assertEqual(generic.returncode, 0, generic.stderr)
        self.assertEqual(json.loads(generic.stdout)['model'], 'argon-low')
        self.assertIn('not frontier', self.call(*self.run_args('--model', 'fast-medium', '--frontier-only')).stderr)

    def test_selected_model_pool_and_per_model_meter(self):
        self.catalog_config()
        obs = r.observations(self.state)
        obs['gemini']['weekly']['used_percent'] = 80
        r.save(self.state / 'observations.json', obs)
        self.assertNotEqual(self.call(*self.run_args('--model', 'argon-high')).returncode, 0)
        passed = self.call(*self.run_args('--model', 'fast-medium'))
        self.assertEqual(passed.returncode, 0, passed.stderr)
        status = json.loads(self.call('status').stdout)
        self.assertEqual(status['jobs'], 1)
        rows = {m['model']: m for m in status['models']}
        self.assertEqual(rows['fast-medium']['completed'], 1)
        self.assertEqual(rows['fast-medium']['tokens']['input_tokens'], 7)
        self.assertEqual(rows['argon-high']['windows']['weekly']['used_percent'], 80)
        self.assertEqual(rows['fast-medium']['windows']['weekly']['used_percent'], 5)
        models = [json.loads(line) for line in self.call('models', '--plan', 'first').stdout.splitlines()]
        self.assertEqual(len(models), 4)

    def test_disabled_route_never_calls_native_refresh_or_inference(self):
        marker = self.base / 'called'
        self.plan.update(enabled=False, refresh_argv=[sys.executable, '-c', "from pathlib import Path; Path("+repr(str(marker))+").touch()"])
        self.write_config([self.plan])
        self.assertEqual(self.call('status', '--refresh').returncode, 0)
        self.assertNotEqual(self.call(*self.run_args()).returncode, 0)
        self.assertFalse(marker.exists())
        self.assertEqual(self.receipts(), [])

    def test_approved_native_unknown_allowance_retains_known_limit(self):
        self.plan['allow_unknown_native'] = True
        self.write_config([self.plan])
        r.save(self.state / 'observations.json', {})
        result = self.call(*self.run_args('--generic'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.call(*self.run_args('--generic')).returncode, 0)
        self.ready('first')
        obs = r.observations(self.state)
        obs['first']['weekly']['used_percent'] = 80
        r.save(self.state / 'observations.json', obs)
        self.assertNotEqual(self.call(*self.run_args('--generic')).returncode, 0)
        self.plan['provider'] = 'agy'
        self.write_config([self.plan])
        self.assertNotEqual(self.call('status').returncode, 0)

    def test_cursor_grok_native_unknown_requires_auth_and_keeps_shared_limit(self):
        for provider, status, match in [('cursor', 'cursor-auth', 'Logged in as'),
                                        ('grok', 'grok-auth', 'logged in with grok\\.com')]:
            with self.subTest(provider=provider):
                plan = copy.deepcopy(self.plan)
                plan.update(provider=provider, allow_unknown_native=True, require_fresh_weekly=True, quota_group='shared-pool')
                plan['auth'] = {'argv': [sys.executable, str(self.fake), status], 'match': match}
                self.write_config([plan])
                r.save(self.state / 'observations.json', {})
                self.assertNotEqual(self.call(*self.run_args()).returncode, 0)  # no weekly observation
                self.ready('shared-pool')
                self.assertEqual(self.call(*self.run_args()).returncode, 0)
                obs = r.observations(self.state)
                obs['shared-pool']['weekly']['used_percent'] = 80
                r.save(self.state / 'observations.json', obs)
                self.assertNotEqual(self.call(*self.run_args()).returncode, 0)
                self.ready('shared-pool')
                plan['auth']['argv'][-1] = 'bad-auth'
                self.write_config([plan])
                self.assertNotEqual(self.call(*self.run_args()).returncode, 0)
                plan['auth'] = {}
                self.write_config([plan])
                self.assertNotEqual(self.call('status').returncode, 0)

    def test_round_robin_native_entries_cannot_bypass_router_gate(self):
        import ast
        tree = ast.parse((HERE / 'plan-rr.py').read_text())
        native = [n for n in ast.walk(tree) if isinstance(n, ast.If) and isinstance(n.test, ast.Call) and isinstance(n.test.func, ast.Attribute) and n.test.func.attr == 'startswith' and n.test.args and isinstance(n.test.args[0], ast.Constant) and n.test.args[0].value == 'native:']
        self.assertEqual(len(native), 1)
        # Branch only maps to the configured plan. A regression adding an execute call fails.
        self.assertFalse(any(isinstance(n, ast.Call) for node in native[0].body for n in ast.walk(node)))
        branches = ast.get_source_segment((HERE / 'plan-rr.py').read_text(), native[0])
        self.assertIn('personal-cursor', branches)
        self.assertIn('personal-grok', branches)

    def timed_plan(self):
        plan = self.reserve_plan()
        plan.update(refresh_format='timed-weekly-json', refresh_argv=['fake-reader'])
        return plan

    def timed_item(self):
        def at(seconds):
            return r.dt.datetime.fromtimestamp(seconds, r.UTC).isoformat()
        return dict(schema='xai-weekly-v1', status='ready', url='https://grok.com/dashboard',
                    observed_at=at(995), expires_at=at(1595), reset_at=at(5000), used_percent=2)

    def timed_execute(self, item, rc=0):
        def execute(argv, prompt, workspace, env, timeout, stdout, stderr):
            stdout.write_text(json.dumps(item) if not isinstance(item, str) else item)
            stderr.write_text('')
            return rc, False
        return execute

    def test_timed_refresh_preserves_capture_and_gate_boundaries(self):
        plan = self.timed_plan()
        for provider in ('cursor', 'grok'):
            plan['provider'] = provider
            for used, blocked in ((0, False), (2.1235, False), (79.99, False), (80, True), (100, True)):
                item = dict(self.timed_item(), used_percent=used)
                with self.subTest(provider=provider, used=used), mock.patch.object(r.time, 'time', return_value=1000), mock.patch.object(r, 'execute', side_effect=self.timed_execute(item)):
                    self.assertTrue(r.refresh(plan, self.state))
                    obs = r.observations(self.state)
                    self.assertEqual(obs['shared-pool']['weekly']['observed_at'], item['observed_at'])
                    self.assertEqual(obs['shared-pool']['weekly']['expires_at'], item['expires_at'])
                    self.assertEqual(bool(r.gate(plan, obs, 1000)), blocked)

    def test_timed_refresh_invalidates_previous_success_on_every_read_failure(self):
        item = self.timed_item()
        cases = [('not JSON', '{broken'), ('array', []), ('missing schema', {}), ('producer failed', dict(item, status='error')),
                 ('wrong origin', dict(item, url='https://example.invalid/dashboard')),
                 ('old read', dict(item, observed_at='1970-01-01T00:06:39+00:00')),
                 ('future read', dict(item, observed_at='1970-01-01T00:16:41+00:00')),
                 ('expired', dict(item, expires_at='1970-01-01T00:16:39+00:00')),
                 ('excess lifetime', dict(item, expires_at='1970-01-01T00:26:36+00:00')),
                 ('reset passed', dict(item, reset_at='1970-01-01T00:16:39+00:00')),
                 ('negative', dict(item, used_percent=-1)), ('over100', dict(item, used_percent=101)),
                 ('nan', dict(item, used_percent=float('nan'))), ('infinite', dict(item, used_percent=float('inf'))),
                 ('text percent', dict(item, used_percent='2')), ('bool percent', dict(item, used_percent=True)),
                 ('missing percent', {k:v for k,v in item.items() if k!='used_percent'}),
                 ('missing date', {k:v for k,v in item.items() if k!='observed_at'}),
                 ('date no timezone', dict(item, observed_at='1970-01-01T00:16:35')),
                 ('date null', dict(item, observed_at=None))]
        plan = self.timed_plan()
        for name, bad in cases:
            with self.subTest(name=name), mock.patch.object(r.time, 'time', return_value=1000):
                with mock.patch.object(r, 'execute', side_effect=self.timed_execute(item)):
                    r.refresh(plan, self.state)
                with mock.patch.object(r, 'execute', side_effect=self.timed_execute(bad)):
                    with self.assertRaises(ValueError):
                        r.refresh(plan, self.state)
                self.assertNotIn('weekly', r.observations(self.state)['shared-pool'])
                self.assertIsNotNone(r.gate(plan, r.observations(self.state), 1000))
        for rc in (1, 2):
            with self.subTest(rc=rc), mock.patch.object(r.time, 'time', return_value=1000):
                with mock.patch.object(r, 'execute', side_effect=self.timed_execute(item)):
                    r.refresh(plan, self.state)
                with mock.patch.object(r, 'execute', side_effect=self.timed_execute(item, rc=rc)):
                    with self.assertRaises(ValueError): r.refresh(plan, self.state)
                self.assertNotIn('weekly', r.observations(self.state)['shared-pool'])

    def test_timed_failed_refresh_never_launches_with_old_good_observation(self):
        plan = self.reserve_plan()
        plan.update(refresh_format='timed-weekly-json', refresh_argv=[sys.executable, '-c', 'print("not JSON")'])
        # Real CLI path: valid previous capture must be removed when the next read fails.
        self.ready('shared-pool')
        self.write_config([plan])
        result = self.call(*self.run_args())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('skipped', result.stderr)
        self.assertEqual(self.receipts(), [])
        self.assertNotIn('weekly', r.observations(self.state)['shared-pool'])

    def reserve_plan(self, provider='cursor'):
        plan = copy.deepcopy(self.plan)
        plan.update(provider=provider, allow_unknown_native=True, require_fresh_weekly=True,
                    quota_group='shared-pool')
        plan['auth'] = {'argv': [sys.executable, str(self.fake), provider + '-auth'],
                        'match': 'Logged in as' if provider == 'cursor' else 'logged in with grok\\.com'}
        return plan

    def test_fresh_weekly_reserve_gate_boundaries_and_unknown_short_window(self):
        plan = self.reserve_plan()
        weekly = {'observed_at': r.stamp(), 'expires_at': FUTURE, 'reset_at': FUTURE,
                  'status': 'ready', 'used_percent': 5}
        now = time.time() + 5
        for used, blocked in [(0, False), (79, False), (79.99, False), (80, True), (80.01, True), (100, True)]:
            with self.subTest(used=used):
                obs = {'shared-pool': {'weekly': {**weekly, 'used_percent': used}}}  # short window unknown
                reason = r.gate(plan, obs, now)
                self.assertEqual(bool(reason), blocked, reason)
                if blocked:
                    self.assertIn('threshold', reason)
        for name, obs in [('no observations', {}),
                          ('no weekly', {'shared-pool': {'short': dict(weekly)}}),
                          ('stale', {'shared-pool': {'weekly': {**weekly, 'expires_at': PAST}}}),
                          ('reset passed', {'shared-pool': {'weekly': {**weekly, 'reset_at': PAST}}}),
                          ('not yet observed', {'shared-pool': {'weekly': {**weekly, 'observed_at': FUTURE}}}),
                          ('not ready', {'shared-pool': {'weekly': {**weekly, 'status': 'unknown'}}}),
                          ('missing percent', {'shared-pool': {'weekly': {k: v for k, v in weekly.items() if k != 'used_percent'}}}),
                          ('nan percent', {'shared-pool': {'weekly': {**weekly, 'used_percent': float('nan')}}}),
                          ('string percent', {'shared-pool': {'weekly': {**weekly, 'used_percent': '5'}}}),
                          ('other group only', {'other': {'weekly': dict(weekly)}})]:
            with self.subTest(name=name):
                self.assertIn('weekly', r.gate(plan, obs, now))
        # A fresh weekly observation alone admits; an observed short window at 100 still blocks.
        self.assertIsNone(r.gate(plan, {'shared-pool': {'weekly': dict(weekly)}}, now))
        both = {'shared-pool': {'weekly': dict(weekly), 'short': {**weekly, 'used_percent': 100}}}
        self.assertIn('short', r.gate(plan, both, now))
        # Entitlement and disabled checks still come first.
        expired = copy.deepcopy(plan)
        expired['subscription_only']['expires_at'] = PAST
        self.assertIn('verification', r.gate(expired, {'shared-pool': {'weekly': dict(weekly)}}, now))
        disabled = {**plan, 'enabled': False}
        self.assertEqual(r.gate(disabled, {'shared-pool': {'weekly': dict(weekly)}}, now), 'plan disabled')
        # Other plans keep their unknown-native behaviour without the flag.
        other = {**plan}
        del other['require_fresh_weekly']
        self.assertIsNone(r.gate(other, {}, now))
        self.assertIsNone(r.gate({**self.plan, 'allow_unknown_native': True}, {}, now))

    def test_fresh_weekly_reserve_blocks_inference_end_to_end_and_config_requires_it(self):
        for provider in ('cursor', 'grok'):
            with self.subTest(provider=provider):
                plan = self.reserve_plan(provider)
                self.write_config([plan])
                before = len(self.receipts())
                r.save(self.state / 'observations.json', {})
                marker = self.workspace / 'started'
                plan['argv'][2] = 'wait'
                self.write_config([plan])
                self.assertNotEqual(self.call(*self.run_args()).returncode, 0)
                self.assertFalse(marker.exists())
                self.assertEqual(len(self.receipts()), before)
                plan['argv'][2] = 'ok'
                self.write_config([plan])
                self.ready('shared-pool')
                obs = r.observations(self.state)
                del obs['shared-pool']['short']  # weekly fresh, short unmetered
                r.save(self.state / 'observations.json', obs)
                self.assertEqual(self.call(*self.run_args()).returncode, 0)
                obs['shared-pool']['weekly']['used_percent'] = 80
                r.save(self.state / 'observations.json', obs)
                self.assertNotEqual(self.call(*self.run_args()).returncode, 0)
                self.assertEqual(len(self.receipts()), before + 1)
                del plan['require_fresh_weekly']
                self.write_config([plan])
                with self.assertRaisesRegex(ValueError, 'require_fresh_weekly'):
                    r.config(self.config)
                plan['require_fresh_weekly'] = 'yes'
                self.write_config([plan])
                with self.assertRaisesRegex(ValueError, 'true or false'):
                    r.config(self.config)

    def test_uncatalogued_default_does_not_inherit_other_plans_model(self):
        data = self.write_config([self.plan])
        data = json.loads(self.config.read_text())
        data['difficulty_defaults'] = {'easy': 'other-provider-model'}
        self.config.write_text(json.dumps(data))
        result = self.call(*self.run_args('--generic', '--difficulty', 'easy'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['model'], self.plan['model'])

    def test_status_refreshes_each_shared_catalog_pool_once(self):
        self.catalog_config()
        meter = self.base / 'pool-meter.py'
        calls = self.base / 'pool-calls.txt'
        meter.write_text("from pathlib import Path\np=Path(" + repr(str(calls)) + "); p.write_text(p.read_text()+'x' if p.exists() else 'x')\n" +
                         "for group,left in [('gemini',91),('partner',72)]:\n for window in ['Weekly Limit Remaining','Five Hour Limit Remaining']: print(group+'\\t'+window+'\\t'+str(left)+'%\\t2099-01-01T00:00:00Z')\n")
        for model in self.plan['models']:
            model['refresh_group'] = model['quota_group'] = 'gemini' if model['family'] == 'argon' else 'partner'
        self.plan.update(refresh_argv=[sys.executable, str(meter)], refresh_group='gemini', quota_group='gemini')
        self.write_config([self.plan])
        result = self.call('status', '--refresh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls.read_text(), 'xx')
        obs = r.observations(self.state)
        self.assertEqual(obs['gemini']['weekly']['used_percent'], 9)
        self.assertEqual(obs['partner']['weekly']['used_percent'], 28)

    def test_model_copy_updates_only_supported_effort_argument(self):
        self.catalog_config()
        target = self.plan['models'][1]
        selected = r.model_copy(self.plan, target)
        self.assertEqual(selected['argv'][selected['argv'].index('--model') + 1], 'argon-high')
        self.assertNotIn('--effort', selected['argv'])  # agy effort is part of its exact model ID
        self.plan['effort_flag'] = '--effort'
        selected = r.model_copy(self.plan, target)
        self.assertEqual(selected['argv'][-2:], ['--effort', 'high'])
        self.plan['argv'] += ['--effort', 'medium']
        self.assertEqual(r.model_copy(self.plan, target)['argv'][-2:], ['--effort', 'high'])


    def limit_plan(self):
        fake = self.base / 'stream_fake.py'
        fake.write_text('''import json, sys, time
mode = sys.argv[1]
print(json.dumps({'type': 'system', 'subtype': 'init'}))
if mode != 'none':
    status = {'allowed': 'allowed', 'warning': 'allowed_warning', 'rejected': 'rejected', 'overage': 'allowed', 'reserve': 'allowed'}[mode]
    info = {'status': status, 'resetsAt': int(time.time()) + 3600, 'rateLimitType': 'five_hour', 'isUsingOverage': mode == 'overage'}
    info['unifiedWindows'] = {'five_hour': {'utilization': {'warning': 0.85, 'reserve': 0.8}.get(mode, 0), 'resetsAt': info['resetsAt'], 'status': status}}
    print(json.dumps({'type': 'rate_limit_event', 'rate_limit_info': info}))
print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'result': 'ok', 'usage': {'input_tokens': 5, 'output_tokens': 2}}))
''')
        plan = copy.deepcopy(self.plan)
        plan.update(allow_unknown_native=True, limit_events=True)
        plan['argv'] = [sys.executable, str(fake), 'allowed', '--model', 'frontier-test', '--output-format', 'stream-json', '--verbose']
        return plan

    def test_limit_events_start_unknown_then_pause_on_warning_rejected_or_overage(self):
        plan = self.limit_plan()
        self.write_config([plan])
        # No reading yet: starts. A stream with no limit event records nothing and stays usable.
        plan['argv'][2] = 'none'
        self.write_config([plan])
        self.assertEqual(self.call('run', '--workspace', str(self.workspace), '--prompt-file', str(self.prompt)).returncode, 0)
        self.assertEqual(r.observations(self.state).get('first', {}).get('limit_events'), None)
        for mode, word in [('allowed', None), ('warning', 'allowed_warning'), ('rejected', 'rejected'), ('overage', 'overage'), ('reserve', '(five_hour)')]:
            with self.subTest(mode=mode):
                r.save(self.state / 'observations.json', {})
                plan['argv'][2] = mode
                self.write_config([plan])
                run = ['run', '--workspace', str(self.workspace), '--prompt-file', str(self.prompt)]
                self.assertEqual(self.call(*run).returncode, 0)
                item = r.observations(self.state)['first']['limit_events']['five_hour']
                self.assertEqual(item['status'], 'rejected' if mode == 'rejected' else ('allowed_warning' if mode == 'warning' else 'allowed'))
                self.assertEqual(item['is_using_overage'], mode == 'overage')
                self.assertEqual(item['utilization'], {'warning': 0.85, 'reserve': 0.8}.get(mode, 0))
                reason = r.gate(plan, r.observations(self.state), time.time())
                if word is None:
                    self.assertIsNone(reason)
                    self.assertIsNone(item['blocked_until'])
                    self.assertEqual(self.call(*run).returncode, 0)
                else:
                    self.assertIn(word, reason)
                    before = len(self.receipts())
                    self.assertNotEqual(self.call(*run).returncode, 0)
                    self.assertEqual(len(self.receipts()), before)  # paused: no inference started
                    # After the reset time the lane opens again.
                    later = time.time() + 7200
                    self.assertIsNone(r.gate(plan, r.observations(self.state), later))

    def test_warn_gate_false_pauses_only_at_80_percent_rejected_or_overage(self):
        """AT-3491 / AT-3494: personal, Vals and Stanford Claude run with warn_gate false: a warning below 80% does not pause."""
        plan = self.limit_plan()
        plan['warn_gate'] = False
        cases = [('allowed_warning', 0.29, False), ('allowed_warning', 0.79, False), ('allowed_warning', None, False),
                 ('allowed_warning', 0.8, True), ('allowed_warning', 85, True), ('allowed', 0.81, True),
                 ('rejected', 0.1, True), ('allowed', 0.1, False)]
        for status, used, blocked in cases:
            with self.subTest(status=status, used=used):
                self.assertEqual(r.item_blocks(plan, {'status': status, 'utilization': used, 'is_using_overage': False}), blocked)
        self.assertTrue(r.item_blocks(plan, {'status': 'allowed', 'utilization': 0.1, 'is_using_overage': True}))
        # Default (warn_gate not false): any warning pauses.
        self.assertTrue(r.item_blocks(copy.deepcopy(self.plan), {'status': 'allowed_warning', 'utilization': 0.29, 'is_using_overage': False}))
        # A stored old warning event (blocked_until set) is re-judged by the gate and self-heals.
        now = time.time()
        stored = {'first': {'limit_events': {'seven_day': {'status': 'allowed_warning', 'utilization': 0.3, 'is_using_overage': False,
                                                            'resets_at': FUTURE, 'blocked_until': FUTURE}}}}
        self.assertIsNone(r.limit_gate(plan, stored, now))
        stored['first']['limit_events']['seven_day']['utilization'] = 0.8
        self.assertIn('until', r.limit_gate(plan, stored, now))

    def test_limit_events_need_stream_json_verbose_and_status_lists_them(self):
        plan = self.limit_plan()
        for drop in ('--verbose', 'stream-json'):
            bad = copy.deepcopy(plan)
            bad['argv'].remove(drop)
            self.write_config([bad])
            with self.assertRaises(ValueError):
                r.config(self.config)
        self.write_config([plan])
        self.assertEqual(self.call('run', '--workspace', str(self.workspace), '--prompt-file', str(self.prompt)).returncode, 0)
        out = self.call('status')
        self.assertEqual(out.returncode, 0, out.stderr)
        row = next(json.loads(x) for x in out.stdout.splitlines() if json.loads(x)['plan'] == 'first')
        self.assertEqual(row['limit_events']['five_hour']['status'], 'allowed')
        self.assertEqual(row['gate'], 'eligible; authentication checked at launch')

    # --- AT-3529: per-lane Codex sign-in folders, and the Cursor/Grok estimate gate ---
    def codex_plan(self, name, home):
        plan = copy.deepcopy(self.plan)
        plan.update(id=name, provider='codex', model='gpt-test', env={'CODEX_HOME': str(home)},
                    argv=[sys.executable, str(self.fake), 'ok', '--sandbox', 'workspace-write', '--model', 'gpt-test',
                          '-c', 'forced_login_method=chatgpt'])
        plan['auth'] = {'argv': [sys.executable, str(self.fake), 'codex-auth']}
        return plan

    def fake_codex_on_path(self):
        bin_dir = self.base / 'bin'
        bin_dir.mkdir(exist_ok=True)
        script = bin_dir / 'codex'
        script.write_text('#!%s\nimport os, sys\nif sys.argv[1:3] == ["login", "status"]:\n    print("Logged in using ChatGPT" if os.path.exists(os.path.join(os.environ["CODEX_HOME"], "auth.json")) else "Not logged in")\n    sys.exit(0)\nsys.exit(2)\n' % sys.executable)
        script.chmod(0o755)
        return mock.patch.dict(os.environ, {'PATH': str(bin_dir) + os.pathsep + os.environ['PATH']})

    def test_codex_lanes_must_have_their_own_sign_in_folder(self):
        a, b = self.codex_plan('lane-a', self.base / 'home-a'), self.codex_plan('lane-b', self.base / 'home-a')
        self.write_config([a, b])
        with self.assertRaisesRegex(ValueError, 'share one CODEX_HOME'):
            r.config(self.config)
        b['env']['CODEX_HOME'] = str(self.base / 'home-b')
        self.write_config([a, b])
        self.assertEqual(len(r.config(self.config)['plans']), 2)
        b['enabled'] = False  # a disabled lane may keep an old folder
        b['env']['CODEX_HOME'] = str(self.base / 'home-a')
        self.write_config([a, b])
        self.assertEqual(len(r.config(self.config)['plans']), 2)

    def test_codex_job_records_login_status_and_waits_for_its_folder(self):
        home = self.base / 'home-a'
        home.mkdir()
        (home / 'auth.json').write_text('{}')
        plan = self.codex_plan('lane-a', home)
        plan['auth'] = {'argv': [sys.executable, str(self.fake), 'argument', 'Logged in using ChatGPT']}
        plan['home_lock_wait_seconds'] = 1
        self.write_config([plan])
        self.ready('lane-a')
        with self.fake_codex_on_path():
            done = subprocess.run(
                self.command('run', '--plan', 'lane-a', '--workspace', str(self.workspace), '--prompt-file', str(self.prompt)),
                capture_output=True, text=True, timeout=10)
            self.assertEqual(done.returncode, 0, done.stderr)
            receipt = self.receipts()[0]
            self.assertEqual(receipt['codex_home'], os.path.realpath(home))
            self.assertEqual(receipt['codex_login_status'], 'Logged in using ChatGPT')
            # Another job already using this folder: this one waits its turn, then skips instead of sharing auth.json.
            locks = r.private_dir(Path('/tmp') / ('plan-router-' + str(os.getuid())))
            path = locks / ('codex-home-' + __import__('hashlib').sha256(r.codex_home(plan).encode()).hexdigest()[:16] + '.lock')
            with r.home_locked(path, 1):
                busy = subprocess.run(self.command('run', '--plan', 'lane-a', '--workspace', str(self.workspace), '--prompt-file', str(self.prompt)),
                                      capture_output=True, text=True, timeout=10)
            self.assertNotEqual(busy.returncode, 0)
            self.assertIn('another job is using this Codex sign-in folder', busy.stderr)
            self.assertEqual(len(self.receipts()), 1)
            # A folder with no sign-in never starts a job.
            (home / 'auth.json').unlink()
            signed_out = subprocess.run(self.command('run', '--plan', 'lane-a', '--workspace', str(self.workspace), '--prompt-file', str(self.prompt)),
                                        capture_output=True, text=True, timeout=10)
            self.assertNotEqual(signed_out.returncode, 0)
            self.assertEqual(len(self.receipts()), 1)

    def estimate_plan(self, **settings):
        plan = self.reserve_plan()
        plan['estimate_between_readings'] = settings
        return plan

    def old_reading(self, hours_ago, used, reset=FUTURE):
        seen = time.time() - hours_ago * 3600
        stamp = r.dt.datetime.fromtimestamp(seen, r.UTC).isoformat()
        return {'observed_at': stamp, 'reset_at': reset, 'used_percent': used}

    def add_jobs(self, plan_id, hours_ago_list):
        for n, hours in enumerate(hours_ago_list):
            folder = self.state / 'jobs' / ('fake-%s-%d-%s' % (plan_id, n, hours))
            folder.mkdir(parents=True)
            (folder / 'receipt.json').write_text(json.dumps({'plan': plan_id, 'status': 'completed',
                'started_at': r.dt.datetime.fromtimestamp(time.time() - hours * 3600, r.UTC).isoformat()}))

    def test_estimate_between_readings_stops_at_30_percent_left(self):
        plan = self.estimate_plan()
        self.write_config([plan])
        plan = r.config(self.config)['plans'][0]
        item = {**self.old_reading(10, 50), 'expires_at': FUTURE, 'status': 'ready'}
        obs = {'shared-pool': {'weekly': item}}
        now = time.time()
        # No calibration yet: default 1% per job. 50 + 19 jobs = 69 passes, the 20th makes 70 and stops.
        self.add_jobs('first', [5] * 19)
        self.assertIsNone(r.gate(plan, obs, now, self.state))
        self.add_jobs('first', [4])
        reason = r.gate(plan, obs, now, self.state)
        self.assertIn('estimated 70.0% used', reason)
        self.assertIn('stop at 70% used', reason)
        # The reading alone stops at 70, not 80.
        self.assertIn('threshold', r.gate(plan, {'shared-pool': {'weekly': {**item, 'used_percent': 70}}}, now))
        self.assertIsNone(r.gate(plan, {'shared-pool': {'weekly': {**item, 'used_percent': 69.9}}}, now))
        # Jobs of other pools do not count; jobs before the reading do not count.
        self.add_jobs('other', [1] * 30)
        self.add_jobs('first', [20] * 30)
        self.assertEqual(r.estimated_used(plan, self.state, item)[1], 20)

    def test_cost_per_job_is_calibrated_from_daily_readings(self):
        plan = self.estimate_plan()
        self.write_config([plan])
        plan = r.config(self.config)['plans'][0]
        self.assertEqual(r.calibrated_cost(plan, self.state), (1.0, 0))  # default before any pair of readings
        for row in (self.old_reading(80, 10), self.old_reading(56, 14), self.old_reading(32, 15), self.old_reading(8, 16)):
            r.record_reading(self.state, row)
            r.record_reading(self.state, row)  # a reading is kept once
        self.assertEqual(len(r.readings(self.state)), 4)
        self.add_jobs('first', [70, 68, 66, 64, 45, 44, 20, 19])  # 4 jobs for +4, 2 jobs for +1, 2 jobs for +1
        cost, samples = r.calibrated_cost(plan, self.state)
        self.assertEqual(samples, 3)
        self.assertAlmostEqual(cost, 0.5)  # samples 1.0, 0.5, 0.5: median 0.5, latest 0.5
        self.add_jobs('first', [6, 5, 3])  # a latest interval that cost more per job wins over the median
        r.record_reading(self.state, self.old_reading(1, 19))
        self.assertAlmostEqual(r.calibrated_cost(plan, self.state)[0], 1.0)

    def test_refresh_accepts_a_daily_reading_in_estimate_mode_only(self):
        feed = self.base / 'feed.json'
        argv = [sys.executable, '-c', 'import sys;sys.stdout.write(open(%r).read())' % str(feed)]
        for mode, hours, ok in [('estimate', 10, True), ('estimate', 30, False), ('plain', 10, False)]:
            with self.subTest(mode=mode, hours=hours):
                plan = self.estimate_plan() if mode == 'estimate' else self.reserve_plan()
                plan.update(refresh_argv=argv, refresh_format='timed-weekly-json')
                self.write_config([plan])
                plan = r.config(self.config)['plans'][0]
                row = self.old_reading(hours, 20, reset='2099-01-01T00:00:00+00:00')
                feed.write_text(json.dumps({**row, 'schema': 'xai-weekly-v1', 'status': 'ready', 'url': 'https://grok.com/dashboard',
                                            'expires_at': r.dt.datetime.fromtimestamp(time.time() - hours * 3600 + 600, r.UTC).isoformat()}))
                r.save(self.state / 'observations.json', {})
                if ok:
                    self.assertTrue(r.refresh(plan, self.state))
                    weekly = r.observations(self.state)['shared-pool']['weekly']
                    self.assertEqual(weekly['used_percent'], 20)
                    self.assertTrue(r.fresh(weekly, time.time()))
                    self.assertEqual(len(r.readings(self.state)), 1)
                else:
                    with self.assertRaisesRegex(ValueError, 'stale'):
                        r.refresh(plan, self.state)
        # A feed that fails keeps the earlier reading while it is still inside its window.
        plan = self.estimate_plan()
        plan.update(refresh_argv=[sys.executable, '-c', 'import sys;sys.exit(1)'], refresh_format='timed-weekly-json')
        self.write_config([plan])
        plan = r.config(self.config)['plans'][0]
        r.save(self.state / 'observations.json', {'shared-pool': {'weekly': {**self.old_reading(5, 20), 'expires_at': FUTURE, 'status': 'ready'}}})
        self.assertTrue(r.refresh(plan, self.state))


if __name__ == '__main__':
    from unittest import mock
    unittest.main()
