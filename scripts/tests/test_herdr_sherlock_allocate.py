"""Offline tests: fake scheduler/runner responses, real local file operations."""

import base64
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("allocate", Path(__file__).resolve().parents[1].joinpath("herdr_sherlock_allocate.py"))
allocate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(allocate)


def host_key(byte=b"x"):
    return base64.b64encode(struct.pack(">I", 11) + b"ssh-ed25519" + struct.pack(">I", 32) + byte * 32).decode()


class AllocateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.lease = self.root / "sherlock.json"
        self.config = self.root / "herdr-stanford.conf"
        self.keys = self.root / "known_hosts"
        self.config.write_text("# retain me\nHost herdr-sherlock\n    HostName sh03-01n68 # keep comment\n    User brando9\n\nHost herdr-farmshare\n    HostName rice-02.farmshare.stanford.edu\n")
        self.lease.write_text(json.dumps({"host": "sh03-01n68", "job_id": "41", "expires_at": 500, "extra": True}))
        self.keys.write_text("unrelated-host ssh-ed25519 " + host_key() + "\n")
        for path in (self.config, self.lease, self.keys):
            path.chmod(0o600)
        self.data = {"job_id": "42", "job_name": "herdr-interactive", "user": "brando9",
                     "status": "RUNNING", "host": "sh03-01n69", "expires_at": 2000,
                     "key_type": "ssh-ed25519", "host_key": host_key(), "submitted": False}

    def tearDown(self):
        self.temp.cleanup()

    def apply(self):
        with patch.object(allocate.time, "time", return_value=1000):
            allocate.apply_result(self.data, self.lease, self.config, self.keys)

    def snapshot(self):
        return tuple(path.read_bytes() for path in (self.lease, self.config, self.keys))

    def test_running_updates_only_hostname_and_preserves_existing_data(self):
        before = self.snapshot()
        self.apply()
        self.assertEqual(self.config.read_bytes(), before[1].replace(b"sh03-01n68", b"sh03-01n69"))
        self.assertTrue(self.keys.read_bytes().startswith(before[2]))
        lease = json.loads(self.lease.read_bytes())
        self.assertEqual(lease["host"], "sh03-01n69")
        self.assertEqual(lease["job_id"], "42")
        self.assertTrue(lease["extra"])
        self.assertFalse(lease["automatic_restart"])
        self.assertEqual(len(list(self.root.glob("*.before-allocation-*"))), 3)

    def test_repeat_refresh_is_idempotent_and_adds_no_key_or_backup(self):
        self.apply()
        before = self.snapshot()
        backups = list(self.root.glob("*.before-allocation-*"))
        self.apply()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(list(self.root.glob("*.before-allocation-*")), backups)

    def test_pending_and_expired_leave_all_local_files_untouched(self):
        before = self.snapshot()
        self.data["status"] = "PENDING"
        with self.assertRaisesRegex(allocate.AllocationError, "PENDING"):
            self.apply()
        self.data["status"] = "RUNNING"
        self.data["expires_at"] = 1000
        with self.assertRaisesRegex(allocate.AllocationError, "expired"):
            self.apply()
        self.assertEqual(self.snapshot(), before)

    def test_changed_known_key_refused_before_any_local_update(self):
        self.keys.write_text("sh03-01n69 ssh-ed25519 " + host_key(b"z") + "\n")
        before = self.snapshot()
        with self.assertRaisesRegex(allocate.AllocationError, "Changed known"):
            self.apply()
        self.assertEqual(self.snapshot(), before)

    def test_mismatched_hostkeyalias_refused_without_changes(self):
        self.config.write_text(self.config.read_text().replace("    User brando9", "    HostKeyAlias sh03-01n68\n    User brando9"))
        before = self.snapshot()
        with self.assertRaisesRegex(allocate.AllocationError, "HostKeyAlias"):
            self.apply()
        self.assertEqual(self.snapshot(), before)

    def test_wrong_user_name_or_login_node_refused(self):
        for field, value in [("user", "other"), ("job_name", "other"), ("host", "sh04-ln07")]:
            previous = self.data[field]
            self.data[field] = value
            with self.assertRaises(allocate.AllocationError):
                self.apply()
            self.data[field] = previous

    def remote(self, rows, state="RUNNING", wrong_user=False):
        calls = []
        script = self.root / ".local/share/herdr-stanford/server.sbatch"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("#!/bin/sh\n")

        def fake_run(args, **kwargs):
            calls.append((args, kwargs))
            if args[0] == "id":
                output = "brando9"
            elif args[0] == "squeue":
                output = rows
            elif args[0] == "sbatch":
                output = "42"
            elif args[0] == "scontrol":
                user = "other" if wrong_user else "brando9"
                output = f"JobId=42 JobName=herdr-interactive UserId={user}(123) JobState={state} NodeList=sh03-01n69 EndTime=2030-10-23T21:14:31"
            elif args[0] == "ssh-keyscan":
                output = "sh03-01n69 ssh-ed25519 " + host_key()
            else:
                raise AssertionError(args)
            return subprocess.CompletedProcess(args, 0, output, "")

        namespace = {}
        stdout = io.StringIO()
        with patch.object(allocate.Path, "home", return_value=self.root), \
                patch.object(allocate.subprocess, "run", side_effect=fake_run), \
                patch.dict(os.environ, {}, clear=False), contextlib.redirect_stdout(stdout):
            try:
                exec(allocate.REMOTE_SCRIPT, namespace)
            finally:
                if "lock" in namespace:
                    namespace["lock"].close()
        record = stdout.getvalue().strip().removeprefix(allocate.MARKER)
        return json.loads(record), calls

    def test_remote_reuses_one_running_job_without_submission(self):
        data, calls = self.remote("42|herdr-interactive|brando9|RUNNING")
        self.assertFalse(data["submitted"])
        self.assertEqual(data["host"], "sh03-01n69")
        self.assertEqual(sum(args[0] == "squeue" for args, _ in calls), 1)
        self.assertEqual(sum(args[0] == "scontrol" for args, _ in calls), 1)
        self.assertFalse(any(args[0] == "sbatch" for args, _ in calls))

    def test_remote_submits_once_from_home_and_does_not_poll_pending_job(self):
        data, calls = self.remote("", "PENDING")
        self.assertEqual(data["status"], "PENDING")
        self.assertTrue(data["submitted"])
        submissions = [(args, kwargs) for args, kwargs in calls if args[0] == "sbatch"]
        self.assertEqual(len(submissions), 1)
        self.assertEqual(submissions[0][1]["cwd"], self.root)
        self.assertEqual(sum(args[0] == "squeue" for args, _ in calls), 1)
        self.assertEqual(sum(args[0] == "scontrol" for args, _ in calls), 1)
        self.assertFalse(any(args[0] == "ssh-keyscan" for args, _ in calls))

    def test_remote_refuses_duplicate_jobs(self):
        with self.assertRaisesRegex(RuntimeError, "More than one"):
            self.remote("42|herdr-interactive|brando9|RUNNING\n43|herdr-interactive|brando9|PENDING")

    def test_remote_refuses_mismatched_scontrol_owner(self):
        with self.assertRaisesRegex(RuntimeError, "mismatch"):
            self.remote("42|herdr-interactive|brando9|RUNNING", wrong_user=True)


if __name__ == "__main__":
    unittest.main()
