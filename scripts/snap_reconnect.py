#!/usr/bin/env python3
"""Shared, fail-closed SSH ProxyCommand admission for five SNAP hosts.

Install locally: python3 scripts/snap_reconnect.py --install --defer-minutes 60
Inspect locally: python3 scripts/snap_reconnect.py --status
Neither command contacts a server. Normal proxy invocations never sleep/retry.
"""

import argparse
import contextlib
import fcntl
import json
import math
import os
from pathlib import Path
import re
import selectors
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

HOSTS = ("skampere1", "skampere2", "skampere3", "mercury1", "mercury2")
INTERVAL = 600
BACKOFF = (900, 1200, 1800, 3600)
BEGIN = "# >>> agents-config snap-reconnect >>>"
END = "# <<< agents-config snap-reconnect <<<"
STATE_DIR = Path.home() / ".ssh" / "snap-reconnect"


class Deferred(Exception):
    pass


def read_state(directory):
    path = directory / "state.json"
    if not path.exists():
        return {"next_attempt": 0, "failures": 0, "last_attempt": 0}
    state = json.loads(path.read_text())
    for key in ("next_attempt", "last_attempt"):
        value = state[key]
        if not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
            raise ValueError("invalid reconnect state: " + key)
    if type(state["failures"]) is not int or not 0 <= state["failures"] <= len(BACKOFF):
        raise ValueError("invalid reconnect failure count")
    return state


def write_state(directory, state):
    fd, name = tempfile.mkstemp(prefix=".state-", dir=directory)
    try:
        with os.fdopen(fd, "w") as output:
            json.dump(state, output, sort_keys=True)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, directory / "state.json")
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextlib.contextmanager
def locked(directory):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (directory / "lock").open("a+") as lock:
        os.chmod(directory / "lock", 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Deferred("another SNAP connection is opening; no network attempt made") from None
        try:
            yield lock
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def reserve(directory, now):
    state = read_state(directory)
    if now < state["next_attempt"]:
        raise Deferred(f"shared SNAP cooldown: {math.ceil(state['next_attempt'] - now)}s remaining; "
                       "no network attempt made")
    # Reserve failure backoff before spawning: a crash or interrupted handshake stays quiet.
    failures = min(state["failures"] + 1, len(BACKOFF))
    state.update(last_attempt=now, next_attempt=now + BACKOFF[failures - 1], failures=failures)
    write_state(directory, state)
    return state


def reached(directory, state):
    # A target SSH greeting proves transport reachability, not successful target authentication.
    state.update(failures=0, next_attempt=state["last_attempt"] + INTERVAL)
    write_state(directory, state)


def proxy_command(host, port):
    return ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectionAttempts=1",
            "-o", "ConnectTimeout=15", "-o", "ControlMaster=auto",
            "-o", "ControlPersist=8h", "-o", "ControlPath=~/.ssh/%r@%h:%p",
            "-W", f"[{host}]:{port}", "brando9@whale.stanford.edu"]


def proxy(host, port, directory=STATE_DIR):
    if host not in {h + ".stanford.edu" for h in HOSTS} or port != 22:
        raise ValueError("proxy is restricted to the five SNAP hosts on port 22")
    child = None
    try:
        with locked(directory) as lock:
            state = reserve(directory, time.time())
            child = subprocess.Popen(proxy_command(host, port), stdin=sys.stdin, stdout=subprocess.PIPE)
            # Hold admission until the destination greets us, with a bounded startup deadline.
            deadline = time.monotonic() + 45
            banner = b""
            with selectors.DefaultSelector() as selector:
                selector.register(child.stdout, selectors.EVENT_READ)
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise Deferred("SNAP greeting timed out; shared failure backoff retained")
                    chunk = os.read(child.stdout.fileno(), 65536)
                    if not chunk:
                        raise Deferred("SNAP transport failed before greeting; shared failure backoff retained")
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.buffer.flush()
                    banner += chunk
                    if any(line.startswith(b"SSH-2.0-") for line in banner.splitlines(keepends=True)
                           if line.endswith(b"\n")):
                        reached(directory, state)
                        fcntl.flock(lock, fcntl.LOCK_UN)
                        break
                    if len(banner) > 65536:
                        raise Deferred("invalid SNAP greeting; shared failure backoff retained")
        # stdin is directly inherited; relay stdout without modifying the SSH protocol.
        while True:
            chunk = os.read(child.stdout.fileno(), 65536)
            if not chunk:
                break
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
        return child.wait()
    finally:
        if child is not None:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
            child.stdout.close()


def block(script, python):
    names = list(HOSTS) + [h + ".stanford.edu" for h in HOSTS]
    command = " ".join(shlex.quote(str(s)) for s in (python, script))
    return (f"{BEGIN}\n# Shared cooldown for fresh SNAP connections; existing masters are reused.\n"
            f"Host {' '.join(names)}\n"
            f"    ProxyCommand {command} %h %p\n"
            "    ControlMaster auto\n    ControlPersist 8h\n"
            "    ControlPath ~/.ssh/%r@%h:%p\n"
            f"{END}\nHost *\n")


def install(config, script, python):
    real = config.resolve()
    old = real.read_bytes() if real.exists() else b""
    text = old.decode()
    pattern = re.compile(r"^" + re.escape(BEGIN) + r"\n.*?^" + re.escape(END) + r"\nHost \*\n", re.M | re.S)
    new = block(script, python) + pattern.sub("", text)
    if new == text:
        return None
    real.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    backup = real.with_name(real.name + time.strftime(".before-snap-reconnect-%m-%d-%Y-%H%M%S"))
    if old:
        backup.write_bytes(old)
        backup.chmod(0o600)
    fd, name = tempfile.mkstemp(prefix=".snap-config-", dir=real.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(new.encode())
        os.chmod(name, real.stat().st_mode & 0o777 if real.exists() else 0o600)
        subprocess.run(["/usr/bin/ssh", "-F", name, "-G", HOSTS[0]],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=10)
        if (real.read_bytes() if real.exists() else b"") != old:
            raise ValueError("SSH configuration changed concurrently; nothing written")
        os.replace(name, real)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return backup if old else None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--status", action="store_true")
    parser.add_argument("--defer-minutes", type=int, choices=range(15, 61), metavar="15..60")
    parser.add_argument("host", nargs="?")
    parser.add_argument("port", nargs="?", type=int)
    args = parser.parse_args(argv)
    if args.install or args.status or args.defer_minutes is not None:
        if args.host is not None or args.port is not None:
            parser.error("administrative modes cannot proxy a connection")
        if args.status and args.defer_minutes is not None:
            parser.error("--status cannot change the cooldown")
        with locked(STATE_DIR):
            if args.defer_minutes is not None:
                state = read_state(STATE_DIR)
                state.update(next_attempt=max(state["next_attempt"], time.time() + args.defer_minutes * 60),
                             failures=len(BACKOFF))
                write_state(STATE_DIR, state)
            if args.install:
                backup = install(Path.home() / ".ssh/config", Path(__file__).resolve(),
                                 Path(shutil.which("python3") or sys.executable).absolute())
                print("Installed shared SNAP reconnect guard; no network attempts made.")
                if backup:
                    print("Private backup:", backup)
            state = read_state(STATE_DIR)
            print(json.dumps({**state, "cooldown_remaining_seconds": max(0, math.ceil(
                state["next_attempt"] - time.time()))}, sort_keys=True))
        return 0
    if args.host is None or args.port is None:
        parser.error("supply host and port, or --install/--status/--defer-minutes")
    return proxy(args.host, args.port)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Deferred, OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"snap-reconnect: {error}", file=sys.stderr)
        sys.exit(255)
