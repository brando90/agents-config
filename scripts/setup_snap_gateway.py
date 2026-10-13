#!/usr/bin/env python3
# TLDR: Route SSH for every SNAP node Brando uses through Stanford's official whale.stanford.edu
# gateway, so SNAP never needs the Cisco VPN. Owns one marked block in ~/.ssh/config (idempotent),
# keeps a private backup, and never edits other stanzas or known_hosts entries.
#
# USAGE
#   python3 ~/agents-config/scripts/setup_snap_gateway.py            # install/refresh, then test every node
#   python3 ~/agents-config/scripts/setup_snap_gateway.py --check    # test only, change nothing
#   python3 ~/agents-config/scripts/setup_snap_gateway.py --no-test  # install/refresh without connecting
#   python3 ~/agents-config/scripts/setup_snap_gateway.py --remove   # delete the managed block
# Add --accept-new-hostkeys on a Mac that has never seen a node: first-use trust only; a changed
# key is still refused.
#
# ENV  SNAP_SSH_USER (default brando9), SNAP_GATEWAY (default whale.stanford.edu),
#      SNAP_SSH_CONFIG (default ~/.ssh/config).
# Docs: machine/snap.md, "Internet-only laptop dispatch through the official gateway".

import argparse
import concurrent.futures
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

# Keep in sync with OPEN_NODES/GATED_NODES in snap_health.sh. ilc is the Slurm controller that
# srun/sbatch to the gated nodes start from; rambo (CPU) joined the gated set by 10-13-2026.
OPEN_NODES = ["skampere1", "skampere2", "skampere3", "mercury1", "mercury2"]
CONTROLLER = "ilc"
GATED_NODES = (["hyperturing1", "hyperturing2"] + [f"ampere{i}" for i in range(1, 10)]
               + ["turing1", "turing2", "turing3", "blackwell1", "rambo"])
NODES = OPEN_NODES + [CONTROLLER] + GATED_NODES
DOMAIN = "stanford.edu"
BEGIN = "# >>> agents-config snap-gateway >>>"
END = "# <<< agents-config snap-gateway <<<"
HOST_RE = re.compile(r"^\s*(host|match)\b", re.I)
BLOCK_RE = re.compile(r"^" + re.escape(BEGIN) + r"\n.*?^" + re.escape(END) + r"\n\n?", re.S | re.M)


def fqdn(node):
    return f"{node}.{DOMAIN}"


def managed_block(user, gateway):
    if gateway in NODES or gateway in map(fqdn, NODES):  # the gateway must never proxy through itself
        raise SystemExit(f"gateway {gateway} must not be one of the routed nodes")
    common = [f"    User {user}", f"    ProxyJump {user}@{gateway}",
              "    GSSAPIAuthentication yes", "    GSSAPIDelegateCredentials yes"]
    return "\n".join([
        BEGIN,
        "# Managed by ~/agents-config/scripts/setup_snap_gateway.py: SNAP over SSH without the Cisco VPN.",
        "# Change the node list in that script, not here. The gateway itself must never match.",
        "Host " + " ".join(NODES),
        f"    HostName %h.{DOMAIN}",
        *common,
        "Host " + " ".join(map(fqdn, NODES)),
        *common,
        END,
    ]) + "\n"


def without_block(text):
    return BLOCK_RE.sub("", text)


def with_block(text, block):
    """Insert the block before the first Host/Match line. ssh keeps the first value it reads, so the
    route wins over older stanzas, while leading global options stay global."""
    lines = without_block(text).splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    i = next((n for n, line in enumerate(lines) if HOST_RE.match(line)), len(lines))
    return "".join(lines[:i]) + block + ("\n" if i < len(lines) else "") + "".join(lines[i:])


def install(config, user, gateway, remove=False):
    """Write the new config atomically. Returns (changed, backup_path_or_None)."""
    real = config.resolve()  # a symlinked config (dotfiles repo) stays a symlink
    old = real.read_bytes() if real.exists() else b""
    text = old.decode("utf-8", "surrogateescape")
    new = without_block(text) if remove else with_block(text, managed_block(user, gateway))
    if new == text:
        return False, None
    real.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    backup = None
    if old:
        backup = real.with_name(real.name + time.strftime(".before-snap-gateway-%m-%d-%Y-%H%M%S"))
        backup.write_bytes(old)
        backup.chmod(0o600)
    mode = real.stat().st_mode & 0o777 if real.exists() else 0o600
    fd, tmp = tempfile.mkstemp(prefix=f".{real.name}.", dir=real.parent)
    with os.fdopen(fd, "w", encoding="utf-8", errors="surrogateescape") as fh:
        fh.write(new)
    os.chmod(tmp, mode)
    if (real.read_bytes() if real.exists() else b"") != old:  # another writer got there first
        os.unlink(tmp)
        raise SystemExit(f"{real} changed while this ran; nothing written. Re-run.")
    os.replace(tmp, real)
    return True, backup


def effective(host, config_args):
    out = subprocess.run(["ssh", *config_args, "-G", host], capture_output=True, text=True,
                         timeout=10).stdout
    values = {}
    for line in out.splitlines():
        key, _, value = line.partition(" ")
        values.setdefault(key, value)
    return values


def route_problems(user, gateway, config_args):
    problems = []
    for node in NODES:
        for name in (node, fqdn(node)):
            v = effective(name, config_args)
            if v.get("hostname") != fqdn(node) or v.get("proxyjump") != f"{user}@{gateway}":
                problems.append(f"{name}: hostname={v.get('hostname')} proxyjump={v.get('proxyjump', 'none')}")
    if effective(gateway, config_args).get("proxyjump", "none") != "none":
        problems.append(f"{gateway} is itself proxied (would recurse)")
    return problems


def probe(node, user, accept_new, config_args):
    """Fresh noninteractive login; a gated node that answers with its known key is reachable."""
    cmd = ["ssh", *config_args, "-v", "-T", "-S", "none", "-o", "BatchMode=yes",
           "-o", "ConnectTimeout=15"]
    if accept_new:
        cmd += ["-o", "StrictHostKeyChecking=accept-new"]
    try:
        r = subprocess.run(cmd + [f"{user}@{fqdn(node)}", "hostname"], capture_output=True,
                           text=True, timeout=60, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return node, "FAIL", "timed out after 60s"
    err = r.stderr
    if r.returncode == 0 and r.stdout.strip().startswith(node):
        return node, "OK", r.stdout.strip().splitlines()[0]
    if "REMOTE HOST IDENTIFICATION HAS CHANGED" in err:
        return node, "HOSTKEY_CHANGED", "refused; verify the new key from inside Stanford first"
    if "Host key verification failed" in err:
        return node, "HOSTKEY_UNKNOWN", "never seen here; verify it, or re-run with --accept-new-hostkeys"
    answered = (f"Host '{fqdn(node)}' is known and matches" in err
                or f"Permanently added '{fqdn(node)}'" in err)
    if "pam_slurm_adopt" in err or (answered and node in GATED_NODES):
        return node, "GATED", "route ok; login needs a Slurm allocation (srun/sbatch from ilc)"
    last = next((l for l in reversed(err.splitlines()) if l.strip() and not l.startswith("debug")), "")
    return node, "FAIL", last or f"exit {r.returncode}"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Route SNAP SSH through whale.stanford.edu (no Cisco VPN).")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="test only; change nothing")
    mode.add_argument("--no-test", action="store_true", help="install/refresh without connecting")
    mode.add_argument("--remove", action="store_true", help="delete the managed block")
    ap.add_argument("--accept-new-hostkeys", action="store_true",
                    help="first-use trust for nodes this Mac has never seen (changed keys stay refused)")
    args = ap.parse_args(argv)

    user = os.environ.get("SNAP_SSH_USER", "brando9")
    gateway = os.environ.get("SNAP_GATEWAY", "whale.stanford.edu")
    default = Path.home() / ".ssh" / "config"
    config = Path(os.environ.get("SNAP_SSH_CONFIG", str(default))).expanduser()
    config_args = [] if config == default else ["-F", str(config)]

    if not args.check:
        changed, backup = install(config, user, gateway, remove=args.remove)
        state = "updated" if changed else "already current"
        print(f"{config}: {state}" + (f" (backup: {backup})" if backup else ""))
        if args.remove:
            return 0

    problems = route_problems(user, gateway, config_args)
    if problems:
        print("route problems:\n  " + "\n  ".join(problems))
        return 1
    print(f"route: all {len(NODES)} nodes (short and .{DOMAIN} names) jump through {user}@{gateway}")
    if args.no_test:
        return 0

    if subprocess.run(["klist", "-s"], capture_output=True).returncode != 0:
        print("warning: no valid Kerberos ticket (klist -s); logins fail until it is renewed")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda n: probe(n, user, args.accept_new_hostkeys, config_args), NODES))
    for node, status, detail in results:
        print(f"  {status:<16} {node:<13} {detail}")
    failed = [node for node, status, _ in results if status not in ("OK", "GATED")]
    print(f"{len(NODES) - len(failed)}/{len(NODES)} nodes reachable without VPN"
          + (f"; check: {' '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
