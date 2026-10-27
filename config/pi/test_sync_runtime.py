import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import sync_runtime as sync


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.agent = self.root/'agent'
        self.manifest = self.root/'runtime.json'
        self.source = self.root/'extension.ts'
        self.source.write_text('export default function() {}')
        self.spec = {'version': 1, 'settings': {'retry': {'maxRetries': 2},
                     'extensions': ['${CONFIG_DIR}/extension.ts']},
                     'trackedFiles': ['extension.ts']}
        self.save()

    def save(self):
        self.manifest.write_text(json.dumps(self.spec))

    def run_sync(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return sync.sync(self.manifest, self.agent, **kwargs)

    def test_check_read_only_on_missing_profile(self):
        with patch.object(sync.subprocess, 'run') as command:
            self.assertEqual(self.run_sync(check=True), 1)
            command.assert_not_called()
        self.assertFalse(self.agent.exists())

    def test_apply_idempotent_preserves_local_settings_and_auth(self):
        self.agent.mkdir()
        sync.write_json(self.agent/'settings.json', {'defaultProvider': 'local', 'retry': {'enabled': False}})
        (self.agent/'auth.json').write_text('do not read or write')
        self.assertEqual(self.run_sync(), 0)
        settings = sync.read_json(self.agent/'settings.json')
        self.assertEqual(settings['defaultProvider'], 'local')
        self.assertEqual(settings['retry'], {'maxRetries': 2, 'enabled': False})
        before = {p.name: p.stat().st_mtime_ns for p in self.agent.iterdir()}
        self.assertEqual(self.run_sync(), 0)
        self.assertEqual(before, {p.name: p.stat().st_mtime_ns for p in self.agent.iterdir()})
        self.assertEqual((self.agent/'auth.json').read_text(), 'do not read or write')

    def test_shared_model_defaults_replace_local_choices_and_preserve_auth(self):
        shared = sync.read_json(Path(__file__).with_name('runtime.json'))['settings']
        expected = {
            'defaultProvider': 'koyejolab-openai-bm',
            'defaultModel': 'gpt-6.1-sol',
            'defaultThinkingLevel': 'medium',
            'modelThinkingLevels': {'koyejolab-openai-bm/gpt-6.1-sol': 'medium'},
        }
        for key, value in expected.items():
            self.assertEqual(shared[key], value)
        self.spec['settings'].update(expected)
        self.save()
        self.agent.mkdir()
        sync.write_json(self.agent/'settings.json', {
            'defaultProvider': 'old', 'defaultModel': 'old',
            'defaultThinkingLevel': 'high', 'theme': 'dark',
            'modelThinkingLevels': {'koyejolab-openai-bm/gpt-6.1-sol': 'high',
                                    'other/model': 'low'},
        })
        auth = self.agent/'auth.json'
        auth.write_text('private fixture: unchanged')
        self.assertEqual(self.run_sync(), 0)
        actual = sync.read_json(self.agent/'settings.json')
        for key in ('defaultProvider', 'defaultModel', 'defaultThinkingLevel'):
            self.assertEqual(actual[key], expected[key])
        self.assertEqual(actual['modelThinkingLevels'], {
            'koyejolab-openai-bm/gpt-6.1-sol': 'medium', 'other/model': 'low'})
        self.assertEqual(actual['theme'], 'dark')
        self.assertEqual(auth.read_text(), 'private fixture: unchanged')
        self.assertEqual(self.run_sync(check=True), 0)

    def test_setting_drift_and_source_drift(self):
        self.run_sync()
        data = sync.read_json(self.agent/'settings.json')
        data['retry']['maxRetries'] = 99
        sync.write_json(self.agent/'settings.json', data)
        self.assertEqual(self.run_sync(check=True), 1)
        self.assertEqual(self.run_sync(), 0)
        self.source.write_text('changed')
        self.assertEqual(self.run_sync(check=True), 1)
        self.assertEqual(self.run_sync(), 0)

    def test_removed_owned_setting_retired_but_modified_value_preserved(self):
        self.run_sync()
        del self.spec['settings']['retry']
        self.save()
        self.assertEqual(self.run_sync(), 0)
        self.assertNotIn('maxRetries', sync.read_json(self.agent/'settings.json')['retry'])

    def test_unmanaged_extension_reported_and_preserved(self):
        (self.agent/'extensions').mkdir(parents=True)
        extra = self.agent/'extensions/local.ts'
        extra.write_text('custom')
        self.assertEqual(self.run_sync(), 1)
        self.assertEqual(extra.read_text(), 'custom')
        self.spec['externalExtensions'] = ['local.ts']
        self.save()
        self.assertEqual(self.run_sync(), 0)

    def test_host_overlay_and_portable_paths(self):
        override = self.root/'host.json'
        override.write_text('{"settings":{"retry":{"maxRetries":4}}}')
        self.assertEqual(self.run_sync(host_config=override), 0)
        data = sync.read_json(self.agent/'settings.json')
        self.assertEqual(data['retry']['maxRetries'], 4)
        self.assertEqual(data['extensions'], [str(self.source)])

    def test_invalid_manifest_does_not_mutate(self):
        self.spec['settings']['packages'] = ['npm:package@latest']
        self.save()
        with self.assertRaises(ValueError):
            self.run_sync()
        self.assertFalse(self.agent.exists())

    def test_missing_npm_then_install_and_version_drift(self):
        self.spec['settings']['packages'] = ['npm:@test/tool@1.2.3']
        self.save()
        installed = self.agent/'npm/node_modules/@test/tool/package.json'
        def install(command, **kwargs):
            self.assertEqual(command, ['pi', 'install', 'npm:@test/tool@1.2.3'])
            self.assertEqual(kwargs['env']['PI_CODING_AGENT_DIR'], str(self.agent))
            installed.parent.mkdir(parents=True)
            installed.write_text('{"version":"1.2.3"}')
            return subprocess.CompletedProcess(command, 0)
        with patch.object(sync.subprocess, 'run', side_effect=install):
            self.assertEqual(self.run_sync(), 0)
        installed.write_text('{"version":"1.2.4"}')
        with patch.object(sync.subprocess, 'run') as command:
            self.assertEqual(self.run_sync(check=True), 1)
            command.assert_not_called()

    def test_package_failure_does_not_record_success(self):
        self.spec['settings']['packages'] = ['npm:tool@1.2.3']
        self.save()
        with patch.object(sync.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)):
            with self.assertRaises(ValueError):
                self.run_sync()
        self.assertFalse((self.agent/sync.STATE).exists())

    def test_cli_check_does_not_touch_models_or_need_catalog(self):
        result = subprocess.run(['python3', str(Path(__file__).with_name('install.py')), '--check',
                                 '--agent-dir', str(self.agent), '--runtime-manifest', str(self.manifest)],
                                 capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertFalse(self.agent.exists())

    def test_git_dirty_checkout_is_preserved_even_at_wrong_commit(self):
        checkout = self.agent/'git/example.invalid/owner/repo'
        checkout.mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(checkout)], check=True)
        source = checkout/'extension.ts'
        source.write_text('original')
        subprocess.run(['git', '-C', str(checkout), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(checkout), '-c', 'user.name=Test',
                        '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture'], check=True)
        source.write_text('uncommitted work')
        self.spec['settings']['packages'] = ['git:example.invalid/owner/repo@' + '0'*40]
        self.save()
        with self.assertRaisesRegex(ValueError, 'local edits'):
            self.run_sync()
        self.assertEqual(source.read_text(), 'uncommitted work')
        self.assertFalse((self.agent/'settings.json').exists())

    def test_resource_lists_are_backed_up_before_replacement(self):
        self.agent.mkdir()
        settings = self.agent/'settings.json'
        settings.write_text('{"extensions":["local.ts"],"theme":"dark"}')
        self.assertEqual(self.run_sync(), 0)
        backups = list(self.agent.glob('settings.json.before-sync-*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(sync.read_json(backups[0])['extensions'], ['local.ts'])
        self.assertEqual(sync.read_json(settings)['theme'], 'dark')

    def test_profile_host_override_is_used_by_default(self):
        self.agent.mkdir()
        (self.agent/'agents-config-host.json').write_text('{"settings":{"retry":{"maxRetries":7}}}')
        self.assertEqual(self.run_sync(), 0)
        self.assertEqual(sync.read_json(self.agent/'settings.json')['retry']['maxRetries'], 7)
        self.assertEqual(self.run_sync(check=True), 0)

    def test_shared_skill_links_and_tree_drift(self):
        skill = self.root/'skills/example'
        skill.mkdir(parents=True)
        (skill/'SKILL.md').write_text('---\nname: example\ndescription: Example\n---\n')
        links = self.root/'client-skills'
        self.spec['settings']['skills'] = ['${CONFIG_DIR}/skills']
        self.spec['trackedDirectories'] = ['skills']
        self.spec['skillLinkRoots'] = [str(links)]
        self.save()
        self.assertEqual(self.run_sync(check=True), 1)
        self.assertFalse(links.exists())
        self.assertEqual(self.run_sync(), 0)
        self.assertEqual((links/'example').resolve(), skill)
        (skill/'helper.py').write_text('print(1)')
        self.assertEqual(self.run_sync(check=True), 1)
        self.assertEqual(self.run_sync(), 0)
        (skill/'helper.py').unlink()
        self.assertEqual(self.run_sync(check=True), 1)

    def test_local_skill_copy_requires_explicit_adoption(self):
        skill = self.root/'skills/example'
        skill.mkdir(parents=True)
        (skill/'SKILL.md').write_text('canonical')
        links = self.root/'client-skills'
        (links/'example').mkdir(parents=True)
        (links/'example/SKILL.md').write_text('local edits')
        self.spec['settings']['skills'] = ['${CONFIG_DIR}/skills']
        self.spec['skillLinkRoots'] = [str(links)]
        self.save()
        with self.assertRaises(ValueError):
            self.run_sync()
        self.assertEqual((links/'example/SKILL.md').read_text(), 'local edits')
        with patch.object(sync.Path, 'home', return_value=self.root):
            self.assertEqual(self.run_sync(adopt_skills=True), 0)
        backups = list((self.root/'.local/state/agents-config/skill-backups').glob('*/SKILL.md'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), 'local edits')

    def test_optional_private_skill_directory_is_local_and_hashed(self):
        self.spec['privateSkillsDirectory'] = '${CONFIG_DIR}/private-skills'
        self.save()
        self.assertEqual(self.run_sync(), 0)
        private = self.root/'private-skills/example'
        private.mkdir(parents=True)
        (private/'SKILL.md').write_text('private instructions')
        self.assertEqual(self.run_sync(check=True), 1)
        self.assertEqual(self.run_sync(), 0)
        self.assertIn(str(private.parent), sync.read_json(self.agent/'settings.json')['skills'])
        (private/'SKILL.md').write_text('private changed')
        self.assertEqual(self.run_sync(check=True), 1)

    def test_skills_folder_may_be_a_link_to_the_repository_skills(self):
        repo = self.root/'repo'
        (repo/'config/pi').mkdir(parents=True)
        (repo/'skills/example').mkdir(parents=True)
        (repo/'skills/example/SKILL.md').write_text('---\nname: example\ndescription: Example\n---\n')
        (repo/'config/pi/skills').symlink_to('../../skills')
        links = self.root/'client-skills'
        self.spec = {'version': 1, 'settings': {'skills': ['${CONFIG_DIR}/skills']},
                     'trackedDirectories': ['skills'], 'skillLinkRoots': [str(links)]}
        self.manifest = repo/'config/pi/runtime.json'
        self.save()
        self.assertEqual(self.run_sync(), 0)
        self.assertEqual((links/'example').resolve(), repo/'skills/example')
        self.assertEqual(self.run_sync(check=True), 0)
        (repo/'skills/example/helper.py').write_text('print(1)')
        self.assertEqual(self.run_sync(check=True), 1)

    def test_tracked_directory_cannot_link_outside_the_repository(self):
        repo = self.root/'repo'
        (repo/'config/pi').mkdir(parents=True)
        (self.root/'elsewhere').mkdir()
        (repo/'config/pi/skills').symlink_to('../../../elsewhere')
        self.spec = {'version': 1, 'settings': {}, 'trackedDirectories': ['skills']}
        self.manifest = repo/'config/pi/runtime.json'
        self.save()
        with self.assertRaises(ValueError):
            self.run_sync()

    def test_invalid_tracked_file_does_not_mutate(self):
        self.spec['trackedFiles'] = ['missing.ts']
        self.save()
        with self.assertRaises(ValueError):
            self.run_sync()
        self.assertFalse(self.agent.exists())


if __name__ == '__main__':
    unittest.main()
