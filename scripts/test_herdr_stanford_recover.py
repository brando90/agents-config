"""Offline fixture tests: no live SSH, authentication, catalog, or Herdr changes."""

import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch


HELPER = Path(__file__).with_name("herdr_stanford_recover.py")
spec = importlib.util.spec_from_file_location("recovery", HELPER)
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.catalog = self.root / "endpoints.json"
        self.log = self.root / "calls.jsonl"
        self.data = {"version": 1, "selected_profile": "1" * 32,
                     "future_metadata": {"keep": True}, "ssh": [
                         {"id": "1" * 32, "label": "skampere1", "target": "skampere1",
                          "session": "default", "enabled": True},
                         {"id": "2" * 32, "label": "Sherlock", "target": "sherlock",
                          "session": "dedicated", "enabled": False, "future": [1, 2]},
                         {"id": "3" * 32, "label": "FarmShare", "target": "farmshare",
                          "session": "default", "enabled": False}]}
        self.catalog.write_text(json.dumps(self.data))
        self.catalog.chmod(0o600)
        self.ssh = self.root / "ssh"
        self.ssh.write_text("""#!/usr/bin/env python3
import json, os, sys
with open(os.environ['TEST_LOG'], 'a') as stream:
    stream.write(json.dumps(['ssh'] + sys.argv[1:]) + '\\n')
hosts = {'sherlock': 'sh04-ln07.sherlock.stanford.edu',
         'sherlock-herdr': 'sh03-01n70.sherlock.stanford.edu',
         'farmshare': 'rice-01.farmshare.stanford.edu',
         'farmshare-herdr': 'rice-02.farmshare.stanford.edu'}
print('hostname ' + hosts.get(sys.argv[-1], sys.argv[-1]))
""")
        self.ssh.chmod(0o700)
        self.herdr = self.root / "herdr"
        self.herdr.write_text("""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ['TEST_LOG'], 'a') as stream:
    stream.write(json.dumps(['herdr'] + args) + '\\n')
path = Path(os.environ['TEST_CATALOG'])
data = json.loads(path.read_text())
if args[:2] == ['machine', 'list']:
    print(json.dumps(data['ssh']))
elif args[:2] == ['machine', 'enable']:
    row = next(r for r in data['ssh'] if r['id'] == args[2])
    row['enabled'] = True
    path.write_text(json.dumps(data))
elif args[:2] == ['machine', 'reconnect']:
    row = next(r for r in data['ssh'] if r['id'] == args[2])
    sys.exit(0 if row['enabled'] else 9)
elif args[:2] == ['machine', 'status']:
    row = next(r for r in data['ssh'] if r['id'] == args[2])
    state = os.environ.get('TEST_STATUS', 'reachable')
    print(json.dumps([{'id': row['id'], 'status': state,
                       'error': None if state == 'reachable' else 'test failure'}]))
elif args[:1] == ['--machine'] and args[2:] == ['agent', 'list']:
    if os.environ.get('TEST_AGENT_FAIL'):
        sys.exit(8)
    print('[]')
else:
    sys.exit(7)
""")
        self.herdr.chmod(0o700)
        self.environment = patch.dict(os.environ, {"TEST_LOG": str(self.log),
                                                  "TEST_CATALOG": str(self.catalog)})
        self.environment.start()
        self.stdout = contextlib.redirect_stdout(io.StringIO())
        self.stderr = contextlib.redirect_stderr(io.StringIO())
        self.stdout.__enter__()
        self.stderr.__enter__()

    def tearDown(self):
        self.stderr.__exit__(None, None, None)
        self.stdout.__exit__(None, None, None)
        self.environment.stop()
        self.temporary.cleanup()

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def migrate(self, label="Sherlock", target="sherlock-herdr", expected="sherlock"):
        return recovery.migrate_target(self.catalog, label, target, expected, str(self.ssh))

    def arguments(self, *args):
        return ["--catalog", str(self.catalog), "--herdr", str(self.herdr),
                "--ssh", str(self.ssh), *args]

    def test_target_only_migration_preserves_ids_order_unknown_fields_and_backup(self):
        original = self.catalog.read_bytes()
        backup = self.migrate()
        expected = copy.deepcopy(self.data)
        expected["ssh"][1]["target"] = "sherlock-herdr"
        self.assertEqual(json.loads(self.catalog.read_bytes()), expected)
        self.assertEqual(backup.read_bytes(), original)
        self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.catalog.stat().st_mode), 0o600)

    def test_repeat_migration_is_noop_even_with_original_expected_target(self):
        self.migrate()
        snapshot = self.catalog.stat()
        backups = list(self.root.glob("*.before-target-*"))
        self.assertIsNone(self.migrate())
        self.assertEqual(self.catalog.stat().st_ino, snapshot.st_ino)
        self.assertEqual(list(self.root.glob("*.before-target-*")), backups)

    def test_wrong_expected_target_fails_without_changes(self):
        original = self.catalog.read_bytes()
        with self.assertRaisesRegex(recovery.RecoveryError, "expected target"):
            self.migrate(expected="another-target")
        self.assertEqual(self.catalog.read_bytes(), original)

    def test_login_node_refused_before_any_herdr_command(self):
        with patch.object(recovery.sys.stdin, "isatty", return_value=True):
            code = recovery.main(self.arguments("reconnect", "Sherlock"))
        self.assertEqual(code, 1)
        self.assertFalse(any(call[0] == "herdr" for call in self.calls()))
        self.assertFalse(json.loads(self.catalog.read_bytes())["ssh"][1]["enabled"])

    def test_login_node_cannot_be_migration_destination(self):
        with self.assertRaisesRegex(recovery.RecoveryError, "refusing Herdr"):
            self.migrate(target="sh04-ln07.sherlock.stanford.edu")

    def test_noninteractive_reconnect_refuses_before_changes_or_commands(self):
        with patch.object(recovery.sys.stdin, "isatty", return_value=False):
            code = recovery.main(self.arguments("reconnect", "FarmShare"))
        self.assertEqual(code, 1)
        self.assertEqual(self.calls(), [])
        self.assertEqual(json.loads(self.catalog.read_bytes()), self.data)

    def test_enable_precedes_reconnect_and_checks_saved_profile_status(self):
        self.migrate()
        with patch.object(recovery.sys.stdin, "isatty", return_value=True):
            code = recovery.main(self.arguments("reconnect", "Sherlock", "FarmShare"))
        self.assertEqual(code, 0)
        calls = self.calls()
        for identifier in ("2" * 32, "3" * 32):
            enable = calls.index(["herdr", "machine", "enable", identifier])
            reconnect = calls.index(["herdr", "machine", "reconnect", identifier])
            status = calls.index(["herdr", "machine", "status", identifier, "--json"])
            agents = calls.index(["herdr", "--machine", identifier, "agent", "list"])
            self.assertLess(enable, reconnect)
            self.assertLess(reconnect, status)
            self.assertLess(status, agents)

    def test_nonreachable_zero_exit_status_does_not_report_success(self):
        with patch.dict(os.environ, {"TEST_STATUS": "error"}), \
                patch.object(recovery.sys.stdin, "isatty", return_value=True):
            code = recovery.main(self.arguments("reconnect", "FarmShare"))
        self.assertEqual(code, 1)
        self.assertFalse(any(call[1:2] == ["--machine"] for call in self.calls()))

    def test_agent_list_failure_does_not_report_success(self):
        with patch.dict(os.environ, {"TEST_AGENT_FAIL": "1"}), \
                patch.object(recovery.sys.stdin, "isatty", return_value=True):
            code = recovery.main(self.arguments("reconnect", "FarmShare"))
        self.assertEqual(code, 1)

    def test_concurrent_write_preserved_and_migration_aborted(self):
        real_mkstemp = recovery.tempfile.mkstemp
        concurrent = dict(self.data, new_concurrent_field="preserve me")

        def another_writer(*args, **kwargs):
            self.catalog.write_text(json.dumps(concurrent))
            return real_mkstemp(*args, **kwargs)

        with patch.object(recovery.tempfile, "mkstemp", side_effect=another_writer):
            with self.assertRaisesRegex(recovery.RecoveryError, "Concurrent catalog change"):
                self.migrate()
        self.assertEqual(json.loads(self.catalog.read_bytes()), concurrent)
        self.assertEqual(list(self.root.glob(".endpoints-recovery-*")), [])

    def test_symlink_catalog_refused(self):
        actual = self.root / "actual.json"
        self.catalog.rename(actual)
        self.catalog.symlink_to(actual)
        with self.assertRaises(recovery.RecoveryError):
            self.migrate()
        self.assertEqual(json.loads(actual.read_bytes()), self.data)

    def test_duplicate_labels_refused_without_creating_profile(self):
        duplicate = dict(self.data["ssh"][1], id="4" * 32)
        self.data["ssh"].append(duplicate)
        self.catalog.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(recovery.RecoveryError, "exactly one"):
            self.migrate()


if __name__ == "__main__":
    unittest.main()
