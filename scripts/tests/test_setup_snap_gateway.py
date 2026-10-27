"""Tests for setup_snap_gateway.py: the managed ~/.ssh/config block, checked with `ssh -G -F` (no network)."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import setup_snap_gateway as gw  # noqa: E402

USER, GATEWAY = "brando9", "whale.stanford.edu"


def resolved(config, host):
    out = subprocess.run(["ssh", "-F", str(config), "-G", host], capture_output=True, text=True,
                         check=True).stdout
    values = {}
    for line in out.splitlines():
        key, _, value = line.partition(" ")
        values.setdefault(key, value)
    return values


@unittest.skipUnless(shutil.which("ssh"), "ssh not installed")
class SetupSnapGatewayTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config = Path(self.tmp.name) / "config"

    def tearDown(self):
        self.tmp.cleanup()

    def test_fresh_config_routes_every_node_but_not_the_gateway(self):
        changed, backup = gw.install(self.config, USER, GATEWAY)
        self.assertTrue(changed)
        self.assertIsNone(backup)
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o600)
        for node in gw.NODES:
            for name in (node, gw.fqdn(node)):
                v = resolved(self.config, name)
                self.assertEqual(v["hostname"], gw.fqdn(node), name)
                self.assertEqual(v["proxyjump"], f"{USER}@{GATEWAY}", name)
                self.assertEqual(v["user"], USER, name)
        self.assertNotIn("proxyjump", resolved(self.config, GATEWAY))
        self.assertEqual(gw.route_problems(USER, GATEWAY, ["-F", str(self.config)]), [])

    def test_globals_stay_global_and_older_stanzas_lose(self):
        original = ("AddKeysToAgent yes\n\nHost skampere1\n    HostName 10.0.0.1\n\n"
                    "Host other\n    HostName other.example.org\n")
        self.config.write_text(original)
        os.chmod(self.config, 0o644)
        changed, backup = gw.install(self.config, USER, GATEWAY)
        self.assertTrue(changed)
        self.assertEqual(backup.read_text(), original)
        self.assertEqual(backup.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o644)
        text = self.config.read_text()
        self.assertTrue(text.startswith("AddKeysToAgent yes\n\n" + gw.BEGIN))
        self.assertEqual(resolved(self.config, "skampere1")["hostname"], "skampere1.stanford.edu")
        other = resolved(self.config, "other")
        self.assertEqual(other["hostname"], "other.example.org")
        self.assertEqual(other["addkeystoagent"], "true")
        self.assertNotIn("proxyjump", other)

    def test_rerun_is_a_no_op_and_remove_restores_the_original(self):
        original = "Host other\n    HostName other.example.org\n"
        self.config.write_text(original)
        gw.install(self.config, USER, GATEWAY)
        once = self.config.read_bytes()
        self.assertEqual(gw.install(self.config, USER, GATEWAY), (False, None))
        self.assertEqual(self.config.read_bytes(), once)
        changed, _ = gw.install(self.config, USER, GATEWAY, remove=True)
        self.assertTrue(changed)
        self.assertEqual(self.config.read_text(), original)

    def test_symlinked_config_stays_a_symlink(self):
        target = Path(self.tmp.name) / "dotfiles_config"
        target.write_text("Host other\n    HostName other.example.org\n")
        self.config.symlink_to(target)
        gw.install(self.config, USER, GATEWAY)
        self.assertTrue(self.config.is_symlink())
        self.assertIn(gw.BEGIN, target.read_text())

    def test_gateway_may_not_be_a_routed_node(self):
        with self.assertRaises(SystemExit):
            gw.managed_block(USER, "ilc.stanford.edu")


if __name__ == "__main__":
    unittest.main()
