import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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

    def test_devin_preserves_other_agents_and_preferences(self):
        settings_path = self.root/'settings.json'
        existing = {'devin.acp.preferredAgent': 'devin-cli',
                    'devin.acp.agentEnv': {'other': {'KEEP': 'yes'}, 'pi-acp': {'CUSTOM': 'preserve'}},
                    'devin.acp.enabledAgents': {'other': True}}
        settings_path.write_text(json.dumps(existing))
        setup.configure_devin(settings_path, Path('/test/pi'), self.agent)
        updated = json.loads(settings_path.read_text())
        self.assertEqual(updated['devin.acp.preferredAgent'], 'devin-cli')
        self.assertEqual(updated['devin.acp.agentEnv']['other'], {'KEEP': 'yes'})
        self.assertEqual(updated['devin.acp.agentEnv']['pi-acp']['CUSTOM'], 'preserve')
        self.assertEqual(updated['devin.acp.agentEnv']['pi-acp']['PI_ACP_PI_COMMAND'], '/test/pi')
        self.assertTrue(updated['devin.acp.enabledAgents']['pi-acp'])
        self.assertEqual(len(list(self.root.glob('settings.json.before-pi-providers-*'))), 1)

    def test_catalog_follows_selected_pi(self):
        package = self.root/'package'
        cli = package/'dist/bundle/cli.js'
        cli.parent.mkdir(parents=True)
        cli.touch()
        catalog = package/'node_modules/@earendil-works/pi-ai/dist/providers/data'
        catalog.mkdir(parents=True)
        (catalog/'openai.json').write_text('{}')
        with patch.object(setup.shutil, 'which', return_value=str(cli)), patch.object(setup.subprocess, 'check_output') as npm:
            self.assertEqual(setup.find_catalog(), catalog.resolve())
            npm.assert_not_called()

    def test_catalog_follows_managed_pi_release(self):
        launcher = self.root/'agent/bin/pi'
        launcher.parent.mkdir(parents=True)
        launcher.write_text('#!/bin/sh\n')
        managed = self.root/'agent/install'
        catalog = managed/'releases/1.4.0/node_modules/@earendil-works/pi-ai/dist/providers/data'
        catalog.mkdir(parents=True)
        (catalog/'openai.json').write_text('{}')
        (managed/'current-version').write_text('1.4.0\n')
        with patch.object(setup.shutil, 'which', return_value=str(launcher)), patch.object(setup.subprocess, 'check_output') as npm:
            self.assertEqual(setup.find_catalog(), catalog.resolve())
            npm.assert_not_called()

    def test_managed_pi_version_cannot_escape_release_directory(self):
        launcher = self.root/'agent/bin/pi'
        launcher.parent.mkdir(parents=True)
        launcher.touch()
        managed = self.root/'agent/install'
        managed.mkdir()
        (managed/'current-version').write_text('../../other')
        with patch.object(setup.shutil, 'which', return_value=str(launcher)):
            with self.assertRaises(ValueError):
                setup.find_catalog()

    def test_missing_key_skipped(self):
        self.key.unlink()
        providers, notices = setup.build_providers(self.manifest, self.catalog, self.keys)
        self.assertFalse(providers)
        self.assertTrue(notices)

    def test_vals_routes_use_separate_private_files_and_keep_metadata(self):
        manifest = json.loads(Path(__file__).with_name('providers.json').read_text())
        entries = {e['id']: e for e in manifest['providers']}
        expected = {'vals-openai-bm': ('openai', 'openai_vals_ai_key.txt'),
                    'vals-anthropic-bm': ('anthropic', 'anthropic_vals_ai_key.txt')}
        for name, (service, filename) in expected.items():
            self.assertEqual(entries[name]['sponsor'], 'vals')
            self.assertEqual(entries[name]['provider'], service)
            self.assertEqual(entries[name]['keyFile'], filename)
            key = self.keys/filename
            key.write_text('fake-vals-secret')
            key.chmod(0o600)
            (self.catalog/(service+'.json')).write_text(json.dumps({'api': {'chat:model': self.model}}))
        manifest = {'providers': [entries[name] for name in expected]}
        providers, notices = setup.build_providers(manifest, self.catalog, self.keys)
        self.assertEqual(set(providers), set(expected))
        self.assertFalse(notices)
        self.assertNotIn('fake-vals-secret', json.dumps(providers))
        for name, (_, filename) in expected.items():
            self.assertIn(filename, providers[name]['apiKey'])
            self.assertEqual(providers[name]['models'][0]['cost'], self.model['cost'])
            self.assertIn(name, providers[name]['models'][0]['name'])

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
