import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('named_pi_install', Path(__file__).with_name('install.py'))
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.keys = self.root/'keys with spaces'
        self.keys.mkdir()
        self.catalog = self.root/'catalog'
        self.catalog.mkdir()
        self.agent = self.root/'agent'
        self.key = self.keys/'fake.txt'
        self.key.write_text('fake-secret-not-for-production')
        self.key.chmod(0o600)
        self.manifest = {'providers': [{'id': 'personal-test-main', 'provider': 'test', 'keyFile': 'fake.txt'}]}
        self.model = {'id': 'model', 'name': 'Model', 'api': 'openai-responses', 'provider': 'test',
                      'type': 'chat', 'baseUrl': 'https://example.invalid/v1',
                      'cost': {'input': 1, 'output': 2, 'cacheRead': 0, 'cacheWrite': 0},
                      'contextWindow': 12345, 'maxTokens': 1000}
        (self.catalog/'test.json').write_text(json.dumps({'openai-responses': {'chat:model': self.model}}))

    def test_no_literal_secret_and_metadata_preserved(self):
        providers, _ = setup.build_providers(self.manifest, self.catalog, self.keys)
        alias = providers['personal-test-main']
        self.assertNotIn('fake-secret-not-for-production', json.dumps(providers))
        self.assertTrue(alias['apiKey'].startswith('!cat '))
        self.assertIn("'", alias['apiKey'])
        self.assertEqual(alias['models'][0]['cost'], self.model['cost'])
        self.assertEqual(alias['models'][0]['id'], 'model')
        self.assertIn('personal-test-main', alias['models'][0]['name'])

    def test_merge_backup_and_idempotent(self):
        self.agent.mkdir()
        (self.agent/'models.json').write_text('{"providers":{"existing":{"name":"preserve"}}}')
        setup.install(self.manifest, self.catalog, self.keys, self.agent)
        first = (self.agent/'models.json').read_text()
        setup.install(self.manifest, self.catalog, self.keys, self.agent)
        self.assertEqual(first, (self.agent/'models.json').read_text())
        self.assertIn('existing', json.loads(first)['providers'])
        self.assertEqual(len(list(self.agent.glob('models.json.before-named-*'))), 2)
        self.assertEqual((self.agent/'models.json').stat().st_mode & 0o777, 0o600)

    def test_missing_key_skipped(self):
        self.key.unlink()
        providers, notices = setup.build_providers(self.manifest, self.catalog, self.keys)
        self.assertFalse(providers)
        self.assertTrue(notices)

    def test_world_readable_key_rejected(self):
        self.key.chmod(0o644)
        with self.assertRaises(ValueError):
            setup.build_providers(self.manifest, self.catalog, self.keys)

    def test_missing_model_rejected(self):
        self.manifest['providers'][0]['models'] = ['not-real']
        with self.assertRaises(ValueError):
            setup.build_providers(self.manifest, self.catalog, self.keys)


if __name__ == '__main__':
    unittest.main()
