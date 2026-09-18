#!/usr/bin/env python3
"""Detect a wedged Google Chrome zombie leak on macOS; optionally SIGKILL that Chrome.

TLDR: --check prints counts; launchd uses --quit-if-wedged --notify and only kills Chrome
when it already has >=100 unreaped zombie children (the 09-17-2026 stall), never on a timer.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

NOTIFY_ZOMBIES = 50
QUIT_ZOMBIES = 100
DEBOUNCE_SEC = 30 * 60
LOG = Path.home() / "Library/Logs/chrome_zombie_watch.log"
STATE = Path.home() / "Library/Logs/chrome_zombie_watch.state"


def _run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)


def chrome_main_pids() -> list[int]:
    try:
        out = _run(["pgrep", "-f", r"Google Chrome\.app/Contents/MacOS/Google Chrome$"])
    except subprocess.CalledProcessError:
        return []
    pids = []
    for line in out.splitlines():
        line = line.strip()
        if line.isdigit():
            pids.append(int(line))
    return pids


def zombie_children_of(ppids: set[int]) -> int:
    if not ppids:
        return 0
    # pid, ppid, state
    out = _run(["ps", "-axo", "pid=,ppid=,stat="])
    n = 0
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            ppid = int(parts[1])
        except ValueError:
            continue
        state = parts[2]
        if ppid in ppids and state[:1] == "Z":
            n += 1
    return n


def load_1min() -> float | None:
    try:
        out = _run(["sysctl", "-n", "vm.loadavg"])
        # "{ 1.23 4.56 7.89 }"
        nums = [float(x) for x in out.replace("{", " ").replace("}", " ").split() if x.replace(".", "", 1).isdigit()]
        return nums[0] if nums else None
    except (subprocess.CalledProcessError, ValueError):
        return None


def notify(title: str, body: str) -> None:
    script = (
        f'display notification {json.dumps(body)} '
        f'with title {json.dumps(title)}'
    )
    subprocess.run(["osascript", "-e", script], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%m-%d-%Y %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"{stamp} {msg}\n")


def read_state() -> dict:
    try:
        return json.loads(STATE.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def write_state(data: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(data))


def kill_chrome(pids: list[int]) -> None:
    for pid in pids:
        try:
            os.kill(pid, 9)
        except ProcessLookupError:
            pass
        except PermissionError as e:
            log(f"SIGKILL {pid} failed: {e}")


def snapshot() -> dict:
    pids = chrome_main_pids()
    z = zombie_children_of(set(pids))
    return {
        "chrome_pids": pids,
        "chrome_zombie_children": z,
        "load_1min": load_1min(),
        "wedged": z >= QUIT_ZOMBIES,
        "notify": z >= NOTIFY_ZOMBIES,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true", help="print JSON snapshot and exit 0 even if wedged")
    p.add_argument("--quit-if-wedged", action="store_true", help=f"SIGKILL Chrome if zombie children >= {QUIT_ZOMBIES}")
    p.add_argument("--notify", action="store_true", help="macOS notification at >= notify/quit thresholds")
    args = p.parse_args()

    snap = snapshot()
    if args.check:
        json.dump(snap, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    z = snap["chrome_zombie_children"]
    now = time.time()
    st = read_state()
    last_note = float(st.get("last_notify", 0))
    last_kill = float(st.get("last_kill", 0))

    if z < NOTIFY_ZOMBIES:
        log(f"ok chrome_pids={snap['chrome_pids']} zombies={z} load1={snap['load_1min']}")
        return 0

    msg = (
        f"Chrome zombie children={z} (notify>={NOTIFY_ZOMBIES} quit>={QUIT_ZOMBIES}) "
        f"pids={snap['chrome_pids']} load1={snap['load_1min']}"
    )
    log(msg)

    if args.notify and (now - last_note) >= DEBOUNCE_SEC:
        if z >= QUIT_ZOMBIES:
            notify("Chrome wedged (zombies)", f"{z} dead children. Tripwire will SIGKILL Chrome.")
        else:
            notify("Chrome leaking zombies", f"{z} unreaped children. Quit Chrome (Cmd-Q) if the Mac is stalling.")
        st["last_notify"] = now

    if args.quit_if_wedged and z >= QUIT_ZOMBIES and snap["chrome_pids"]:
        if (now - last_kill) < 60:
            write_state(st)
            return 0
        log(f"SIGKILL Chrome pids={snap['chrome_pids']} zombies={z}")
        kill_chrome(snap["chrome_pids"])
        st["last_kill"] = now
        if args.notify:
            notify("Chrome SIGKILL", f"Reaped a {z}-zombie leak. Relaunch Chrome when you need it.")
        write_state(st)
        return 0

    write_state(st)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
