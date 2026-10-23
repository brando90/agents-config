"""Offline launcher checks; no credentials, inference, or SSH connections."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class PiRemoteTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pi-remote-test-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.cli = self.home / ".local/lib/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js"
        self.cli.parent.mkdir(parents=True)
        self.cli.write_text("console.log(JSON.stringify(process.argv.slice(2)))")
        self.env = dict(os.environ, HOME=str(self.home))
        self.env.pop("PI_CODING_AGENT_DIR", None)
        self.script = Path(__file__).with_name("pi_remote.sh")
        profile = self.home / ".pi/agent"
        profile.mkdir(parents=True)
        (profile / "settings.json").write_text('{"defaultProvider":"snap-coder"}')
        (profile / "models.json").write_text('{"providers":{"snap-coder":{"baseUrl":"http://127.0.0.1:18127/v1"}}}')
        # Any unintended SSH invocation fails deterministically.
        bindir = self.home / "test-bin"
        bindir.mkdir()
        ssh = bindir / "ssh"
        ssh.write_text("#!/bin/sh\necho UNEXPECTED_SSH >&2\nexit 97\n")
        ssh.chmod(0o755)
        self.env["PATH"] = str(bindir) + os.pathsep + self.env["PATH"]

    def run_cli(self, args):
        return subprocess.run(["bash", str(self.script)] + args, env=self.env,
                              capture_output=True, text=True, timeout=10)

    def assert_passthrough(self, args):
        result = self.run_cli(args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), args)
        self.assertNotIn("UNEXPECTED_SSH", result.stderr)

    def test_version_offline(self):
        self.assert_passthrough(["--version"])

    def test_help_offline(self):
        self.assert_passthrough(["--help"])

    def test_catalog_offline(self):
        self.assert_passthrough(["--list-models"])

    def test_explicit_other_provider_and_literal_arguments(self):
        self.assert_passthrough(["--provider", "other", "-p", "literal $HOME; `echo nope`"])

    def test_missing_package(self):
        self.cli.unlink()
        result = self.run_cli(["--version"])
        self.assertEqual(result.returncode, 127)
        self.assertIn("Pi coding agent is missing", result.stderr)

    def test_installer_preserves_login_precedence_and_is_repeatable(self):
        package = self.cli.parents[2] / "package.json"
        package.write_text('{"version":"1.4.0"}')
        profile = self.home / ".profile"
        profile.write_text('# Existing login configuration\n')
        installer = self.script.with_name("install_pi_remote.sh")
        for _ in range(2):
            result = subprocess.run(["bash", str(installer)], env=self.env,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.home / ".bash_profile").exists())
        self.assertTrue(profile.read_text().startswith('# Existing login configuration\n'))
        self.assertEqual(profile.read_text().count('# Pi user-level command path'), 1)


if __name__ == "__main__":
    unittest.main()
