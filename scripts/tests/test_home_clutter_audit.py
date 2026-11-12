"""Home-clutter candidates must distinguish real checkouts from symlink aliases."""

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "home_clutter_audit.py"
spec = importlib.util.spec_from_file_location("home_clutter_audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class HomeClutterAuditTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.home_patch = patch.object(audit, "HOME", self.home)
        self.scan_patch = patch.object(audit, "SCAN", [self.home])
        self.home_patch.start()
        self.scan_patch.start()
        self.addCleanup(self.home_patch.stop)
        self.addCleanup(self.scan_patch.stop)

    def repo(self, name):
        path = self.home / name
        subprocess.run(["git", "init", "-q", str(path)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(path), "remote", "add", "origin",
                        "git@github.com:example/project.git"], check=True, capture_output=True)
        return path

    def duplicate_candidates(self):
        return [(path, reasons) for path, reasons in audit.audit()
                if any("additional checkout" in reason for reason in reasons)]

    def test_canonical_symlink_is_not_a_second_checkout(self):
        original = self.repo("project-dt")
        (self.home / "project").symlink_to(original, target_is_directory=True)
        self.assertEqual(self.duplicate_candidates(), [])
        self.assertTrue(original.is_dir())
        self.assertTrue((self.home / "project").is_symlink())

    def test_real_extra_checkout_is_reported_once_despite_aliases(self):
        canonical = self.repo("project-original")
        (self.home / "project").symlink_to(canonical, target_is_directory=True)
        extra = self.repo("project-copy")
        (self.home / "project-alias").symlink_to(extra, target_is_directory=True)
        found = self.duplicate_candidates()
        self.assertEqual([path for path, _ in found], [extra])
        self.assertTrue(any("name-matched checkout: ~/project" in reason for reason in found[0][1]))
        self.assertEqual(sum(path == extra for path, _ in audit.audit()), 1)

    def test_multiple_aliases_without_matching_repo_name_are_one_checkout(self):
        original = self.repo("renamed")
        (self.home / "alias-one").symlink_to(original, target_is_directory=True)
        (self.home / "alias-two").symlink_to(original, target_is_directory=True)
        self.assertEqual(self.duplicate_candidates(), [])

    def test_names_are_candidates_not_proof(self):
        for name in ("research-dt", "notes-11-12-2026"):
            (self.home / name).mkdir()
        flagged = audit.audit()
        self.assertEqual(len(flagged), 2)
        self.assertTrue(all("candidate" in reason for _, reasons in flagged for reason in reasons))


if __name__ == "__main__":
    unittest.main()
