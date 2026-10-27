import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('install_dotfiles', Path(__file__).resolve().parents[1] / 'scripts/install_dotfiles.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DotfilesTests(unittest.TestCase):
    def test_cursor_preserves_user_content(self):
        source = '// user comment\n[\n{"key":"cmd+i","command":"custom"}\n]\n'
        result = module.cursor_config(source, [{'key': 'ctrl+cmd+down', 'command': 'split'}])
        self.assertIn('// user comment', result)
        self.assertIn('"command":"custom"', result)
        self.assertEqual(len(json.loads(module.without_comments(result))), 2)
        self.assertEqual(module.cursor_config(result, [{'key': 'ctrl+cmd+down', 'command': 'split'}]), result)

    def test_empty_and_trailing_comma(self):
        for source in ['[]\n', '[{"key":"x","command":"y"},]\n']:
            result = module.cursor_config(source, [{'key': 'a', 'command': 'b'}])
            self.assertEqual(module.cursor_config(result, [{'key': 'a', 'command': 'b'}]), result)

    def test_strings_are_not_comments(self):
        self.assertEqual(module.without_comments('["https://example.org"] // hi'), '["https://example.org"] ')

    def test_ghostty_idempotent_preserves_settings(self):
        result = module.ghostty_config('font-size = 14\n', Path('/repo/keybindings.conf'))
        self.assertIn('font-size = 14', result)
        self.assertEqual(module.ghostty_config(result, Path('/repo/keybindings.conf')), result)

    def test_migration_checksums(self):
        module.verify_legacy()

    def test_zed_settings_merge_preserves_and_is_idempotent(self):
        shared = module.parse_jsonc((module.ROOT / 'dotfiles/zed/settings.json').read_text())
        source = ('// mine\n{\n  "vim_mode": false, // keep\n  "theme": "Foo",\n'
                  '  "agent": {"dock": "left", "default_model": {"model": "y"}},\n}\n')
        result = module.zed_settings(source, shared)
        live = module.parse_jsonc(result)
        self.assertIn('// mine', result)
        self.assertIn('// keep', result)
        self.assertEqual((live['vim_mode'], live['theme']), (False, 'Foo'))
        self.assertEqual(live['agent']['dock'], 'right')
        self.assertEqual(live['agent']['default_model'], {'model': 'y'})
        self.assertFalse(live['agent']['threads_sidebar']['auto_open'])
        self.assertEqual((live['base_keymap'], live['project_panel']['dock']), ('Cursor', 'left'))
        self.assertEqual(module.zed_settings(result, shared), result)

    def test_zed_settings_from_empty_and_strings_with_slashes(self):
        shared = module.parse_jsonc((module.ROOT / 'dotfiles/zed/settings.json').read_text())
        for source in ['', '{}\n', '{"url": "http://x//y", "agent": {"dock": "left"}}']:
            result = module.zed_settings(source, shared)
            self.assertEqual(module.parse_jsonc(result)['agent']['dock'], 'right')
            self.assertEqual(module.zed_settings(result, shared), result)
        self.assertEqual(module.parse_jsonc(result)['url'], 'http://x//y')

    def test_cli_installs_zed_with_backup_in_throwaway_home(self):
        script = str(module.ROOT / 'scripts/install_dotfiles.py')
        with tempfile.TemporaryDirectory() as home:
            zed = Path(home) / '.config/zed'
            zed.mkdir(parents=True)
            (zed / 'settings.json').write_text('{"vim_mode": true, "agent": {"dock": "left"}}\n')
            (zed / 'keymap.json').write_text('[]\n')
            run = lambda *a: subprocess.run([sys.executable, script, '--home', home, *a], check=True, capture_output=True, text=True).stdout
            self.assertIn('Would update', run())
            self.assertEqual(module.parse_jsonc((zed / 'settings.json').read_text())['agent']['dock'], 'left')
            run('--apply')
            live = module.parse_jsonc((zed / 'settings.json').read_text())
            self.assertEqual((live['agent']['dock'], live['vim_mode']), ('right', True))
            self.assertIn('workspace::ToggleLeftDock', (zed / 'keymap.json').read_text())
            backups = list((Path(home) / '.local/state/agents-config/dotfiles/backups').glob('*/.config/zed/settings.json'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(module.parse_jsonc(backups[0].read_text())['agent']['dock'], 'left')
            self.assertNotIn('Would update: ' + str(zed), run('--apply'))
            self.assertIn('Unchanged: ' + str(zed / 'settings.json'), run())


if __name__ == '__main__':
    unittest.main()
