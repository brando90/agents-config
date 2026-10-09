"""Tests for watch_worker.sh: every terminal state (done, dead, blocked, idle, timeout) on an isolated tmux server."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parent / "watch_worker.sh"


@unittest.skipUnless(shutil.which("tmux"), "tmux not installed")
class WatchWorkerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = {**os.environ, "TMUX_TMPDIR": self.tmp.name}
        self.env.pop("TMUX", None)

    def tearDown(self):
        subprocess.run(["tmux", "kill-server"], env=self.env, capture_output=True)
        self.tmp.cleanup()

    def session(self, name, text):
        script = f"printf '%s\\n' {text!r}; sleep 60"
        subprocess.run(["tmux", "new-session", "-d", "-s", name, "sh", "-c", script], env=self.env, check=True)
        subprocess.run(["sleep", "0.5"])

    def watch(self, name, deliverable, *extra):
        cmd = [str(SCRIPT), "--session", name, "--deliverable", str(deliverable), "--interval", "0.2", *extra]
        return subprocess.run(cmd, env=self.env, capture_output=True, text=True, timeout=30)

    def test_done_when_deliverable_written_and_idle(self):
        out = Path(self.tmp.name) / "review.md"
        out.write_text("findings\n")
        self.session("w-done", "Worked for 3m 2s")
        r = self.watch("w-done", out)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(r.stdout.startswith("DONE"))

    def test_dead_when_session_missing(self):
        r = self.watch("w-none", Path(self.tmp.name) / "missing.md")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue(r.stdout.startswith("DEAD"))

    def test_blocked_on_credit_message_at_idle_prompt(self):
        self.session("w-block", "You're out of usage credits. Run /usage-credits to keep using Fable 5.1")
        r = self.watch("w-block", Path(self.tmp.name) / "missing.md")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("usage credits", r.stdout)

    def test_idle_without_deliverable(self):
        self.session("w-idle", "Worked for 14m 58s")
        r = self.watch("w-idle", Path(self.tmp.name) / "missing.md", "--idle-checks", "2")
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertTrue(r.stdout.startswith("IDLE"))

    def test_busy_worker_is_not_idle_and_times_out(self):
        self.session("w-busy", "Working (2m 34s - esc to interrupt) rate limit discussion in progress")
        r = self.watch("w-busy", Path(self.tmp.name) / "missing.md", "--timeout", "1")
        self.assertEqual(r.returncode, 4, r.stdout)
        self.assertIn("busy", r.stdout)

    def test_usage_error_exit_code(self):
        r = subprocess.run([str(SCRIPT), "--session", "x"], env=self.env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 64)


if __name__ == "__main__":
    unittest.main()
