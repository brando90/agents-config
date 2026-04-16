# Workflow: DFS Job Queue Watcher

How to submit and run jobs on SNAP nodes that share a DFS but lack Slurm.

---

## What It Is

A decentralized, file-based job scheduler using a spool-directory pattern. Multiple watcher daemons on different nodes poll a shared `pending/` directory, atomically claim jobs via NFS-safe hardlinks, execute them, and route results to `completed/` or `failed/`. No central coordinator needed.

By default, jobs run in **smart mode**: the watcher wraps execution in a coding agent (clauded/codex/claude) that diagnoses failures, makes up to 3 attempts total, and emails results to `brando.science@gmail.com`. Use **direct mode** for plain subprocess execution (legacy behavior).

**Code lives in:** `~/ultimate-utils/py_src/uutils/job_scheduler_uu/`

---

## Prerequisite: `~/dfs` symlink

Every path in this doc uses `~/dfs/job_queue/...`. That requires `~/dfs → /dfs/scratch0/<user>` to exist on every SNAP node running (or submitting to) the watcher. Without it, the most dangerous case is that `~/dfs` is a plain local directory: `cp my_train.sh ~/dfs/job_queue/pending/` then succeeds locally on LFS but is invisible to the shared queue, so the job is never claimed and never appears anywhere a peer node looks. (See § "Is any job of mine running?" below for the diagnostic.)

```bash
# Create once per node (snap_setup.sh does this automatically on new nodes):
ln -sfn /dfs/scratch0/$(whoami) ~/dfs
ls -la ~/dfs           # should show -> /dfs/scratch0/<user>
ls    ~/dfs/job_queue/ # should show pending/ running/ completed/ failed/ logs/
```

If `~/dfs/job_queue/watchers/` does not exist, no watcher has ever run on this queue. The watcher creates that dir and writes a heartbeat into it on startup — its absence is the single-source check for "is anything running cluster-wide?"

---

## Quick Reference

### Start the watcher daemon

You can start the watcher from any shell — SSH, tmux, or from within a Claude/Codex session. Just tell your agent: _"start the job watcher daemon on this node"_ and it will run the command below.

```bash
# Option A: tmux launcher (recommended)
bash ~/ultimate-utils/py_src/uutils/job_scheduler_uu/start_watcher.sh

# Run up to 4 smart jobs in parallel:
bash ~/ultimate-utils/py_src/uutils/job_scheduler_uu/start_watcher.sh --max-concurrent 4

# Force direct mode (no agent wrapping):
bash ~/ultimate-utils/py_src/uutils/job_scheduler_uu/start_watcher.sh --default-mode direct

# Option B: direct (no tmux)
export PYTHONPATH=~/ultimate-utils/py_src
python -m uutils.job_scheduler_uu.scheduler --poll 15 --max-concurrent 4
```

Attach/kill: `tmux attach -t job_watcher` / `tmux kill-session -t job_watcher`

The daemon emails `brando.science@gmail.com` on start, stop (Ctrl-C), and crash.

### Submit a job

```bash
export PYTHONPATH=~/ultimate-utils/py_src

# Smart mode (default — agent wraps, diagnoses failures, emails results):
python -m uutils.job_scheduler_uu.submit my_train.sh

# Explicitly set mode per-job:
python -m uutils.job_scheduler_uu.submit my_train.sh --mode smart
python -m uutils.job_scheduler_uu.submit my_train.sh --mode direct

# Inline command:
python -m uutils.job_scheduler_uu.submit --inline "echo hello && nvidia-smi"

# Or just copy directly (uses watcher's --default-mode):
cp my_train.sh ~/dfs/job_queue/pending/
```

Agents can also submit jobs from within a session — just run the submit command above.

### Check status

```bash
ls ~/dfs/job_queue/pending/     # queued
ls ~/dfs/job_queue/running/     # in progress
ls ~/dfs/job_queue/completed/   # exit 0
ls ~/dfs/job_queue/failed/      # exit != 0 or timeout
cat ~/dfs/job_queue/logs/<job>___<hostname>.log  # stdout+stderr
```

### "Is any job of mine running?" — always check BOTH layers

The watcher queue is only one way jobs get launched. A fire-and-forget `tmux new-session -d`, `nohup`, `disown`, or an inline script started from a terminal will never touch `~/dfs/job_queue/`. So when the user asks "is my job running" / "check watcher jobs" / "any job", inspect both:

1. **Queue layer** — the commands above (`pending/`, `running/`, etc.) plus the watcher heartbeats (next section).
2. **Detached-process layer** — on every node the job could be on:
   ```bash
   tmux ls                                              # every session, not just job_watcher
   ps -u "$USER" -o pid,etime,%cpu,cmd --sort=-etime    # long-running procs
   nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
   for s in $(tmux ls -F '#S' 2>/dev/null); do tmux capture-pane -t "$s" -p | tail -5; done
   ```
   If the job could be on a peer node (user said "I submitted from skampere1"), SSH to that peer and repeat. A submission on a node missing the `~/dfs` symlink silently lands in that node's LOCAL `~/dfs/job_queue/` and is invisible from the shared DFS — always check the local path on the source node as part of layer 2.

Reporting only one layer is a known failure mode — silence on the other layer looks identical to "no job running."

### Check which watchers are alive (across nodes)

Each running watcher rewrites `~/dfs/job_queue/watchers/<hostname>.heartbeat`
(JSON) every poll cycle. From any node that shares the DFS:

```bash
ls -lt ~/dfs/job_queue/watchers/
cat  ~/dfs/job_queue/watchers/*.heartbeat | jq .
```

If a heartbeat's `last_heartbeat` is older than ~3× `poll_interval_s`, the
watcher is almost certainly dead — SSH to that host and restart it. On a
clean Ctrl-C the file is rewritten with `"state": "STOPPED"`; on an
uncaught exception, `"state": "CRASHED"` (plus the crash email).
SIGKILL / power loss leaves the file frozen as `RUNNING` — rely on mtime
in that case.

---

## Smart Mode vs Direct Mode

### Smart mode (default)

The watcher launches a coding agent (priority: clauded > codex --full-auto > claude --dangerously-skip-permissions) with a prompt that:
1. Executes the job script
2. If the script fails, reads the error, diagnoses, and retries (up to 3 attempts)
3. Emails `brando.science@gmail.com` (CC `brando9@stanford.edu`) with PASS/FAIL results
4. All with full-auto / no permission prompts — it's a daemon, no human in the loop

If no agent binary is found on the node, smart mode falls back to direct mode with a warning.

### Direct mode

The script runs as a plain `bash` / `python` subprocess (legacy behavior). No agent wrapping, no failure diagnosis, no automatic email.

### Per-job mode header

Each job script can override the watcher's default mode with a header comment in the first 20 lines:

```bash
#!/bin/bash
# JOB_MODE: smart
# (or: # JOB_MODE: direct)
export CUDA_VISIBLE_DEVICES=0
python train.py
```

If no header is present, the watcher's `--default-mode` applies (default: smart).

The `submit` tool can inject this header at submission time via `--mode smart|direct`.

---

## Directory Layout

```
~/dfs/job_queue/
    pending/      drop .sh or .py job files here
    running/      jobs claimed by a node (filename___<hostname>)
    completed/    exit-code 0
    failed/       timed-out or non-zero exit
    logs/         per-job stdout+stderr logs
    watchers/     per-host <hostname>.heartbeat JSON (liveness signal)
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

- **Smart mode by default:** Jobs are wrapped in a coding agent that diagnoses failures, retries, and emails results. Override with `--default-mode direct` or per-job `# JOB_MODE: direct`.
- **Agent priority:** `clauded -p` > `codex exec --full-auto` > `claude -p --dangerously-skip-permissions`. All bypass permission prompts since this is a daemon.
- **Daemon lifecycle emails:** The watcher emails `brando.science@gmail.com` on start, stop (Ctrl-C), and crash (unhandled exception).
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
