import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


launch = load('launch')
installer = load('install')
ACCOUNTS = json.loads((ROOT / 'accounts.json').read_text())


class AccountsTest(unittest.TestCase):
    def test_personal_unsets_profile_and_keys(self):
        env = launch.account_env(ACCOUNTS[0], {'CLAUDE_CONFIG_DIR': '/wrong', 'ANTHROPIC_API_KEY': 'fake', 'CLAUDE_CODE_OAUTH_TOKEN': 'fake', 'CLAUDE_CODE_USE_VERTEX': '1', 'PATH': '/bin'})
        self.assertEqual(env, {'PATH': '/bin'})

    def test_profiles_are_independent(self):
        source = {'CLAUDE_CONFIG_DIR': '/wrong'}
        vals = launch.account_env(ACCOUNTS[1], source, '/home/test')
        stanford = launch.account_env(ACCOUNTS[2], source, '/home/test')
        self.assertEqual(vals['CLAUDE_CONFIG_DIR'], '/home/test/.claude-vals')
        self.assertEqual(stanford['CLAUDE_CONFIG_DIR'], '/home/test/.claude-su')
        self.assertEqual(source['CLAUDE_CONFIG_DIR'], '/wrong')

    def test_native_plugin_setting_is_scoped_to_child(self):
        args = ['-p', '--settings', '{"enabledPlugins":{"existing":true}}']
        patched = launch.transport_args(args)
        self.assertEqual(json.loads(patched[2])['enabledPlugins'], {'existing': True, 'plugin-authoring@builtin': False})
        self.assertEqual(json.loads(args[2])['enabledPlugins'], {'existing': True})
        self.assertEqual(launch.transport_args(['auth', 'status']), ['auth', 'status'])

    def test_dependency_patch_is_idempotent_and_hash_checked(self):
        patch = load('patch_dependency')
        patch.apply()
        patch.apply()

    def test_exact_identity_required(self):
        a = ACCOUNTS[0]
        status = dict(loggedIn=True, authMethod='claude.ai', apiProvider='firstParty', subscriptionType='max', email=a['email'], orgId=a['orgId'])
        launch.validate_identity(a, status)
        for field, wrong in [('email', 'other@example.com'), ('orgId', 'other'), ('authMethod', 'api_key'), ('loggedIn', False)]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                launch.validate_identity(a, {**status, field: wrong})

    def test_installer_preserves_settings_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            settings = {'defaultProvider': 'openai', 'defaultModel': 'keep-me', 'packages': ['npm:other@1.0.0'], 'extensions': ['/other.ts']}
            (root/'settings.json').write_text(json.dumps(settings))
            installer.install(root, '/bin/claude', '/bin/python3')
            first = (root/'settings.json').read_text()
            installer.install(root, '/bin/claude', '/bin/python3')
            self.assertEqual(first, (root/'settings.json').read_text())
            got = json.loads(first)
            self.assertEqual(got['defaultModel'], 'keep-me')
            self.assertEqual(got['extensions'], ['/other.ts'])
            self.assertEqual(got['packages'], ['npm:other@1.0.0', str(ROOT)])
            for a in ACCOUNTS:
                path = root/'claude-account-bin'/a['id']
                self.assertEqual(path.stat().st_mode & 0o777, 0o700)
                self.assertIn(a['id'], path.read_text())


if __name__ == '__main__':
    unittest.main()
