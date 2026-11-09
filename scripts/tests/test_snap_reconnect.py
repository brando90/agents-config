"""Offline checks: shared admission, failure recovery, protocol relay and config scope."""

import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import snap_reconnect as guard
import setup_snap_gateway as gateway


def effective(config, host, command=None):
    args = ["/usr/bin/ssh", "-F", str(config), "-G", host]
    if command:
        args.append(command)
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return dict(line.split(" ", 1) for line in result.stdout.splitlines())


class ReconnectTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_one_shared_window_and_backoff_survive_new_instances(self):
        with guard.locked(self.directory):
            state = guard.reserve(self.directory, 1000)
            self.assertEqual(state["next_attempt"], 1900)
            guard.reached(self.directory, state)
        with self.assertRaises(guard.Deferred), guard.locked(self.directory):
            guard.reserve(self.directory, 1599)
        now = 1600
        for delay in (900, 1200, 1800, 3600, 3600):
            with guard.locked(self.directory):
                state = guard.reserve(self.directory, now)
                self.assertEqual(state["next_attempt"], now + delay)
            now += delay
        with guard.locked(self.directory):
            state = guard.reserve(self.directory, now)
            guard.reached(self.directory, state)
        self.assertEqual(guard.read_state(self.directory)["next_attempt"], now + 600)
        self.assertEqual(guard.read_state(self.directory)["failures"], 0)

    def test_concurrent_callers_admit_only_one(self):
        # Separate interpreters exercise the actual OS file lock.
        code = ("import sys;sys.path.insert(0,sys.argv[1]);import snap_reconnect as g;"
                "from pathlib import Path;d=Path(sys.argv[2]);"
                "\ntry:\n with g.locked(d):g.reserve(d,1000)\n print('admitted')"
                "\nexcept g.Deferred:print('deferred')")
        args = [sys.executable, "-c", code, str(Path(guard.__file__).parent), str(self.directory)]
        # Popen all before waiting, rather than serializing with run().
        children = [subprocess.Popen(args, stdout=subprocess.PIPE, text=True) for _ in range(12)]
        results = [child.communicate(timeout=10)[0].strip() for child in children]
        self.assertEqual(results.count("admitted"), 1)
        self.assertEqual(results.count("deferred"), 11)

    def test_corrupt_state_and_unrelated_hosts_fail_before_network(self):
        (self.directory / "state.json").write_text('{"next_attempt": "bad"}')
        with patch.object(guard.subprocess, "Popen") as spawn:
            with self.assertRaises(ValueError):
                guard.proxy("other.example.org", 22, self.directory)
            with self.assertRaises((ValueError, KeyError)):
                guard.proxy("mercury1.stanford.edu", 22, self.directory)
            spawn.assert_not_called()

    def test_cooldown_denies_before_network(self):
        guard.write_state(self.directory, {"next_attempt": 10**12, "last_attempt": 0, "failures": 4})
        with patch.object(guard.subprocess, "Popen") as spawn:
            with self.assertRaises(guard.Deferred):
                guard.proxy("mercury1.stanford.edu", 22, self.directory)
            spawn.assert_not_called()

    def test_proxy_relays_bytes_and_resets_on_greeting_only(self):
        real_popen = subprocess.Popen
        payload = b"SSH-2.0-offline-test\r\n\x00\xffpayload"
        incoming = b"SSH-2.0-offline-client\r\n\x01\xferequest"
        source = tempfile.TemporaryFile()
        source.write(incoming)
        source.seek(0)
        def fake_spawn(*args, **kwargs):
            code = ("import sys;sys.stdout.buffer.write(" + repr(payload) + ");"
                    "sys.stdout.buffer.flush();sys.stdout.buffer.write(sys.stdin.buffer.read())")
            return real_popen([sys.executable, "-c", code], **kwargs)
        output = io.TextIOWrapper(io.BytesIO())
        with source:
            with patch.object(guard.subprocess, "Popen", side_effect=fake_spawn), \
                    patch.object(guard.sys, "stdin", source), \
                    contextlib.redirect_stdout(output):
                self.assertEqual(guard.proxy("mercury1.stanford.edu", 22, self.directory), 0)
        self.assertEqual(output.buffer.getvalue(), payload + incoming)
        self.assertEqual(guard.read_state(self.directory)["failures"], 0)
        with self.assertRaises(guard.Deferred):
            guard.proxy("skampere3.stanford.edu", 22, self.directory)

    def test_failed_transport_keeps_pessimistic_backoff(self):
        real_popen = subprocess.Popen
        def fake_spawn(*args, **kwargs):
            return real_popen([sys.executable, "-c", "raise SystemExit(255)"], **kwargs)
        with patch.object(guard.subprocess, "Popen", side_effect=fake_spawn), \
                patch.object(guard.sys, "stdin", subprocess.DEVNULL):
            with self.assertRaises(guard.Deferred):
                guard.proxy("skampere1.stanford.edu", 22, self.directory)
        state = guard.read_state(self.directory)
        self.assertEqual(state["failures"], 1)
        self.assertEqual(state["next_attempt"] - state["last_attempt"], 900)

    def test_config_only_changes_five_hosts_and_survives_gateway_refresh(self):
        config = self.directory / "config"
        original = ("Host unrelated\n HostName other.example.org\n ProxyCommand /usr/bin/false\n"
                    "Host *\n ServerAliveInterval 42\n")
        config.write_text(original)
        gateway.install(config, "brando9", "whale.stanford.edu")
        unaffected = ("unrelated", "whale.stanford.edu", "ampere1", "farmshare", "sherlock")
        before = {h: effective(config, h) for h in unaffected}
        backup = guard.install(config, Path(guard.__file__), Path(sys.executable))
        self.assertEqual(backup.stat().st_mode & 0o777, 0o600)
        once = config.read_bytes()
        guard.install(config, Path(guard.__file__), Path(sys.executable))
        self.assertEqual(once, config.read_bytes())
        for _ in range(2):
            gateway.install(config, "brando9", "whale.stanford.edu")
            for host in guard.HOSTS:
                for name in (host, host + ".stanford.edu"):
                    for command in (None, "echo Codex remote SSH requires SHELL"):
                        settings = effective(config, name, command)
                        self.assertIn("snap_reconnect.py", settings["proxycommand"])
                        self.assertEqual(settings["controlmaster"], "auto")
                        self.assertEqual(settings["hostname"], host + ".stanford.edu")
            self.assertEqual(before, {h: effective(config, h) for h in unaffected})
            self.assertEqual(gateway.route_problems("brando9", "whale.stanford.edu", ["-F", str(config)]), [])


if __name__ == "__main__":
    unittest.main()
