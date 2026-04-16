# Workflow: DFS Job Queue Watcher

How to submit and run jobs on SNAP nodes that share a DFS but lack Slurm.

---

## What It Is

A decentralized, file-based job scheduler using a spool-directory pattern. Multiple watcher daemons on different nodes poll a shared `pending/` directory, atomically claim jobs via NFS-safe hardlinks, execute them, and route results to `completed/` or `failed/`. No central coordinator needed.

**Code lives in:** `ultimate-utils/py_src/uutils/job_scheduler_uu/`

---

## Quick Reference

### Start the watcher daemon (on each node)

```bash
# Option A: tmux launcher (recommended)
bash ~/ultimate-utils/py_src/uutils/job_scheduler_uu/start_watcher.sh

# Run up to 4 jobs in parallel on this node:
bash ~/ultimate-utils/py_src/uutils/job_scheduler_uu/start_watcher.sh --max-concurrent 4

# Option B: direct
export PYTHONPATH=~/ultimate-utils/py_src
python -m uutils.job_scheduler_uu.scheduler --poll 15 --gpu-idle-timeout 14400 --max-concurrent 4
```

Attach/kill: `tmux attach -t job_watcher` / `tmux kill-session -t job_watcher`

### Submit a job

```bash
export PYTHONPATH=~/ultimate-utils/py_src

# From a script file
python -m uutils.job_scheduler_uu.submit my_train.sh

# Inline command
python -m uutils.job_scheduler_uu.submit --inline "echo hello && nvidia-smi"

# Or just copy directly
cp my_train.sh ~/dfs/job_queue/pending/
```

### Check status

```bash
ls ~/dfs/job_queue/pending/     # queued
ls ~/dfs/job_queue/running/     # in progress
ls ~/dfs/job_queue/completed/   # exit 0
ls ~/dfs/job_queue/failed/      # exit != 0 or timeout
cat ~/dfs/job_queue/logs/<job>___<hostname>.log  # stdout+stderr
```

---

## Directory Layout

```
~/dfs/job_queue/
    pending/      drop .sh or .py job files here
    running/      jobs claimed by a node (filename___<hostname>)
    completed/    exit-code 0
    failed/       timed-out or non-zero exit
    logs/         per-job stdout+stderr logs
```

---

## How Atomic Claims Work (NFS-safe)

The watcher uses `os.link()` (hardlink), not `os.rename()`, because rename is NOT reliably atomic across NFS clients.

1. `os.link(pending/job.sh, running/job.sh___<hostname>)` -- atomic on NFS v3+
2. Check `os.stat(pending/job.sh).st_nlink == 2` -- we won the race
3. `os.unlink(pending/job.sh)` -- remove from pending

If another node wins, either the link fails or the nlink count is > 2.

---

## Key Details

- **GPU-idle kill:** Default 4 hours of continuous GPU idleness (<=1% utilization) triggers a kill. Long-running GPU-active jobs are left alone indefinitely. Configurable via `--gpu-idle-timeout` (seconds, 0 to disable) and `--gpu-idle-threshold` (default 1.0%).
- **Wall-clock safety net:** Default 48 hours hard timeout kills unconditionally (for truly runaway jobs). Configurable via `--timeout`.
- **Environment:** The subprocess inherits the full host environment (`CUDA_VISIBLE_DEVICES`, API keys, etc.).
- **Job types:** `.sh` and `.bash` run with bash; `.py` runs with the current Python; `.json` not yet supported.
- **FIFO ordering:** Pending jobs are sorted by modification time (oldest first).
- **Deduplication:** The submit tool uses `O_CREAT | O_EXCL` to prevent two concurrent submitters from overwriting each other.
- **Triple-underscore separator:** Claimed filenames use `___` (not `_`) between the job name and hostname, avoiding ambiguity with underscores in filenames.
- **Parallel jobs on one node:** `--max-concurrent N` (default 1) lets one watcher run N jobs simultaneously. Each job is a real OS process (`subprocess.Popen`), so they get true parallelism — no GIL. The main loop polls child PIDs non-blockingly each cycle and launches new claims when under capacity.

---

## Where Things Live

- **Code (scheduler, submitter, tmux launcher):** `~/ultimate-utils/py_src/uutils/job_scheduler_uu/` — this is the Python implementation. Edit here for algorithm or CLI changes.
- **Docs (usage guide, protocol, operator commands):** `~/agents-config/workflows/dfs-job-watcher.md` (this file) — this is the human-readable reference. Update here when the interface changes.

Keep both in sync after changes.
