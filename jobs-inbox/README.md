# jobs-inbox — phone-dispatch queue

Drop `.sh` files in [`pending/`](pending/) from **any context that can reach this git repo** (including claude.ai mobile, Anthropic cloud sandboxes, or a web editor). A poller running on a SNAP cluster node will:

1. `git pull` this repo every ~30 s.
2. Move each `pending/*.sh` into `~/dfs/job_queue/pending/` on the cluster (the DFS watcher queue).
3. Move the source file to [`dispatched/`](dispatched/) and commit+push.
4. The legacy DFS watcher smart mode wraps the job in a coding agent. New jobs use the [direct-dispatch procedure](../workflows/remote-job-dispatch.md), explicit model settings, and a verified watch/recovery plan; the job's coordinator handles important-event email under Rules 14, 26 and 70.

End-to-end: commit from phone → poller queues the job → verify actual execution through logs and queue state. Polling cadence is not a launch guarantee. Important-event email follows Rules 14, 26 and 70 and requires a verified receipt.

---

## Writing a job file

Plain bash, standard SNAP env. The poller adds a timestamp prefix but otherwise does not modify your script.

```bash
#!/usr/bin/env bash
# JOB_MODE: smart
# Brief description of what this job does.
set -euo pipefail

cd ~/veribench
# Route LLM work through local CLIs per ~/agents-config/INDEX_RULES.md Hard Rule 9.
bash run_some_experiment.sh
```

Commit path: `jobs-inbox/pending/<descriptive-name>.sh`

---

## Submitting from claude.ai on your phone

Paste this into a claude.ai session (mobile or web) in an Anthropic cloud env with `gh` available:

```
Clone my agents-config repo into an isolated checkout and add a job file to jobs-inbox/pending/<NAME>.sh that does X with # JOB_MODE: direct, explicit model settings, and the applicable checkpoint, results and watch instructions. Commit and push, then verify actual dispatch and execution. Email important events under Rules 14, 26 and 70: To brandojazz@gmail.com, BCC brando.science@gmail.com; CC brando@vals.ai only for Vals work.

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
