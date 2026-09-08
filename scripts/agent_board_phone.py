#!/usr/bin/env python3
"""Install a per-user Tailscale service and privately serve only board.html."""

import argparse
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import time
from urllib.request import ProxyHandler, build_opener

from agent_board_serve import PORT


LABEL = "com.brando.agentboard.tailscale"


def install_service(label, arguments, runtime):
    """Install or update one user service, preserving a matching running job."""
    agents = Path.home() / "Library/LaunchAgents"
    agents.mkdir(parents=True, exist_ok=True)
    plist = agents / f"{label}.plist"
    config = {
        "Label": label,
        "ProgramArguments": arguments,
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 10,
        "Umask": 0o077,
        "StandardOutPath": str(runtime / f"{label}.log"),
        "StandardErrorPath": str(runtime / f"{label}.err"),
    }
    payload = plistlib.dumps(config)
    changed = not plist.exists() or plist.read_bytes() != payload
    service = f"gui/{os.getuid()}/{label}"
    loaded = subprocess.run(["launchctl", "print", service],
                            capture_output=True).returncode == 0
    if changed:
        temporary = plist.with_suffix(".tmp")
        temporary.write_bytes(payload)
        temporary.chmod(0o600)
        temporary.replace(plist)
    if loaded and changed:
        subprocess.run(["launchctl", "bootout", service], check=True)
        loaded = False
    if not loaded:
        # bootout returns before launchd necessarily completes removal.
        for _ in range(20):
            started = subprocess.run(["launchctl", "bootstrap", f"gui/{os.getuid()}",
                                      str(plist)], capture_output=True)
            if started.returncode == 0:
                break
            if started.returncode != 5:
                started.check_returncode()
            time.sleep(0.2)
        started.check_returncode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", action="store_true", help="inspect without changes")
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("this installer is for macOS")
    cli, daemon = shutil.which("tailscale"), shutil.which("tailscaled")
    if not cli or not daemon:
        parser.error("install the open source variant first: brew install tailscale")
    runtime = Path.home() / ".agent-board/tailscale"
    command = [cli, f"--socket={runtime / 'tailscaled.sock'}"]
    if args.status:
        return subprocess.run(command + ["status"]).returncode
    board = Path.home() / ".agent-board/board.html"
    if not board.is_file() or board.is_symlink():
        parser.error("expected a regular ~/.agent-board/board.html; install the board first")
    runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    runtime.chmod(0o700)
    install_service(LABEL, [daemon, "--tun=userspace-networking",
                           f"--statedir={runtime}",
                           f"--socket={runtime / 'tailscaled.sock'}"], runtime)
    for _ in range(50):
        status = subprocess.run(command + ["status", "--json"], capture_output=True)
        if status.stdout:
            break
        time.sleep(0.1)
    else:
        parser.error(f"Tailscale did not start; inspect {runtime / (LABEL + '.err')}")
    state = json.loads(status.stdout)
    if state.get("BackendState") != "Running":
        connected = subprocess.run(command + ["up", "--hostname=agent-board",
                                   "--accept-dns=false", "--accept-routes=false",
                                   "--timeout=5s"])
        if connected.returncode:
            print("Sign in using the link above, then run this script again.")
            return connected.returncode
    server = Path(__file__).resolve().with_name("agent_board_serve.py")
    install_service("com.brando.agentboard.web", [sys.executable, str(server)], runtime)
    target = f"http://127.0.0.1:{PORT}"
    opener = build_opener(ProxyHandler({}))
    for _ in range(50):
        try:
            with opener.open(target, timeout=1) as response:
                if response.headers.get("X-Agent-Board") == "1":
                    break
        except OSError:
            pass
        time.sleep(0.1)
    else:
        parser.error(f"Board server did not start on {target}; inspect the service error log")
    # The loopback server serves only board.html, with no directory browsing.
    return subprocess.run(command + ["serve", "--bg", "--https=443", "--yes",
                                     target]).returncode


if __name__ == "__main__":
    sys.exit(main())
