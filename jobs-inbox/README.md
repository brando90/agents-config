# jobs-inbox — phone-dispatch queue

Drop `.sh` files in [`pending/`](pending/) from **any context that can reach this git repo** (including claude.ai mobile, Anthropic cloud sandboxes, or a web editor). A poller running on a SNAP cluster node will:

1. `git pull` this repo every ~30 s.
2. Move each `pending/*.sh` into `~/dfs/job_queue/pending/` on the cluster (the DFS watcher queue).
3. Move the source file to [`dispatched/`](dispatched/) and commit+push.
4. The DFS watcher daemon (smart mode) then wraps the job in a coding agent that diagnoses failures, retries up to 3×, and emails PASS/FAIL.

End-to-end: commit from phone → running on cluster within ~30 s → email on completion.

---

## Writing a job file

Plain bash, standard SNAP env. The poller adds a timestamp prefix but otherwise does not modify your script.

```bash
#!/usr/bin/env bash
# JOB_MODE: smart
# Brief description of what this job does.
set -euo pipefail

export ANTHROPIC_API_KEY=$(cat ~/keys/anthropic_bm_key_koyejolab.txt | tr -d '[:space:]')
cd ~/veribench
bash run_some_experiment.sh
```

Commit path: `jobs-inbox/pending/<descriptive-name>.sh`

---

## Submitting from claude.ai on your phone

Paste this into a claude.ai session (mobile or web) in an Anthropic cloud env with `gh` available:

```
Clone my agents-config repo, add a job file to jobs-inbox/pending/<NAME>.sh that does X, commit and push. The cluster poller will pick it up within 30 seconds and email me when it finishes.

Repo: https://github.com/brando90/agents-config
```

Claude will write the script, commit, push. Cluster poller takes it from there.

---

## Checking that the poller is alive

From any SNAP node:

```bash
cat ~/dfs/job_queue/git_inbox_heartbeat.json | jq .
ls  ~/dfs/job_queue/pending/        # should show your job within ~30s
ls  ~/dfs/job_queue/completed/      # your job ends up here on success
ls  ~/dfs/job_queue/failed/         # …or here on failure
```

If `last_heartbeat` in the JSON is older than ~3× the interval, restart the poller — see [`../workflows/remote-job-dispatch.md`](../workflows/remote-job-dispatch.md) § Phone dispatch (git-inbox).

---

## Security

Anyone with push access to this repo can execute arbitrary code on the cluster as the running user. Current model: repo is private, sole write access = Brando. **Do not fork or open push access without moving this inbox to a dedicated private repo first.**
