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

    def test_zed_keymap_matches_cursor_shortcuts(self):
        text = (module.ROOT / 'dotfiles/zed/keymap.json').read_text()
        duplicates = []

        def no_duplicates(pairs):
            keys = [key for key, _ in pairs]
            duplicates.extend(key for key in keys if keys.count(key) > 1)
            return dict(pairs)

        blocks = json.loads(module.without_comments(text).replace(',]', ']'), object_pairs_hook=no_duplicates)
        self.assertEqual(duplicates, [])
        bound = {(block['context'], key): action for block in blocks for key, action in block['bindings'].items()}
        # Cursor: Cmd+Opt+S is Save All, Cmd+E the agent layout, Cmd+Opt+F Replace; Brando's Cursor split and focus keys.
        self.assertEqual(bound[('Workspace', 'cmd-alt-s')], 'workspace::SaveAll')
        self.assertEqual(bound[('Workspace', 'cmd-e')], 'multi_workspace::ToggleWorkspaceSidebar')
        self.assertEqual(bound[('Editor && mode == full', 'cmd-alt-f')], 'buffer_search::DeployReplace')
        self.assertEqual(bound[('Pane', 'ctrl-cmd-down')], 'pane::SplitDown')
        self.assertEqual(bound[('Pane', 'ctrl-cmd-right')], 'pane::SplitRight')
        self.assertEqual(bound[('Workspace', 'ctrl-alt-cmd-left')], 'workspace::ActivatePaneLeft')
        cursor = json.loads(module.without_comments((module.ROOT / 'dotfiles/cursor/keybindings.json').read_text()))
        self.assertEqual(len(cursor), 6)

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

    def test_zed_settings_edge_cases(self):
        shared = module.parse_jsonc((module.ROOT / 'dotfiles/zed/settings.json').read_text())
        cases = {
            'comment after last value': '{\n  "vim_mode": true // enable vim\n}\n',
            'comma-brace inside string': '{"agent": {"dock": "left", "note": "a, }"}}',
            'comment beside managed value': '{\n  "base_keymap": "VSCode" /* mine */,\n  "vim_mode": true\n}',
            'trailing comment on managed value': '{\n  "vim_mode": true,\n  "base_keymap": "VSCode" // keep me\n}',
            'crlf': '{\r\n  "vim_mode": true\r\n}\r\n',
            'only comments': '// nothing yet\n',
        }
        for name, source in cases.items():
            if name == 'only comments':
                with self.assertRaises(ValueError):
                    module.zed_settings(source, shared)
                continue
            result = module.zed_settings(source, shared)
            live = module.parse_jsonc(result)
            self.assertEqual(live['base_keymap'], 'Cursor', name)
            self.assertEqual(module.zed_settings(result, shared), result, name)
        self.assertIn('"a, }"', module.zed_settings(cases['comma-brace inside string'], shared))
        self.assertIn('/* mine */', module.zed_settings(cases['comment beside managed value'], shared))
        self.assertIn('// keep me', module.zed_settings(cases['trailing comment on managed value'], shared))
        self.assertIn('// enable vim', module.zed_settings(cases['comment after last value'], shared))
        self.assertNotIn('\n', module.zed_settings(cases['crlf'], shared).replace('\r\n', ''))

    def test_keymap_empty_and_bracket_in_comment(self):
        bindings = [{'context': 'Editor', 'bindings': {'cmd-b': 'x'}}]
        for source in ['', '[]\n// old: [disabled]\n']:
            result = module.cursor_config(source, bindings)
            self.assertEqual(module.cursor_config(result, bindings), result)

    def test_keymap_comment_after_last_entry(self):
        bindings = [{'context': 'Editor', 'bindings': {'cmd-b': 'x'}}]
        result = module.cursor_config('[\n  {"bindings": {"a": "b"}} // mine\n]\n', bindings)
        self.assertIn('// mine', result)
        self.assertEqual(len(module.parse_jsonc(result)), 2)
        self.assertEqual(module.cursor_config(result, bindings), result)

    def test_crlf_and_broken_symlink_in_cli(self):
        script = str(module.ROOT / 'scripts/install_dotfiles.py')
        with tempfile.TemporaryDirectory() as home:
            zed = Path(home) / '.config/zed'
            zed.mkdir(parents=True)
            (zed / 'keymap.json').write_bytes(b'[\r\n  {"bindings": {"a": "b"}}\r\n]\r\n')
            subprocess.run([sys.executable, script, '--home', home, '--apply'], check=True, capture_output=True)
            data = (zed / 'keymap.json').read_bytes()
            self.assertEqual(data.count(b'\n'), data.count(b'\r\n'))
        with tempfile.TemporaryDirectory() as home:
            zed = Path(home) / '.config/zed'
            zed.mkdir(parents=True)
            missing = module.ROOT / 'dotfiles/zed/does-not-exist.json'
            (zed / 'keymap.json').symlink_to(missing)
            result = subprocess.run([sys.executable, script, '--home', home, '--apply'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(missing.exists())

    def test_symlink_into_repo_is_refused(self):
        script = str(module.ROOT / 'scripts/install_dotfiles.py')
        with tempfile.TemporaryDirectory() as home:
            zed = Path(home) / '.config/zed'
            zed.mkdir(parents=True)
            (zed / 'keymap.json').symlink_to(module.ROOT / 'dotfiles/zed/keymap.json')
            before = (module.ROOT / 'dotfiles/zed/keymap.json').read_text()
            result = subprocess.run([sys.executable, script, '--home', home, '--apply'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((module.ROOT / 'dotfiles/zed/keymap.json').read_text(), before)


if __name__ == '__main__':
    unittest.main()
