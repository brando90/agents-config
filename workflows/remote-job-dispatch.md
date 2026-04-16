# Remote Job Dispatch — SSH, DFS watcher, and phone dispatch

Three ways to run a job on a SNAP cluster node that isn't the one you're sitting on. All three share the same **smart-mode agent wrapper** from [`smart-job-agent-prompt.md`](smart-job-agent-prompt.md): diagnose failures → retry up to 3× → email STARTING + PASS/FAIL. Pick the path that matches your starting context.

---

## TL;DR — pick a path

| Starting context | Recommended path | One-liner |
|:---|:---|:---|
| Live on a SNAP node, want to run on another SNAP node | **SSH fire-and-forget** | `~/agents-config/scripts/ssh-submit.sh --node skampere2 --job /tmp/eval.sh` |
| Anywhere on the cluster, headless/batch/queued | **DFS watcher daemon** | `cp my_job.sh ~/dfs/job_queue/pending/` |
| Phone, claude.ai web, Anthropic cloud sandbox (no SSH) | **Phone dispatch (git-inbox)** | commit `jobs-inbox/pending/<name>.sh` to `agents-config` repo |

---

## Comparison

| Property | SSH fire-and-forget | DFS watcher | Phone dispatch (git-inbox) |
|:---|:---|:---|:---|
| Prerequisite on submitter side | Kerberos ticket or SSH key | write access to `~/dfs/job_queue/pending/` | write access to `brando90/agents-config` git repo |
| Prerequisite on cluster side | target node reachable via `ssh`, `tmux` installed | daemon running (heartbeat in `~/dfs/job_queue/watchers/`) | daemon **and** git-inbox poller running on at least one node |
| Survives submitter dying? | Yes (detached tmux) | Yes (file on DFS) | Yes (commit on GitHub) |
| Cluster-wide pickup? | No — you pick the node | **Yes** — any watcher can claim | Yes (routed through the watcher) |
| Visibility during run | `ssh <node> "tmux attach -t <session>"` | `tail -f ~/dfs/job_queue/logs/<job>.log` | same as watcher (it's the second stage) |
| Latency from submit → running | seconds | seconds (watcher poll = 15 s) | ~30 s (git pull interval) + watcher poll |
| Smart-mode agent wrapping | yes, same prompt | yes | yes |
| Emails (start + end) | yes | yes (via agent) | yes |
| Audit trail | tmux history + log file | `completed/` + `failed/` dirs on DFS | git history + DFS dirs |
| Best for | "Launch this now on that node, I'll watch" | "Queue many jobs, let them drain" | "I'm on my phone and want to dispatch" |
| Main limitation | you must choose a node up front | requires daemon to be alive | requires poller + private git repo |

**Default:** SSH fire-and-forget when live on the cluster. Watcher and phone dispatch are specializations of the same "drop file → agent runs it" pattern, for cases where SSH isn't available or you don't want to pick a node.

---

## 1. SSH fire-and-forget

Fast path for "I'm on node A, I want this running on node B within seconds."

### Submit

```bash
~/agents-config/scripts/ssh-submit.sh --node skampere2 --job ~/path/to/job.sh
# defaults: smart mode, tmux session prefix ssh_job_, email brando.science@gmail.com
```

The launcher:
1. `scp`s the job into `~/dfs/ssh_job_queue/<timestamp>__<name>/` on the target.
2. Reads [`smart-job-agent-prompt.md`](smart-job-agent-prompt.md), substitutes placeholders.
3. `ssh <node> "tmux new -d -s <session> 'clauded -p <prompt>'"`.
4. Returns immediately. You get a STARTING email within ~1 min, PASS/FAIL at end.

### Options

```bash
--node HOST          target SNAP node (required)
--job  PATH          local path to .sh (required)
--name STR           override job name (default: basename without .sh)
--smart|--direct     wrap in agent (default) | plain bash (no retries, no email)
--tmux-prefix STR    tmux session prefix (default: ssh_job)
--notify-email ADDR  override primary recipient
--notify-cc ADDR     override CC
```

### Watch live

```bash
ssh skampere2 "tmux ls | grep ^ssh_job_"        # list active jobs
ssh skampere2 "tmux attach -t ssh_job_<name>_<stamp>"   # live view
```

### Gotchas

- **Kerberos expires.** `klist` should show a valid ticket. If `ssh <node>` prompts for a password, `kinit` and retry. See [`../init_no_passwords_snap_kinit.md`](../init_no_passwords_snap_kinit.md).
- **Target node must have an agent binary** (`clauded`/`codex`/`claude`) on `PATH` for smart mode; otherwise the remote script falls back to direct mode with a warning.
- **The job's working directory is `~/dfs/ssh_job_queue/<stamp>__<name>/`** when the agent executes it. If your script `cd`s elsewhere (e.g. `cd ~/harbor_jobs`), that's fine.

---

## 2. DFS watcher daemon

Queue-based dispatch for batch / headless / unknown-node scenarios. The daemon polls `~/dfs/job_queue/pending/` and claims jobs atomically across nodes.

### Start the daemon (once per node you want as a worker)

```bash
# tmux launcher (recommended):
bash ~/ultimate-utils/py_src/uutils/job_scheduler_uu/start_watcher.sh
bash ~/ultimate-utils/py_src/uutils/job_scheduler_uu/start_watcher.sh --max-concurrent 4

# direct (no tmux):
export PYTHONPATH=~/ultimate-utils/py_src
python -m uutils.job_scheduler_uu.scheduler --poll 15 --max-concurrent 4
```

Attach / kill: `tmux attach -t job_watcher` / `tmux kill-session -t job_watcher`

The daemon emails `brando.science@gmail.com` on start, stop (Ctrl-C), and crash.

### Submit a job

```bash
export PYTHONPATH=~/ultimate-utils/py_src

# smart mode (default):
python -m uutils.job_scheduler_uu.submit my_train.sh

# explicitly:
python -m uutils.job_scheduler_uu.submit my_train.sh --mode smart
python -m uutils.job_scheduler_uu.submit my_train.sh --mode direct

# inline:
python -m uutils.job_scheduler_uu.submit --inline "echo hello && nvidia-smi"

# or just drop it in:
cp my_train.sh ~/dfs/job_queue/pending/
```

### Status

```bash
ls ~/dfs/job_queue/pending/     # queued
ls ~/dfs/job_queue/running/     # in progress
ls ~/dfs/job_queue/completed/   # exit 0
ls ~/dfs/job_queue/failed/      # exit != 0 or timeout
cat ~/dfs/job_queue/logs/<job>___<hostname>.log
```

### Watchers alive across nodes

```bash
ls  -lt ~/dfs/job_queue/watchers/
cat ~/dfs/job_queue/watchers/*.heartbeat | jq .
```

If `last_heartbeat` is older than ~3× `poll_interval_s`, the watcher is almost certainly dead — SSH to that host and restart it.

### Per-job mode header

Override the watcher's default mode inline in the script's first 20 lines:

```bash
#!/bin/bash
# JOB_MODE: smart
# (or: # JOB_MODE: direct)
```

### Directory layout

```
~/dfs/job_queue/
    pending/    drop .sh or .py job files here
    running/    jobs claimed by a node (filename___<hostname>)
    completed/  exit 0
    failed/     non-zero exit or timeout
    logs/       per-job stdout+stderr
    watchers/   per-host heartbeats
```

### Atomic claim protocol (NFS-safe)

The watcher uses `os.link()` not `os.rename()`. `rename()` is *not* reliably atomic across NFS clients.

1. `os.link(pending/job.sh, running/job.sh___<host>)` — atomic on NFS v3+.
2. Check `os.stat(pending/job.sh).st_nlink == 2` — won the race if so.
3. `os.unlink(pending/job.sh)` — remove from pending.

### Key details

- **Smart mode default.** Agent wraps, retries, emails. Override via `--default-mode direct` or per-job header.
- **Agent priority:** `clauded -p` > `codex exec --full-auto` > `claude -p --dangerously-skip-permissions`. All bypass permission prompts — it's a daemon.
- **Daemon lifecycle emails** on start, stop, crash.
- **GPU-idle kill:** default 4 h of ≤1 % GPU util → kill. `--gpu-idle-timeout` seconds (0 = disable), `--gpu-idle-threshold` (default 1.0).
- **Wall-clock safety net:** default 48 h hard timeout. `--timeout`.
- **Env inheritance.** Subprocess inherits the host env (`CUDA_VISIBLE_DEVICES`, API keys, etc.).
- **Job types:** `.sh` / `.bash` run with bash; `.py` runs with the current Python.
- **FIFO ordering** by mtime (oldest first).
- **Submit-tool deduplication:** `O_CREAT | O_EXCL` prevents concurrent overwrite.
- **Triple-underscore separator** between job name and hostname in claimed filenames (`job.sh___<hostname>`).
- **Parallel jobs on one node:** `--max-concurrent N` (default 1). Each job is a real OS process.

### Code vs docs

- **Code:** `~/ultimate-utils/py_src/uutils/job_scheduler_uu/` — scheduler, submitter, tmux launcher.
- **Docs:** this file. Keep both in sync after changes.

---

## 3. Phone dispatch (git-inbox)

For contexts that cannot SSH into the cluster and cannot write to DFS: Anthropic cloud sandboxes (claude.ai web/mobile, Codex cloud env), a web-only browser session, a second laptop without Kerberos.

The bridge is a git-tracked inbox in `agents-config/jobs-inbox/`. A poller on a SNAP node pulls the repo every ~30 s, moves any `pending/*.sh` into the DFS watcher queue, and commits the move back. Jobs end up in the same smart-mode agent wrapper as the other two paths.

### Prerequisite: poller must be running on one cluster node

```bash
tmux new -d -s git_inbox_poller "bash ~/agents-config/scripts/git-inbox-poller.sh"
tmux attach -t git_inbox_poller     # to verify
```

Defaults: poll every 30 s, pull from `~/agents-config`, push to `~/dfs/job_queue/pending/`.

**Only one poller per user.** Running two pollers would cause race conditions on the git commit. Pick one long-lived node (typically `skampere1`).

Check liveness from any node:

```bash
cat ~/dfs/job_queue/git_inbox_heartbeat.json | jq .
```

If `last_heartbeat` is more than ~3× the poll interval old, restart it.

### Submitting from a phone / cloud sandbox

Open claude.ai (mobile or web) in a context where `gh` works (most Anthropic cloud envs have it). Tell Claude:

> "Clone my agents-config repo, add a job file to `jobs-inbox/pending/<name>.sh` that does X, commit and push. Cluster poller will pick it up within 30 s and email me when it finishes. Repo: https://github.com/brando90/agents-config"

Claude writes the script, commits, pushes. Poller fetches, dispatches. Watcher runs. You get STARTING + PASS/FAIL emails — same as the other two paths.

### Writing an inbox job

```bash
#!/usr/bin/env bash
# JOB_MODE: smart
# Descriptive comment.
set -euo pipefail

# Load keys exactly as you would on the cluster:
export ANTHROPIC_API_KEY=$(cat ~/keys/anthropic_bm_key_koyejolab.txt | tr -d '[:space:]')
cd ~/veribench
bash my_experiment.sh
```

File path in the repo: `jobs-inbox/pending/<descriptive-name>.sh`.

The poller moves it to `jobs-inbox/dispatched/<timestamp>__<name>.sh` after pickup, so the repo keeps a commit-log audit trail of every phone submission.

### Security

Anyone with push access to `brando90/agents-config` can execute arbitrary code on the cluster as Brando. Model: repo is private, sole write access = Brando.

**Do not** fork the repo publicly or give push access to collaborators without first moving `jobs-inbox/` into a dedicated private repo.

### Checking pipeline health from a phone

Have Claude run:

```bash
gh api repos/brando90/agents-config/commits?per_page=5 | jq '.[].commit.message'
```

Recent `inbox: dispatch ...` messages mean the poller is alive and dispatching.

---

## Prerequisite: `~/dfs` symlink (all three paths assume it)

Every path above uses `~/dfs/job_queue/...`. That requires `~/dfs` → `/dfs/scratch0/<user>` on every SNAP node. Without it, the watcher can't find the queue, and `cp my_job.sh ~/dfs/job_queue/pending/` silently writes into a local LFS directory that only the current node can see.

```bash
ln -sfn /dfs/scratch0/$(whoami) ~/dfs
ls -la ~/dfs                      # should show → /dfs/scratch0/<user>
ls    ~/dfs/job_queue/            # pending/ running/ completed/ failed/ logs/ watchers/
```

`snap_setup.sh` and [`../machine/snap-init.md`](../machine/snap-init.md) handle this on a fresh node.

If `~/dfs/job_queue/watchers/` does not exist, no watcher has ever run on this queue. Cluster-wide "is anything alive" check:

```bash
ls -lt ~/dfs/job_queue/watchers/
```

---

## Design notes

**Why three paths, not one?** Different submitter contexts have different primitives available. SSH needs Kerberos/keys. DFS write needs a logged-in session. Git push needs only HTTPS. The three paths cover the full range from "I'm at a terminal" to "I'm on my phone."

**Why reuse the smart-mode prompt across all three?** Agent retry/diagnose + email notification is useful in every path. Duplicating the prompt would mean fixing every bug three times. See [`smart-job-agent-prompt.md`](smart-job-agent-prompt.md) for the single source of truth.

**Why default to smart mode?** Jobs on a remote node are invisible otherwise. Silent failures + missing email = "where did my experiment go?" Smart mode + STARTING + PASS/FAIL email makes the remote dispatch feel like a local run that pings you.

**Why `~/dfs/ssh_job_queue/` instead of reusing `~/dfs/job_queue/` for SSH?** Keeps SSH-launched jobs out of the watcher's queue dirs (avoiding accidental double-pickup by the watcher). SSH jobs are already running — putting them in `pending/` would be wrong; putting them in `running/` would confuse the watcher's filename convention.
