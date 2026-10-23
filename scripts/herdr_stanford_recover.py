#!/usr/bin/env python3
"""Explicit, attended recovery of existing Stanford Herdr machine profiles.

Herdr 0.9.5 source contracts:
https://github.com/herdrdev/herdr/blob/v0.9.5/src/client/endpoint/catalog.rs
https://github.com/herdrdev/herdr/blob/v0.9.5/src/cli/target.rs#L260

This helper does not allocate nodes, install/start servers, or run in the
background. The operator must provision a policy-compliant, live compute
allocation before recovering Sherlock. It cannot extend authentication or job
lifetimes. Migration is an implementation-level catalog edit because Herdr
0.9.5 has no target-edit command. Keep other catalog writers idle while using
migrate-target: Herdr does not share this helper's advisory lock, so comparison
immediately before atomic replacement cannot eliminate the final race window.
"""

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from datetime import datetime


PROFILES = ("Sherlock", "FarmShare")
MAX_BYTES = 64 * 1024
COMPUTE_HOST = re.compile(r"sh\d{2}-\d{2}n\d+(?:\.sherlock\.stanford\.edu)?\.?", re.I)


class RecoveryError(Exception):
    pass


def default_catalog():
    base = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state")))
    return base / "herdr/client/endpoints.json"


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RecoveryError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(raw):
    try:
        return json.loads(raw, object_pairs_hook=unique_object)
    except (ValueError, UnicodeError) as error:
        raise RecoveryError(f"Invalid JSON: {error}") from error


def validate_target(target):
    if (not isinstance(target, str) or not target or target.startswith("-")
            or len(target.encode()) > 1024
            or any(ord(char) < 32 or ord(char) == 127 for char in target)):
        raise RecoveryError("Invalid SSH target")
    authority = target.removeprefix("ssh://")
    if "@" in authority and ":" in authority.rsplit("@", 1)[0]:
        raise RecoveryError("SSH targets must not embed passwords")


def read_snapshot(path):
    """Read a private regular file without following a final symlink."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid():
                raise RecoveryError("Catalog must be a regular file owned by this user")
            raw = stream.read(MAX_BYTES + 1)
            after = os.fstat(stream.fileno())
    except OSError as error:
        raise RecoveryError(f"Cannot read catalog {path}: {error}") from error
    if len(raw) > MAX_BYTES:
        raise RecoveryError("Catalog exceeds Herdr's 64 KiB limit")
    signature = lambda info: (info.st_dev, info.st_ino, info.st_size,
                              info.st_mtime_ns, info.st_ctime_ns)
    if signature(before) != signature(after):
        raise RecoveryError("Catalog changed while being read; retry after the writer finishes")
    return raw, signature(after)


def load_catalog(path):
    raw, identity = read_snapshot(path)
    data = parse_json(raw)
    if not isinstance(data, dict) or data.get("version") != 1:
        raise RecoveryError("Only Herdr endpoint catalog version 1 is supported")
    rows = data.get("ssh")
    if not isinstance(rows, list) or len(rows) > 64:
        raise RecoveryError("Catalog must contain at most 64 SSH profiles")
    ids = set()
    for row in rows:
        if not isinstance(row, dict) or not re.fullmatch(r"[0-9a-f]{32}", str(row.get("id", ""))):
            raise RecoveryError("Invalid saved profile ID")
        if row["id"] in ids:
            raise RecoveryError("Duplicate saved profile ID")
        ids.add(row["id"])
        if not isinstance(row.get("label"), str) or not isinstance(row.get("session"), str):
            raise RecoveryError("Invalid profile label/session")
        if not isinstance(row.get("enabled"), bool):
            raise RecoveryError("Invalid profile enabled state")
        validate_target(row.get("target"))
    return data, raw, identity


def select_profile(data, label):
    matches = [row for row in data["ssh"] if row["label"] == label]
    if len(matches) != 1:
        raise RecoveryError(f"Expected exactly one existing {label} profile; found {len(matches)}")
    return matches[0]


def checked_run(args, capture=True, timeout=60):
    try:
        result = subprocess.run(args, text=True, capture_output=capture, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RecoveryError(f"Command failed: {args[0]}: {error}") from error
    if result.returncode:
        detail = ((result.stderr or result.stdout or "").strip() if capture else "")
        raise RecoveryError(f"Command exited {result.returncode}: {' '.join(args)}"
                            + (f"\n{detail}" if detail else ""))
    return result.stdout if capture else ""


def resolve_host(target, ssh="ssh"):
    validate_target(target)
    output = checked_run([ssh, "-G", target], timeout=15)
    matches = [line.split(None, 1)[1] for line in output.splitlines()
               if line.startswith("hostname ")]
    if len(matches) != 1:
        raise RecoveryError("ssh -G did not return exactly one resolved hostname")
    return matches[0].lower()


def guard_target(label, target, ssh="ssh"):
    host = resolve_host(target, ssh)
    if label == "Sherlock" and not COMPUTE_HOST.fullmatch(host):
        raise RecoveryError(f"Sherlock target {target!r} resolves to {host!r}; refusing Herdr "
                            "connection. Use a dedicated alias resolving to the concrete "
                            "compute node in the current owned allocation, not a login node.")
    return host


@contextlib.contextmanager
def catalog_lock(path):
    lock = path.with_name(path.name + ".stanford-recovery.lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(fd, "a+b") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
                raise RecoveryError("Unsafe migration lock file")
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
    except BlockingIOError as error:
        raise RecoveryError("Another recovery helper is editing the catalog") from error


def assert_unchanged(path, raw, identity):
    now, current_identity = read_snapshot(path)
    if current_identity != identity or now != raw:
        raise RecoveryError("Concurrent catalog change detected; migration was not applied")


def fsync_directory(directory):
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def migrate_target(path, label, target, expected_target, ssh="ssh"):
    """Change one target, retain profile identity/order and all other JSON fields."""
    guard_target(label, target, ssh)
    with catalog_lock(path):
        data, raw, identity = load_catalog(path)
        row = select_profile(data, label)
        if row["target"] == target:
            print(f"{label}: target already {target}; no write or duplicate profile")
            return None
        if row["target"] != expected_target:
            raise RecoveryError(f"{label}: expected target {expected_target!r}, "
                                f"found {row['target']!r}; migration was not applied")
        row["target"] = target
        replacement = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode()
        if len(replacement) > MAX_BYTES:
            raise RecoveryError("Updated catalog would exceed Herdr's 64 KiB limit")
        assert_unchanged(path, raw, identity)
        stamp = datetime.now().astimezone().strftime("%m-%d-%Y-%H%M%S-%f")
        backup = path.with_name(f"{path.name}.before-target-{stamp}-{os.getpid()}")
        with os.fdopen(os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        fd, temp_name = tempfile.mkstemp(prefix=".endpoints-recovery-", dir=path.parent)
        temporary = Path(temp_name)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(replacement)
                stream.flush()
                os.fsync(stream.fileno())
            assert_unchanged(path, raw, identity)
            os.replace(temporary, path)
            fsync_directory(path.parent)
            observed, _ = read_snapshot(path)
            if observed != replacement:
                raise RecoveryError(f"Catalog changed after replacement; inspect {backup}. "
                                    "No automatic rollback was attempted.")
        finally:
            temporary.unlink(missing_ok=True)
        print(f"{label}: retained ID {row['id']}; target {expected_target} -> {target}")
        print(f"Backup: {backup}")
        print(f"Catalog SHA-256: {hashlib.sha256(replacement).hexdigest()}")
        return backup


def verify_cli_profile(herdr, expected):
    rows = parse_json(checked_run([herdr, "machine", "list", "--json"]))
    if not isinstance(rows, list):
        raise RecoveryError("Unexpected Herdr machine-list response")
    matches = [row for row in rows if row.get("id") == expected["id"]]
    if len(matches) != 1 or any(matches[0].get(key) != expected[key]
                               for key in ("label", "target", "session")):
        raise RecoveryError("Herdr's active profile differs from the guarded catalog; "
                            "check XDG_STATE_HOME and concurrent changes")
    return matches[0]


def reconnect_profile(path, label, herdr="herdr", ssh="ssh"):
    data, _, _ = load_catalog(path)
    profile = select_profile(data, label)
    host = guard_target(label, profile["target"], ssh)
    verify_cli_profile(herdr, profile)
    # Enable is necessary: Herdr 0.9.5 refuses reconnect/status selectors for disabled profiles.
    checked_run([herdr, "machine", "enable", profile["id"]])
    enabled = verify_cli_profile(herdr, profile)
    if enabled.get("enabled") is not True:
        raise RecoveryError(f"{label} did not remain enabled")
    guard_target(label, profile["target"], ssh)
    print(f"{label}: authenticating {profile['target']} ({host}), session {profile['session']}", flush=True)
    checked_run([herdr, "machine", "reconnect", profile["id"]], capture=False, timeout=None)
    verify_cli_profile(herdr, profile)
    guard_target(label, profile["target"], ssh)
    rows = parse_json(checked_run([herdr, "machine", "status", profile["id"], "--json"]))
    if (not isinstance(rows, list) or len(rows) != 1 or rows[0].get("id") != profile["id"]
            or rows[0].get("status") != "reachable" or rows[0].get("error") is not None):
        raise RecoveryError(f"{label}: post-reconnect status is not reachable: {rows}")
    agents = checked_run([herdr, "--machine", profile["id"], "agent", "list"])
    final = verify_cli_profile(herdr, profile)
    if final.get("enabled") is not True:
        raise RecoveryError(f"{label}: profile was disabled during verification")
    print(f"{label}: enabled, reachable; saved-machine agent list succeeded")
    if agents.strip():
        print(agents.rstrip())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--catalog", type=Path, default=default_catalog(), help="Endpoint catalog path")
    parser.add_argument("--herdr", default="herdr", help="Herdr executable")
    parser.add_argument("--ssh", default="ssh", help="OpenSSH executable")
    sub = parser.add_subparsers(dest="command", required=True)
    migrate = sub.add_parser("migrate-target", help="Guarded target-only migration preserving profile ID")
    migrate.add_argument("profile", choices=PROFILES)
    migrate.add_argument("target", help="Dedicated SSH alias or concrete host")
    migrate.add_argument("--expect-target", required=True, help="Current target expected before migration")
    reconnect = sub.add_parser("reconnect", help="Attend authentication; enable and verify existing profiles")
    reconnect.add_argument("profiles", nargs="*", help="Sherlock and/or FarmShare; defaults to both")
    args = parser.parse_args(argv)
    try:
        if args.command == "migrate-target":
            migrate_target(args.catalog, args.profile, args.target, args.expect_target, args.ssh)
            return 0
        labels = args.profiles or list(PROFILES)
        if any(label not in PROFILES for label in labels) or len(set(labels)) != len(labels):
            raise RecoveryError("Choose Sherlock and/or FarmShare exactly once")
        if not sys.stdin.isatty():
            raise RecoveryError("Reconnect requires an interactive terminal for native SSH authentication. "
                                "Run this command in a terminal; no profiles were changed.")
        failed = False
        for label in labels:
            try:
                reconnect_profile(args.catalog, label, args.herdr, args.ssh)
            except RecoveryError as error:
                failed = True
                print(f"{label}: {error}", file=sys.stderr)
        return int(failed)
    except (RecoveryError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
