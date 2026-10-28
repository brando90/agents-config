"""Tests for stale_checkout_sweep.py: only worktrees with nothing unique are removed."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "stale_checkout_sweep.py"


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout


class StaleCheckoutSweepTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name).resolve()
        self.origin, self.main, self.wts = t / "origin.git", t / "home" / "proj", t / "wts"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], check=True)
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.main)], check=True, capture_output=True)
        git(self.main, "config", "user.email", "t@example.com")
        git(self.main, "config", "user.name", "t")
        (self.main / ".gitignore").write_text("results/\n__pycache__/\n")
        (self.main / "a.txt").write_text("a\n")
        git(self.main, "add", ".")
        git(self.main, "commit", "-qm", "init")
        git(self.main, "push", "-q", "origin", "main")
        git(self.main, "remote", "set-head", "origin", "main")

    def tearDown(self):
        self.tmp.cleanup()

    def worktree(self, name):
        path = self.wts / "proj" / name
        git(self.main, "worktree", "add", "-q", "-b", name, str(path), "origin/main")
        return path

    def sweep(self, *extra):
        cmd = [sys.executable, str(SCRIPT), "--root", f"{self.wts}:3", "--min-age-hours", "0", "--json", *extra]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        return {Path(i["path"]).name: i for i in out["results"]}, out["actions"]

    def test_classification(self):
        clean = self.worktree("clean")
        (self.worktree("cache") / "__pycache__").mkdir()
        (self.wts / "proj" / "cache" / "__pycache__" / "x.pyc").write_bytes(b"\0")
        (self.worktree("dirty") / "a.txt").write_text("changed\n")
        (self.worktree("untracked") / "new.txt").write_text("only here\n")
        ahead = self.worktree("ahead")
        (ahead / "b.txt").write_text("b\n")
        git(ahead, "add", "b.txt")
        git(ahead, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", "local only")
        (self.worktree("results") / "results").mkdir()
        (self.wts / "proj" / "results" / "results" / "run.log").write_text("evidence\n")
        locked = self.worktree("locked")
        git(self.main, "worktree", "lock", str(locked))
        res, _ = self.sweep()
        self.assertEqual(res["clean"]["status"], "SAFE")
        self.assertEqual(res["cache"]["status"], "SAFE")
        for name in ("dirty", "untracked", "ahead", "results", "locked"):
            self.assertEqual(res[name]["status"], "KEEP", (name, res[name]))
        self.assertTrue(clean.exists())  # dry run removes nothing

    def test_changes_already_on_main_are_safe(self):
        landed = self.worktree("landed")
        (landed / "c.txt").write_text("landed\n")
        (self.main / "c.txt").write_text("landed\n")
        git(self.main, "add", "c.txt")
        git(self.main, "commit", "-qm", "land c")
        git(self.main, "push", "-q", "origin", "main")
        res, _ = self.sweep()
        self.assertEqual(res["landed"]["status"], "SAFE", res["landed"])
        self.assertTrue(res["landed"]["force"])

    def test_ignored_copy_of_main_checkout_is_safe(self):
        wt = self.worktree("copied")
        for root in (wt, self.main):
            (root / "results").mkdir()
            (root / "results" / "r.json").write_text("{}\n")
        res, _ = self.sweep()
        self.assertEqual(res["copied"]["status"], "SAFE", res["copied"])

    def test_untracked_copy_of_main_checkout_is_safe(self):
        wt = self.worktree("copied-untracked")
        for root in (wt, self.main):
            (root / "notes.md").write_text("same in both\n")
        res, _ = self.sweep()
        self.assertEqual(res["copied-untracked"]["status"], "SAFE", res["copied-untracked"])

    def test_age_survives_repeated_sweeps(self):
        wt = self.worktree("old")
        gitdir = Path(git(wt, "rev-parse", "--absolute-git-dir").strip())
        two_days_ago = time.time() - 48 * 3600
        for f in (wt, gitdir / "HEAD", gitdir / "logs" / "HEAD", gitdir / "index"):
            os.utime(f, (two_days_ago, two_days_ago))
        for _ in range(2):  # the first sweep must not make the worktree look recent to the second
            res, _ = self.sweep("--min-age-hours", "24")
            self.assertEqual(res["old"]["status"], "SAFE", res["old"])
        self.assertLess(os.stat(gitdir / "index").st_mtime, time.time() - 47 * 3600)

    def test_apply_removes_empty_codex_containers(self):
        container = self.wts / "codex-id"
        git(self.main, "worktree", "add", "-q", "-b", "c", str(container / "proj"), "origin/main")
        (container / ".codex-worktree-name").write_text("")
        (self.wts / "leftover").mkdir()
        (self.wts / "leftover" / ".codex-worktree-name").write_text("")
        (self.wts / "real").mkdir()
        (self.wts / "real" / "notes.md").write_text("keep\n")
        _, actions = self.sweep("--apply")
        self.assertFalse(container.exists(), actions)
        self.assertFalse((self.wts / "leftover").exists(), actions)
        self.assertTrue((self.wts / "real" / "notes.md").exists())

    def test_apply_removes_safe_and_merged_branch_only(self):
        clean = self.worktree("clean")
        dirty = self.worktree("dirty")
        (dirty / "a.txt").write_text("changed\n")
        _, actions = self.sweep("--apply")
        self.assertFalse(clean.exists())
        self.assertTrue(dirty.exists())
        self.assertTrue(any("REMOVED" in a and "deleted merged local branch clean" in a for a in actions), actions)
        self.assertNotIn("clean", git(self.main, "branch", "--format=%(refname:short)").split())
        self.assertIn("dirty", git(self.main, "branch", "--format=%(refname:short)").split())


if __name__ == "__main__":
    unittest.main()
