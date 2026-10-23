#!/usr/bin/env python3
"""Explicit one-shot Sherlock allocation refresh through the private runner.

Reuses one herdr-interactive job or submits the installed server.sbatch once.
Pending jobs return nonzero without polling. This does not repair ordinary
Stanford SSH authentication or reconnect Herdr. The proxy still needs an
authenticated ordinary sherlock login master and compute-host credentials.
Local writes use backups and atomic replacement; keep other local file writers
idle because their unrelated processes do not share this helper's lock.
"""

import argparse
import base64
import fcntl
import json
import math
import os
from pathlib import Path
import re
import shlex
import stat
import struct
import subprocess
import sys
import tempfile
import time
from datetime import datetime


JOB_NAME = "herdr-interactive"
USER = "brando9"
HOST = re.compile(r"sh\d{2}-\d{2}n\d+")
MARKER = "HERDR_ALLOCATE_RESULT="

# A single bounded runner request. No loop, retries, SSH server, or scheduler poll.
REMOTE_SCRIPT = r'''
import fcntl, json, os, re, subprocess, time
from pathlib import Path
from datetime import datetime
os.environ['TZ'] = 'America/Los_Angeles'
time.tzset()
os.umask(0o077)
home = Path.home()
state = home / '.local/state/herdr-stanford'
state.mkdir(parents=True, exist_ok=True)
lock = (state / 'refresh.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
def run(args, **kwargs):
    p = subprocess.run(args, text=True, capture_output=True, timeout=30, **kwargs)
    if p.returncode:
        raise RuntimeError('Command failed: ' + args[0] + ': ' + p.stderr.strip())
    return p.stdout.strip()
user = run(['id', '-un'])
if user != 'brando9':
    raise RuntimeError('Runner user does not match brando9')
rows = run(['squeue', '--noheader', '--user', user, '--name', 'herdr-interactive',
            '--format=%i|%j|%u|%T']).splitlines()
jobs = []
for row in rows:
    fields = row.strip().split('|')
    if len(fields) != 4 or not re.fullmatch(r'[1-9]\d*', fields[0]) or fields[1:3] != ['herdr-interactive', user]:
        raise RuntimeError('Unexpected or mismatched scheduler row')
    jobs.append(fields[0])
if len(jobs) > 1:
    raise RuntimeError('More than one active herdr-interactive job; no submission or local update')
submitted = False
if not jobs:
    script = home / '.local/share/herdr-stanford/server.sbatch'
    if not script.is_file():
        raise RuntimeError('Installed server.sbatch is missing')
    env = {k:v for k,v in os.environ.items() if not k.startswith('SBATCH_')}
    job = run(['sbatch', '--parsable', str(script)], cwd=home, env=env).split(';')[0]
    if not re.fullmatch(r'[1-9]\d*', job):
        raise RuntimeError('Uncertain sbatch result; inspect scheduler before rerunning')
    submitted = True
else:
    job = jobs[0]
raw = run(['scontrol', 'show', 'job', '--oneliner', job])
fields = dict(re.findall(r'(?:^|\s)(JobId|JobName|UserId|JobState|NodeList|EndTime)=([^\s]+)', raw))
if fields.get('JobId') != job or fields.get('JobName') != 'herdr-interactive' or not re.fullmatch(r'brando9\(\d+\)', fields.get('UserId', '')):
    raise RuntimeError('scontrol job identity/name/user mismatch')
data = {'job_id':job, 'job_name':'herdr-interactive', 'user':user, 'submitted':submitted,
        'status':fields.get('JobState', 'UNKNOWN')}
if data['status'] == 'RUNNING':
    host = fields.get('NodeList', '')
    if not re.fullmatch(r'sh\d{2}-\d{2}n\d+', host):
        raise RuntimeError('Expected exactly one concrete compute node')
    expiry = int(datetime.strptime(fields['EndTime'], '%Y-%m-%dT%H:%M:%S').timestamp())
    if expiry <= time.time():
        raise RuntimeError('Running job has an expired allocation deadline')
    scanned = run(['ssh-keyscan', '-T', '5', '-t', 'ed25519', host])
    keys = set()
    for line in scanned.splitlines():
        if line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) != 3 or parts[1] != 'ssh-ed25519' or parts[0] not in (host, host+'.sherlock.stanford.edu'):
            raise RuntimeError('Unexpected host key scan output')
        keys.add(parts[2])
    if len(keys) != 1:
        raise RuntimeError('Missing or inconsistent compute ED25519 host key')
    data.update(host=host, expires_at=expiry, key_type='ssh-ed25519', host_key=keys.pop())
print('HERDR_ALLOCATE_RESULT=' + json.dumps(data))
'''


class AllocationError(Exception):
    pass


def run_command(args, timeout=60):
    try:
        return subprocess.run(args, text=True, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise AllocationError(f"Command did not complete: {args[0]}. Inspect its receipt before retrying: {error}") from error


def retrieve(ctl):
    command = "python3 - <<'HERDR_ALLOCATE_PY'\n" + REMOTE_SCRIPT + "\nHERDR_ALLOCATE_PY\n"
    result = run_command([ctl, "--wait-seconds", "90", "exec", command], timeout=180)
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    if result.returncode:
        raise AllocationError("Private-runner request failed or remains unresolved; inspect its request/run receipt before retrying")
    records = [line[len(MARKER):] for line in result.stdout.splitlines() if line.startswith(MARKER)]
    if len(records) != 1:
        raise AllocationError("Missing/ambiguous allocation receipt; no local files changed")
    return json.loads(records[0])


def validate_result(data, now):
    if not isinstance(data, dict) or data.get("job_name") != JOB_NAME or data.get("user") != USER:
        raise AllocationError("Allocation receipt has the wrong job name or user")
    if not re.fullmatch(r"[1-9]\d*", str(data.get("job_id", ""))):
        raise AllocationError("Invalid Slurm job ID")
    if data.get("status") != "RUNNING":
        raise AllocationError(f"Job {data['job_id']} is {data.get('status', 'UNKNOWN')}; "
                              "no local files changed. Invoke this helper later after the scheduler starts it.")
    if not isinstance(data.get("host"), str) or not HOST.fullmatch(data["host"]):
        raise AllocationError("Allocation does not identify one concrete Sherlock compute host")
    expiry = data.get("expires_at")
    try:
        valid_expiry = not isinstance(expiry, bool) and isinstance(expiry, (int, float)) and math.isfinite(expiry) and expiry > now
    except OverflowError:
        valid_expiry = False
    if not valid_expiry:
        raise AllocationError("Allocation expiry is invalid or expired; no local files changed")
    if data.get("key_type") != "ssh-ed25519" or not isinstance(data.get("host_key"), str):
        raise AllocationError("Missing ED25519 host key")
    try:
        raw = base64.b64decode(data["host_key"], validate=True)
    except ValueError as error:
        raise AllocationError("Invalid base64 host key") from error
    prefix = struct.pack(">I", 11) + b"ssh-ed25519" + struct.pack(">I", 32)
    if len(raw) != len(prefix) + 32 or not raw.startswith(prefix):
        raise AllocationError("Malformed ED25519 host key")


def read_file(path, optional=False):
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except FileNotFoundError:
        if optional:
            return None, None
        raise
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise AllocationError(f"Refusing non-owned/non-regular file: {path}")
        raw = stream.read(4 * 1024 * 1024 + 1)
        if len(raw) > 4 * 1024 * 1024:
            raise AllocationError(f"File unexpectedly large: {path}")
        return raw, (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def replace_guarded(path, previous, replacement):
    if previous[0] == replacement:
        return
    if read_file(path, optional=True) != previous:
        raise AllocationError(f"Concurrent change detected in {path}; inspect backups before retrying")
    if previous[0] is not None:
        stamp = datetime.now().astimezone().strftime("%m-%d-%Y-%H%M%S-%f")
        backup = path.with_name(path.name + ".before-allocation-" + stamp)
        with os.fdopen(os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as stream:
            stream.write(previous[0]); stream.flush(); os.fsync(stream.fileno())
    fd, name = tempfile.mkstemp(prefix=".herdr-allocation-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(replacement); stream.flush(); os.fsync(stream.fileno())
        if read_file(path, optional=True) != previous:
            raise AllocationError(f"Concurrent change detected in {path}; update aborted")
        os.replace(name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        if read_file(path)[0] != replacement:
            raise AllocationError(f"Concurrent change after writing {path}; no automatic rollback")
    finally:
        Path(name).unlink(missing_ok=True)


def updated_config(raw, host):
    lines = raw.decode().splitlines(keepends=True)
    active = False
    sections, hostnames = 0, []
    for index, line in enumerate(lines):
        words = shlex.split(line, comments=True)
        if not words:
            continue
        key = words[0].lower()
        if key in ("host", "match"):
            active = key == "host" and "herdr-sherlock" in words[1:]
            if active:
                if words[1:] != ["herdr-sherlock"]:
                    raise AllocationError("herdr-sherlock must have its own dedicated Host block")
                sections += 1
        elif active and key == "hostname":
            hostnames.append(index)
        elif active and key == "hostkeyalias" and words[1:] != [host]:
            raise AllocationError("Explicit HostKeyAlias does not match the new compute host; resolve it before refresh")
    if sections != 1 or len(hostnames) != 1:
        raise AllocationError("Expected exactly one Host herdr-sherlock block and HostName line")
    index = hostnames[0]
    pattern = r"^(\s*HostName\s+)(\S+)(.*)$"
    lines[index] = re.sub(pattern, lambda m: m[1] + host + m[3], lines[index], flags=re.I)
    return "".join(lines).encode()


def known_hosts_update(path, original, host, key):
    if original is not None:
        found = run_command(["ssh-keygen", "-F", host, "-f", str(path)])
        if found.returncode not in (0, 1):
            raise AllocationError("Could not inspect current host keys")
        existing = []
        for line in found.stdout.splitlines():
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if parts[0].startswith("@"):
                raise AllocationError("Marked host-key entry requires explicit inspection")
            if len(parts) >= 3 and parts[1] == "ssh-ed25519":
                existing.append(parts[2])
        if existing and any(value != key for value in existing):
            raise AllocationError("Changed known ED25519 host key; refusing replacement")
        if existing:
            return original
    prefix = original or b""
    if prefix and not prefix.endswith(b"\n"):
        prefix += b"\n"
    return prefix + f"{host} ssh-ed25519 {key}\n".encode()


def apply_result(data, lease, config, known_hosts):
    validate_result(data, time.time())
    before_config = read_file(config)
    next_config = updated_config(before_config[0], data["host"])
    before_keys = read_file(known_hosts, optional=True)
    next_keys = known_hosts_update(known_hosts, before_keys[0], data["host"], data["host_key"])
    before_lease = read_file(lease, optional=True)
    next_lease = json.loads(before_lease[0]) if before_lease[0] else {}
    if not isinstance(next_lease, dict):
        raise AllocationError("Existing lease is not a JSON object")
    next_lease.update(host=data["host"], job_id=str(data["job_id"]), expires_at=data["expires_at"],
                      session="default", automatic_restart=False)
    encoded_lease = (json.dumps(next_lease, indent=2) + "\n").encode()
    validate_result(data, time.time())
    # Trust material first; lease last. A changed host with an old lease is rejected by the proxy.
    replace_guarded(known_hosts, before_keys, next_keys)
    replace_guarded(config, before_config, next_config)
    replace_guarded(lease, before_lease, encoded_lease)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sherlockctl", default="sherlockctl")
    parser.add_argument("--lease", type=Path, default=Path.home() / ".local/state/herdr-stanford/sherlock.json")
    parser.add_argument("--config", type=Path, default=Path.home() / ".ssh/herdr-stanford.conf")
    parser.add_argument("--known-hosts", type=Path, default=Path.home() / ".ssh/known_hosts")
    args = parser.parse_args(argv)
    try:
        args.lease.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        lock_path = args.lease.parent / "allocate.lock"
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(fd, "a+b") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            data = retrieve(args.sherlockctl)
            apply_result(data, args.lease, args.config, args.known_hosts)
        deadline = datetime.fromtimestamp(data["expires_at"]).astimezone().strftime("%m-%d-%Y %H:%M:%S %Z")
        print(f"Sherlock job {data['job_id']}: {data['host']}, lease expires {deadline}.")
        print("Saved route and host key refreshed. Ordinary SSH authentication and Herdr connectivity still require verification.")
        return 0
    except (AllocationError, OSError, ValueError, UnicodeError) as error:
        print(f"Allocation refresh failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
