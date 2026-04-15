#!/usr/bin/env python3
"""
DFS Job Queue Watcher Daemon

Polls a shared DFS directory for pending jobs, atomically claims them via
os.rename(), executes them with GPU-aware environment passthrough, and
routes results to completed/ or failed/.

All paths are derived from $HOME — no hardcoded absolute paths.

Usage:
    python dfs_job_watcher.py                       # defaults: 15s poll, 4h timeout
    python dfs_job_watcher.py --poll-interval 10 --timeout 7200
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("dfs_job_watcher")

# ---------------------------------------------------------------------------
# Path helpers (all relative to $HOME)
# ---------------------------------------------------------------------------

def _home() -> Path:
    h = os.environ.get("HOME") or os.path.expanduser("~")
    return Path(h)


def _queue_root() -> Path:
    return _home() / "dfs" / "job_queue"


# ---------------------------------------------------------------------------
# 1. Server initialisation — bootstrap agents-config (blocking)
# ---------------------------------------------------------------------------

def bootstrap_agents_config() -> None:
    target = _home() / "agents-config"
    if target.is_dir():
        log.info("Pulling latest agents-config …")
        cmd = ["git", "-C", str(target), "pull"]
    else:
        log.info("Cloning agents-config …")
        cmd = [
            "git", "clone",
            "https://github.com/brando90/agents-config",
            str(target),
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.critical(
            "agents-config git command failed (rc=%d): %s",
            result.returncode,
            result.stderr.strip(),
        )
        sys.exit(1)
    log.info("agents-config ready at %s", target)


# ---------------------------------------------------------------------------
# 2. Directory structure
# ---------------------------------------------------------------------------

SUBDIRS = ("pending", "running", "completed", "failed", "logs")


def ensure_queue_dirs() -> dict[str, Path]:
    root = _queue_root()
    paths: dict[str, Path] = {}
    for name in SUBDIRS:
        p = root / name
        p.mkdir(parents=True, exist_ok=True)
        paths[name] = p
    log.info("Job-queue dirs verified under %s", root)
    return paths


# ---------------------------------------------------------------------------
# 3. Atomic claim
# ---------------------------------------------------------------------------

def try_claim(src: Path, running_dir: Path, hostname: str) -> Path | None:
    """Attempt to atomically move *src* into running/.  Returns the new path
    on success, or ``None`` if another host grabbed it first."""
    dest = running_dir / f"{src.name}_{hostname}"
    try:
        os.rename(src, dest)
        return dest
    except OSError:
        return None


# ---------------------------------------------------------------------------
# 4. Job execution with GPU-safe timeout
# ---------------------------------------------------------------------------

def _kill_tree(pid: int) -> None:
    """Send SIGKILL to the entire process group rooted at *pid*."""
    try:
        os.killpg(pid, signal.SIGKILL)
    except OSError:
        pass


def run_job(job_path: Path, logs_dir: Path, hostname: str,
            timeout: int) -> int:
    """Execute *job_path* as a shell script.  Returns the exit code
    (or -1 for timeout)."""
    log_file = logs_dir / f"{job_path.stem}_{hostname}.log"

    with open(log_file, "w") as fh:
        try:
            proc = subprocess.Popen(
                ["bash", str(job_path)],
                stdout=fh,
                stderr=subprocess.STDOUT,
                env=os.environ.copy(),       # passthrough CUDA_VISIBLE_DEVICES etc.
                start_new_session=True,       # own process group for clean kill
            )
            proc.wait(timeout=timeout)
            return proc.returncode
        except subprocess.TimeoutExpired:
            log.warning("Job %s timed out after %ds — killing", job_path.name, timeout)
            _kill_tree(proc.pid)
            proc.wait()
            return -1
        except Exception:
            log.exception("Unexpected error running %s", job_path.name)
            if proc.poll() is None:
                _kill_tree(proc.pid)
                proc.wait()
            return -1


# ---------------------------------------------------------------------------
# 5. Cleanup — move to completed/ or failed/
# ---------------------------------------------------------------------------

def finalise(job_path: Path, exit_code: int, dirs: dict[str, Path]) -> None:
    dest_dir = dirs["completed"] if exit_code == 0 else dirs["failed"]
    dest = dest_dir / job_path.name
    try:
        os.rename(job_path, dest)
        log.info("Moved %s → %s/", job_path.name, dest_dir.name)
    except OSError:
        log.error("Failed to move %s to %s", job_path, dest)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def watch(poll_interval: int, timeout: int) -> None:
    hostname = socket.gethostname()
    dirs = ensure_queue_dirs()

    log.info(
        "Watcher started on %s — polling every %ds, timeout %ds",
        hostname, poll_interval, timeout,
    )

    while True:
        pending = sorted(dirs["pending"].iterdir())
        for job_file in pending:
            if not job_file.is_file():
                continue

            claimed = try_claim(job_file, dirs["running"], hostname)
            if claimed is None:
                continue

            log.info("Claimed %s → %s", job_file.name, claimed.name)
            rc = run_job(claimed, dirs["logs"], hostname, timeout)
            log.info("Job %s finished with rc=%s", claimed.name, rc)
            finalise(claimed, rc, dirs)

        time.sleep(poll_interval)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="DFS job-queue watcher daemon",
    )
    p.add_argument(
        "--poll-interval", type=int, default=15,
        help="Seconds between pending/ scans (default: 15)",
    )
    p.add_argument(
        "--timeout", type=int, default=4 * 3600,
        help="Per-job timeout in seconds (default: 14400 = 4 hours)",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    bootstrap_agents_config()
    watch(poll_interval=args.poll_interval, timeout=args.timeout)
