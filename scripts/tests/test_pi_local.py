"""Launcher contract checks using a fake executable, with no inference or network."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1].joinpath('pi_local.py')
spec = importlib.util.spec_from_file_location('pi_local', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        config = self.home / '.local/share/pi-local'
        config.mkdir(parents=True)
        self.models = config / 'models.json'
        self.models.write_text(json.dumps({'providers': {'ollama-local': {
            'baseUrl': 'http://127.0.0.1:11434/v1',
            'models': [{'id': 'qwen3.5:9b-q4_K_M'}]}}}))
        self.env = patch.dict(os.environ, {'HOME': str(self.home), 'OPENAI_API_KEY': 'test-only'})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_local_endpoint_and_key_environment(self):
        cmd, env = module.local_command(['-p', '--', 'fix the bug'])
        self.assertNotIn('OPENAI_API_KEY', env)
        self.assertEqual(env['OLLAMA_NO_CLOUD'], '1')
        self.assertEqual(cmd[cmd.index('--provider')+1], 'ollama-local')
        self.assertEqual(cmd[-1], 'fix the bug')

    def test_provider_override_rejected(self):
        with self.assertRaises(ValueError): module.local_command(['--provider=paid'])

    def test_herdr_extension_preserves_local_provider(self):
        hook = self.home / '.pi/agent/extensions/herdr-agent-state.ts'
        hook.parent.mkdir(parents=True); hook.write_text('// test fixture\n')
        cmd, env = module.local_command([])
        self.assertEqual(cmd[cmd.index('--extension')+1], str(hook))
        self.assertEqual(cmd[cmd.index('--provider')+1], 'ollama-local')
        self.assertNotIn('GEMINI_API_KEY', env)

    def test_prompt_literal_not_mistaken_for_option(self):
        cmd, _ = module.local_command(['--', '--provider=example'])
        self.assertEqual(cmd[-1], '--provider=example')

    def test_remote_endpoint_rejected(self):
        self.models.write_text(self.models.read_text().replace('127.0.0.1', 'example.com'))
        with self.assertRaises(ValueError): module.local_command([])

    def test_cloud_model_rejected(self):
        self.models.write_text(self.models.read_text().replace('9b-q4_K_M', 'cloud'))
        with self.assertRaises(ValueError): module.local_command([])

    def run_recovery(self, mode, *args):
        launcher = self.home / mode
        launcher.write_text(SOURCE.read_text())
        launcher.chmod(0o755)
        return subprocess.run([str(launcher), *map(str, args)], cwd=self.home,
                              capture_output=True, text=True)

    def test_live_writer_rejected(self):
        result = self.run_recovery('pi-takeover', 'unused.md', '--previous-pid', os.getpid())
        self.assertEqual(result.returncode, 2)
        self.assertIn('still alive', result.stderr)

    def test_missing_quota_evidence_rejected(self):
        checkpoint = self.home / 'checkpoint.md'; checkpoint.write_text('Fix the bug.')
        result = self.run_recovery('pi-resilient', checkpoint)
        self.assertEqual(result.returncode, 2)
        self.assertIn('requires --error-log', result.stderr)

    def test_exit_code_and_hashed_receipt(self):
        subprocess.run(['git', 'init', '-q', str(self.home)], check=True)
        binary = self.home / '.local/bin/pi'; binary.parent.mkdir(parents=True)
        binary.write_text('#!/bin/sh\nexit 7\n'); binary.chmod(0o755)
        checkpoint = self.home / 'checkpoint.md'; checkpoint.write_text('Fix the bug.')
        evidence = self.home / 'error.log'; evidence.write_text('usage limit reached')
        result = self.run_recovery('pi-resilient', checkpoint, '--error-log', evidence, '-p')
        self.assertEqual(result.returncode, 7)
        receipts = list((self.home / '.local/state/pi-local').glob('*/recovery-*.json'))
        self.assertEqual(len(receipts), 1)
        data = json.loads(receipts[0].read_text())
        self.assertEqual(data['exit_code'], 7)
        self.assertEqual(data['status'], 'agent_exited')
        self.assertEqual(len(data['checkpoint_sha256']), 64)


if __name__ == '__main__': unittest.main()
