# Remote Job Dispatch — SSH, DFS watcher, and phone dispatch

**TLDR:** Dispatch jobs to a remote Stanford Network Analysis Project (SNAP)
node through Secure Shell (SSH), the distributed file system (DFS) watcher,
or the phone's Git inbox. Use direct mode and put any agent command, explicit
model settings, and completion protocol inside the job; the legacy smart-mode
wrappers have stale defaults and have not been repaired by this documentation.

Before choosing a transport, complete [reliable agent dispatch](reliable-agent-dispatch.md) under Trigger Rule 48: explicit phase-appropriate models and effort, shared usage/finishing budget, verified remote runbook/checkpoint delivery, and a tested remote recovery/watch plan. The transports below launch commands; they do not supply cross-provider recovery on their own. A regular worker can execute a strong master's concrete plan, while acceptance and measured-model pins remain fixed.

The optional legacy wrapper is described in
[`smart-job-agent-prompt.md`](smart-job-agent-prompt.md). Until its launchers
are updated, bypass it with `--direct`, `--mode direct`, or a
`# JOB_MODE: direct` header as shown below. `ssh-submit.sh` has no model flag.
Run Trigger Rule 38's health check before dispatch, use an isolated worktree
for edits, and include the checkpoint, results, watch, and landing instructions
from Trigger Rules 37, 42, 44, and 46 in the job's runbook. Agent workers use
`~/agents-config/scripts/snap_dispatch.sh` or `ssh-submit.sh --direct` for their
own named terminal session. The watcher examples below run ordinary shell jobs;
an agent job submitted through a watcher must itself create its own named session
and wait for its recorded completion, so the queue tracks the actual job lifetime.

---

## TL;DR — pick a path

| Starting context | Recommended path | One-liner |
|:---|:---|:---|
| Live on a SNAP node, want to run on another SNAP node | **SSH fire-and-forget** | `~/agents-config/scripts/ssh-submit.sh --node skampere2 --job /tmp/eval.sh --direct` |
| Anywhere on the cluster, headless/batch/queued | **DFS watcher daemon** | `cp my_job.sh ~/dfs/job_queue/pending/` after adding `# JOB_MODE: direct` |
| Phone, claude.ai web, Anthropic cloud sandbox (no SSH) | **Phone dispatch (git-inbox)** | commit `jobs-inbox/pending/<name>.sh` with `# JOB_MODE: direct` to `agents-config` repo |
| Sitting on the Mac, want ONE long command (a driver, a sweep) detached on a SNAP node with no agent wrapper | **Direct SNAP launcher** (`scripts/snap_dispatch.sh`) | `SNAP_HOST=skampere1 ~/agents-config/scripts/snap_dispatch.sh run vb-gold-repair 'cd /lfs/... && bash driver.sh'` (then `tail` / `attach` / `kill`) |
| Sitting on the Mac, want a worker in its own byobu session you can attach to or drive from the phone | **Local deploy** (`scripts/deploy_cc.sh`) | `~/agents-config/scripts/deploy_cc.sh --name vb-fix --cwd ~/veribench --prompt-file <runbook.md>` (pass the master-selected `--model` and `--effort`; existing fallback defaults are `cc` profile, `claude-fable-5-1`, effort `max`, Remote Control on; `--profile codex` for a Codex worker; `byobu attach -t vb-fix`; Trigger Rule 42) |

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
| Agent wrapping | bypass legacy wrapper with `--direct` | bypass with `# JOB_MODE: direct` | preserve the same direct-mode header |
| Emails | job handles its authorized completion notice | job handles its authorized completion notice | job handles its authorized completion notice |
| Audit trail | tmux history + log file | `completed/` + `failed/` dirs on DFS | git history + DFS dirs |
| Best for | "Launch this now on that node, I'll watch" | "Queue many jobs, let them drain" | "I'm on my phone and want to dispatch" |
| Main limitation | you must choose a node up front | requires daemon to be alive | requires poller + private git repo |

**Default:** SSH fire-and-forget when live on the cluster. Watcher and phone dispatch are specializations of the same "drop file → agent runs it" pattern, for cases where SSH isn't available or you don't want to pick a node.

---

## 1. SSH fire-and-forget

Fast path for "I'm on node A, I want this running on node B within seconds."

### Submit

```bash
~/agents-config/scripts/ssh-submit.sh --node skampere2 --job ~/path/to/job.sh --direct
# Explicit direct mode avoids the launcher's legacy smart-mode default.
```

The launcher:
1. `scp`s the job into `~/dfs/ssh_job_queue/<timestamp>__<name>/` on the target.
2. Starts a detached tmux session running `bash <job>` with a log in that staging directory.
3. Returns the actual session name `<prefix>_<job>_<timestamp>` and log path;
   use that returned name when attaching. Launch success alone does not prove
   the job or agent is healthy: watch its process, log, and exit status.
4. In direct mode the job itself handles retries and any authorized completion
   notice; launcher notification flags do not add them. Remote-agent landings
   follow Trigger Rule 46's standing email instruction.

For a review worker, put an explicit command such as
`codex exec --dangerously-bypass-approvals-and-sandbox -m gpt-6-astra -c 'model_reasoning_effort="ultra"' "$JOB_PROMPT"`
in the job. An experiment workload instead uses its declared regular model,
for example `claude --dangerously-skip-permissions --model claude-sonnet-5 -p "$JOB_PROMPT"`.
Set `JOB_PROMPT` from the validated runbook first. For remote Claude workers,
follow Trigger Rule 46's authentication and private-binary instructions;
never load provider billing keys. Record the actual model in the results.

### Options

```bash
--node HOST          target SNAP node (required)
--job  PATH          local path to .sh (required)
--name STR           override job name (default: basename without .sh)
--smart|--direct     wrap in agent (default) | plain bash (no retries, no email)
--tmux-prefix STR    tmux session prefix (default: ssh_job)
--notify-email ADDR  override primary recipient; use brando.science@gmail.com for tracked internal notifications
--notify-cc ADDR     explicit CC only; omit for internal notifications unless Brando named extra recipients
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
bash ~/ultimate-utils/py_src/uutils/job_scheduler_uu/start_watcher.sh --default-mode direct
bash ~/ultimate-utils/py_src/uutils/job_scheduler_uu/start_watcher.sh --max-concurrent 4 --default-mode direct

# direct (no tmux):
export PYTHONPATH=~/ultimate-utils/py_src
python -m uutils.job_scheduler_uu.scheduler --poll 15 --max-concurrent 4 --default-mode direct
```

Attach / kill: `tmux attach -t job_watcher` / `tmux kill-session -t job_watcher`

The daemon logs start, stop (Ctrl-C), and crash events. Email `brando.science@gmail.com` only when the watcher/job was explicitly configured as a tracked task.

### Submit a job

```bash
export PYTHONPATH=~/ultimate-utils/py_src

# Explicitly bypass the legacy agent wrapper:
python -m uutils.job_scheduler_uu.submit my_train.sh --mode direct

# inline:
python -m uutils.job_scheduler_uu.submit --mode direct --inline "echo hello && nvidia-smi"

# or drop in a script whose first 20 lines contain # JOB_MODE: direct:
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
# JOB_MODE: direct
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

- **Legacy default remains smart.** The scheduler code still wraps jobs unless overridden. Set `--default-mode direct` and the per-job direct header; direct jobs own retries and any authorized completion notice.
- **Legacy agent selection is stale.** It prefers `clauded`, then Codex, then `claude`; the Codex fallback still uses the removed `--full-auto` flag and model settings are not pinned. Bypass this path until the scheduler code is fixed; use explicit agent commands inside direct jobs.
- **Daemon lifecycle logs** on start, stop, crash; email only when explicitly configured for a tracked job.
- **GPU-idle kill:** default 4 h of ≤1 % GPU util → kill. `--gpu-idle-timeout` seconds (0 = disable), `--gpu-idle-threshold` (default 1.0).
- **Wall-clock safety net:** default 48 h hard timeout. `--timeout`.
- **Environment inheritance.** Direct jobs inherit the host environment. Set `CUDA_VISIBLE_DEVICES` for any Python workload and use authenticated agent commands under Hard Rule 9; do not add provider-key exports.
- **Job types:** `.sh` / `.bash` run with bash; `.py` runs with the current Python.
- **FIFO ordering** by mtime (oldest first).
- **Submit-tool deduplication:** `O_CREAT | O_EXCL` prevents concurrent overwrite.
- **Triple-underscore separator** between job name and hostname in claimed filenames (`job.sh___<hostname>`).
- **Parallel jobs on one node:** `--max-concurrent N` (default 1). Each job is a real OS process.

For agent workers with no graphics-processing-unit work, disable the legacy low-GPU-utilization kill rule using the documented zero-disable setting above and use the task's progress/deadline watchdog instead. An idle accelerator does not mean an idle coding agent.

### Code vs docs

- **Code:** `~/ultimate-utils/py_src/uutils/job_scheduler_uu/` — scheduler, submitter, tmux launcher.
- **Docs:** this file. Keep both in sync after changes.

---

## 3. Phone dispatch (git-inbox)

For contexts that cannot SSH into the cluster and cannot write to DFS: Anthropic cloud sandboxes (claude.ai web/mobile, Codex cloud env), a web-only browser session, a second laptop without Kerberos.

The bridge is a git-tracked inbox in `agents-config/jobs-inbox/`. A poller on a SNAP node pulls the repo every ~30 s, moves any `pending/*.sh` into the DFS watcher queue, and commits the move back. Include `# JOB_MODE: direct` in every submitted script to bypass the legacy agent wrapper.

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

> "Clone my agents-config repo into a private checkout, add a job file to `jobs-inbox/pending/<name>.sh` that does X with `# JOB_MODE: direct`, commit and push. Include explicit model settings and the applicable checkpoint, results, watch, and remote-worker landing instructions. Email follows Trigger Rules 14/26/46. Repo: https://github.com/brando90/agents-config. TL;DR: Submit the isolated, direct-mode job with its completion protocol and report the commit."

Claude writes the script, commits, pushes. Poller fetches, dispatches. Watcher runs. You inspect status from the queue/logs; explicitly tracked jobs may send one final PASS/FAIL email.

### Writing an inbox job

```bash
#!/usr/bin/env bash
# JOB_MODE: direct
# Descriptive comment.
set -euo pipefail

cd /absolute/path/to/worker-owned-checkout
# Route large language model work through authenticated command-line interfaces
# with explicit models per INDEX_RULES.md Hard Rules 8/9.
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

**Why reuse the smart-mode prompt across all three?** Agent retry/diagnose behavior is useful in every path. Duplicating the prompt would mean fixing every bug three times. See [`smart-job-agent-prompt.md`](smart-job-agent-prompt.md) for the single source of truth.

**Why explicitly select direct mode now?** The legacy smart wrappers have stale command flags and model defaults. Direct mode preserves the transport and logs while the job supplies current agent commands, its watch, and its authorized completion protocol.

**Why `~/dfs/ssh_job_queue/` instead of reusing `~/dfs/job_queue/` for SSH?** Keeps SSH-launched jobs out of the watcher's queue dirs (avoiding accidental double-pickup by the watcher). SSH jobs are already running — putting them in `pending/` would be wrong; putting them in `running/` would confuse the watcher's filename convention.

## Keep the editor checkout current

The dispatcher owns one periodic local catch-up schedule under [Trigger Rule 46](../INDEX_RULES.md), normally every 30 minutes, plus an initial verified check. Record the actual schedule identifier, target checkout, last successful run and before/after commits in the master checkpoint. Remote workers still finish and publish independently while the laptop sleeps. Bound the total check duration, individual operations, lock acquisition and retries; prevent overlapping invocations before writing state. Apply ownership checks to reused isolated checkouts too. fetch and verify their main landings, pin the fetched main commit, then use `git merge --ff-only --no-autostash --no-overwrite-ignore <checked-commit>` in the user-designated editor checkout only when exclusive write ownership is held for the entire check/update/verification window (coordinate active owners; a lock works only if all writers respect it), it is on main without tracked/staged changes or unpublished commits, and incoming files cannot overwrite untracked or ignored work. Otherwise update an owned isolated checkout and state plainly that the editor checkout remains stale; never hide that condition behind a successful fetch or mirror update. Do not create a pull request merely to download an already-merged change. Verify old untracked experiment-name leftovers before preserving them outside the active list. Keep unchanged checks quiet and stop after every job is verified complete or explicitly canceled, required publications are confirmed, and local catch-up finishes, preserving unrelated paused schedules.
