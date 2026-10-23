"""Gemini wrapper checks with a fake credential and no network requests."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('pi_gemini', Path(__file__).with_name('pi_gemini.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class GeminiLauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        (self.home / 'keys').mkdir()
        self.key_file = self.home / 'keys/gemini_allen_key.txt'
        self.key_file.write_text('fake-test-credential\n')
        self.env = patch.dict(os.environ, {'HOME': str(self.home), 'OPENAI_API_KEY': 'fake-other',
                                          'GEMINI_API_KEY': 'wrong-inherited',
                                          'PI_GEMINI_MODEL': 'gemini-3-flash-preview'})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_runtime_key_is_only_in_environment(self):
        cmd, env = module.gemini_command(['-p', '--', 'VeriBench task'])
        self.assertEqual(env['GEMINI_API_KEY'], 'fake-test-credential')
        self.assertNotIn('OPENAI_API_KEY', env)
        self.assertNotIn('fake-test-credential', ' '.join(cmd))
        self.assertEqual(cmd[cmd.index('--provider') + 1], 'google')
        self.assertEqual(env['PI_CODING_AGENT_DIR'], str(self.home / '.local/share/pi-gemini'))

    def test_provider_and_credential_overrides_rejected(self):
        for arg in ('--provider=other', '--api-key=other', '--model=other/model'):
            with self.assertRaises(ValueError): module.gemini_command([arg])

    def test_prompt_text_is_not_parsed_as_an_option(self):
        cmd, _ = module.gemini_command(['--', '--provider=example'])
        self.assertEqual(cmd[-1], '--provider=example')

    def test_model_selection_stays_on_google(self):
        with patch.dict(os.environ, {'PI_GEMINI_MODEL': 'gemini-3.1-pro-preview'}):
            cmd, _ = module.gemini_command([])
            self.assertEqual(cmd[cmd.index('--model') + 1], 'gemini-3.1-pro-preview')
        with patch.dict(os.environ, {'PI_GEMINI_MODEL': 'other/model'}):
            with self.assertRaises(ValueError): module.gemini_command([])

    def test_invalid_key_error_does_not_disclose_contents(self):
        self.key_file.write_text('sensitive value')
        with self.assertRaises(ValueError) as error: module.gemini_command([])
        self.assertNotIn('sensitive', str(error.exception))

    def test_installed_herdr_extension_is_explicitly_loaded(self):
        hook = self.home / '.pi/agent/extensions/herdr-agent-state.ts'
        hook.parent.mkdir(parents=True); hook.write_text('// test fixture\n')
        cmd, _ = module.gemini_command([])
        self.assertEqual(cmd[cmd.index('--extension') + 1], str(hook))
        self.assertIn('--no-extensions', cmd)


if __name__ == '__main__': unittest.main()
