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
                plan.update(provider=provider, allow_unknown_native=True, quota_group='shared-pool')
                plan['auth'] = {'argv': [sys.executable, str(self.fake), status], 'match': match}
                self.write_config([plan])
                r.save(self.state / 'observations.json', {})
                self.assertEqual(self.call(*self.run_args()).returncode, 0)
                self.ready('shared-pool')
                obs = r.observations(self.state)
                obs['shared-pool']['weekly']['used_percent'] = 80
                r.save(self.state / 'observations.json', obs)
                self.assertNotEqual(self.call(*self.run_args()).returncode, 0)
                plan['auth']['argv'][-1] = 'bad-auth'
                self.write_config([plan])
                r.save(self.state / 'observations.json', {})
                self.assertNotEqual(self.call(*self.run_args()).returncode, 0)
                plan['auth'] = {}
                self.write_config([plan])
                self.assertNotEqual(self.call('status').returncode, 0)

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


if __name__ == '__main__':
    from unittest import mock
    unittest.main()
