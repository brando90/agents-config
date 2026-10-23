import importlib.util
import json
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


if __name__ == '__main__':
    unittest.main()
