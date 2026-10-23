#!/usr/bin/env python3
"""Gate an explicitly invoked SSH ProxyCommand on a bounded Sherlock lease.

Arguments are SSH's %h %p. Lease: ~/.local/state/herdr-stanford/sherlock.json
with host, job_id, expires_at (Unix seconds). This checks the saved expiry; it
does not poll the scheduler or prove that a job has not ended early. An ordinary
authenticated `sherlock` login master is required for noninteractive forwarding.
Compute-host authentication may additionally require central Stanford Kerberos
credentials. All diagnostics go to stderr; stdout belongs to the SSH transport.
"""

import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import time


COMPUTE_HOST = re.compile(r"sh\d{2}-\d{2}n\d+(?:\.sherlock\.stanford\.edu)?", re.I)
MAX_LEASE_BYTES = 16 * 1024


class LeaseError(Exception):
    pass


def normalized_host(value):
    if not isinstance(value, str):
        raise LeaseError("Lease host must be a concrete Sherlock compute hostname")
    value = value.lower().removesuffix(".")
    if not COMPUTE_HOST.fullmatch(value):
        raise LeaseError("Lease host must be a concrete Sherlock compute hostname")
    return value


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise LeaseError(f"Duplicate lease field: {key}")
        result[key] = value
    return result


def read_lease(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise LeaseError("Lease must be a regular file owned by this user")
        if info.st_mode & 0o022:
            raise LeaseError("Lease must not be writable by other users")
        raw = stream.read(MAX_LEASE_BYTES + 1)
    if len(raw) > MAX_LEASE_BYTES:
        raise LeaseError("Lease file is too large")
    data = json.loads(raw, object_pairs_hook=unique_object)
    if not isinstance(data, dict):
        raise LeaseError("Lease must be a JSON object")
    return data


def validate_lease(data, host, port, now):
    requested = normalized_host(host)
    if port != "22":
        raise LeaseError("Only SSH port 22 is permitted")
    leased = normalized_host(data.get("host"))
    if requested != leased:
        raise LeaseError("Requested compute host does not match the current lease")
    job = data.get("job_id")
    if isinstance(job, bool) or not isinstance(job, (int, str)) or not re.fullmatch(r"[1-9]\d*", str(job)):
        raise LeaseError("Lease job_id must be a positive Slurm job number")
    expiry = data.get("expires_at")
    try:
        finite_expiry = not isinstance(expiry, bool) and isinstance(expiry, (int, float)) and math.isfinite(expiry)
    except OverflowError:
        finite_expiry = False
    if not finite_expiry:
        raise LeaseError("Lease expires_at must be finite Unix seconds")
    if expiry <= now:
        raise LeaseError("Sherlock allocation lease has expired; renew it from a verified owned allocation")
    return leased


def main(argv=None, lease_path=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print("Sherlock proxy: expected compute hostname and port", file=sys.stderr)
        return 1
    path = lease_path or Path.home() / ".local/state/herdr-stanford/sherlock.json"
    try:
        data = read_lease(path)
        host = validate_lease(data, args[0], args[1], time.time())
        os.execvp("ssh", ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                          "-W", f"{host}:22", "sherlock"])
    except (LeaseError, OSError, ValueError, UnicodeError) as error:
        print(f"Sherlock proxy: {error}", file=sys.stderr)
        return 1
    # os.execvp never returns on success.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
