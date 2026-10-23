"""Offline lease-boundary tests; exec is mocked, so no network is contacted."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("sherlock_proxy", Path(__file__).with_name("herdr_sherlock_proxy.py"))
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)


class ProxyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "sherlock.json"
        self.data = {"host": "sh03-01n69", "job_id": 49231871, "expires_at": 2000}
        self.write()

    def tearDown(self):
        self.temp.cleanup()

    def write(self):
        self.path.write_text(json.dumps(self.data))
        self.path.chmod(0o600)

    def invoke(self, host="sh03-01n69", port="22", now=1000):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr), \
                patch.object(proxy.time, "time", return_value=now), \
                patch.object(proxy.os, "execvp") as execute:
            result = proxy.main([host, port], self.path)
        self.assertEqual(stdout.getvalue(), "")
        return result, execute, stderr.getvalue()

    def assert_refused(self, **kwargs):
        result, execute, error = self.invoke(**kwargs)
        self.assertEqual(result, 1)
        execute.assert_not_called()
        self.assertTrue(error)

    def test_valid_lease_executes_exact_noninteractive_forwarding_command(self):
        result, execute, error = self.invoke()
        self.assertEqual(result, 0)
        self.assertEqual(error, "")
        execute.assert_called_once_with("ssh", ["ssh", "-o", "BatchMode=yes", "-o",
                                                "ConnectTimeout=15", "-W", "sh03-01n69:22", "sherlock"])

    def test_expiry_boundary_is_closed(self):
        self.assert_refused(now=2000)
        self.assert_refused(now=2001)

    def test_mismatched_compute_host_refused(self):
        self.assert_refused(host="sh03-01n70")

    def test_non22_port_refused(self):
        self.assert_refused(port="2222")

    def test_login_host_refused(self):
        self.data["host"] = "sh04-ln07.sherlock.stanford.edu"
        self.write()
        self.assert_refused(host=self.data["host"])

    def test_option_or_shell_syntax_host_refused(self):
        for bad in ["-oProxyCommand=bad", "sh03-01n69;echo bad", "sh03-01n69.attacker.example", "sh03-01n69\n"]:
            self.data["host"] = bad
            self.write()
            self.assert_refused(host=bad)

    def test_malformed_and_missing_fields_refused(self):
        for field, value in [("host", None), ("job_id", True), ("job_id", 0),
                             ("job_id", "1;echo bad"), ("expires_at", True),
                             ("expires_at", "2000"), ("expires_at", float("nan")),
                             ("expires_at", float("inf")), ("expires_at", 10 ** 1000)]:
            previous = self.data[field]
            self.data[field] = value
            self.write()
            self.assert_refused()
            self.data[field] = previous

    def test_duplicate_fields_refused(self):
        self.path.write_text('{"host":"sh03-01n69","host":"sh03-01n70","job_id":1,"expires_at":2000}')
        self.assert_refused()

    def test_invalid_json_refused(self):
        self.path.write_text("{")
        self.assert_refused()

    def test_missing_lease_refused(self):
        self.path.unlink()
        self.assert_refused()

    def test_symlink_lease_refused(self):
        actual = self.path.with_name("actual.json")
        self.path.rename(actual)
        self.path.symlink_to(actual)
        self.assert_refused()

    def test_other_users_cannot_write_lease(self):
        self.path.chmod(0o666)
        self.assert_refused()


if __name__ == "__main__":
    unittest.main()
