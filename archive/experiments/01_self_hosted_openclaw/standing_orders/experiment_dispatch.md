# Standing Order — Click-Button Experiment Dispatch

**TLDR:** This is a deferred workflow design, not an installed `/experiment` command. Once implemented, an explicit Telegram request would create a worker-owned project checkout, read its experiment specification, run it in a named tmux session, and report results and the pull request (PR) link.

## Goal

Collapse "I want to run experiment X" → "ssh to mercury2, tmux new, git checkout, read prompt, paste into Claude Code, wait" into one Telegram command. Off-load running experiments from Brando's laptop to mercury2's compute.

## When this fires

- **Brando-initiated (Telegram)** — `/experiment <branch-name> [--host mercury2|mac-pro] [--model gpt-6-astra] [--runner claude|codex]`.

**Never** dispatched automatically. Each experiment requires Brando's explicit invocation.

## Inputs

1. **Branch name** — the experiment branch to check out (e.g. `claude/foo-bar-XYZ`).
2. **Host** — `mercury2` (default for compute-heavy) or `mac-pro` (default for local-only experiments).
3. **Spec path** — defaults to `<branch-root>/cc_prompt.md` or `<branch-root>/experiments/<NN>_<name>/cc_prompt.md`; configurable via `--spec`.
4. **Runner** — `claude` (Claude Code print mode) or `codex` (Codex command-line interface (CLI) exec); defaults to whatever the spec frontmatter declares.
5. **Model and effort** — honor the spec or Brando's explicit override. Otherwise use Hard Rule 8's regular experiment tier, such as `claude-sonnet-5` or `gpt-5.6-terra`; reserve `claude-fable-5-1` max / `gpt-6-astra` ultra for review or an explicitly requested flagship workload. Record the exact model and effort in results.
6. **Project repository** — resolve the branch against its actual project repository; do not assume the experiment lives in `~/agents-config`.

## Workflow

1. **Capture**: Brando sends the command.
2. **Validate**: branch exists on origin; spec file exists at expected path; host is reachable.
3. **Show**: preview — branch, target host, spec path, runner, model, estimated runtime if known.
4. **Approve (Brando)**: `post` to dispatch; `edit: --host mac-pro` to swap host; `cancel` to abort.
5. **Execute**:
   - Run Trigger Rule 38's cluster health check and prepare the authentication and
     private Claude binary required by Trigger Rule 46 before connecting to the target host.
   - Fetch the validated branch from the project repository and create an isolated worktree:
     `git -C <project-repo> fetch origin <branch>`, then
     `git -C <project-repo> worktree add -b <unique-worker-branch> <worker-dir> FETCH_HEAD`.
     Resolve `<worker-dir>` to a private absolute path on the target; never switch a shared checkout.
   - Open a new tmux session named `experiment-<branch-slug>-<dispatch-id>`;
     `<dispatch-id>` is a unique identifier for this invocation. Refuse an existing name.
   - Inside tmux, change to `<worker-dir>`, set `RUNBOOK` and `RUN_LOG` to the validated
     specification and a log path in the worker directory, create the requested output directory,
     and launch one runner. Example workload commands (replace model/effort if the spec requires it):
     - **Claude**: `claude --dangerously-skip-permissions --model claude-sonnet-5 -p "$(cat "$RUNBOOK")" > "$RUN_LOG" 2>&1`
     - **Codex CLI**: `codex exec --dangerously-bypass-approvals-and-sandbox -m gpt-5.6-terra -c 'model_reasoning_effort="medium"' "$(cat "$RUNBOOK")" > "$RUN_LOG" 2>&1`
     - Output locations belong in the specification; Claude has no `--output-dir` flag.
       Preserve the command's exit code in a completion record before the session exits.
       Follow Trigger Rule 46's remote authentication and private-binary instructions.
   - Maintain `results.md` and `CKPT_<task>.md` (the task's checkpoint) under Trigger Rules 37/44;
     include the remote-worker landing protocol and watch required by Trigger Rules 42/46.
   - Detach.
6. **Heartbeat**: every 15 min, post the actual unique session name, host, status, timestamp, and last log line to `openclaw-ops`.
7. **Completion**: read the recorded exit code; a disappearing tmux session alone does not prove success. Report `DONE` only for success, otherwise `FAILED` or `UNKNOWN`, and send Brando a direct message (DM) with branch, runtime, log tail, output directory, and PR link if one was created. Trigger Rule 46 also governs the authorized landing email.
8. **Log**: `~/openclaw/audit/experiments_dispatched.jsonl`.

## Outputs

- A running tmux session on the target host.
- Heartbeats in `openclaw-ops`.
- Final DM with results + log location + PR link.
- Audit log entry.

## Safety rules

- **Approval level:** `approve_to_dispatch` (a softer level than `never_autonomous` — running an experiment is not externally consequential).
- **Resource ceiling** — refuse if mercury2 is already running > 2 OpenClaw experiments concurrently (avoid swapping out other compute).
- **Spec sanity-check** — refuse if spec exceeds 50KB (likely wrong file); refuse if spec contains shell commands targeting `/dfs/scratch0/` outside the user's directory.
- **Branch sanity** — refuse `main` / `master` / branches not under `claude/*` or `experiments/*` namespace (avoid running experiments on the trunk).
- **mercury2 unavailability** — when mercury2 is unavailable, select another authorized healthy cluster node or report the dispatch blocked. Do not move a long experiment onto a Mac; Trigger Rule 42 keeps those jobs on the cluster.

## Open setup questions

1. **Runner default** — `claude -p` or `codex exec`? Brando uses both; spec frontmatter could declare per-experiment.
2. **Spec frontmatter schema** — define a YAML header for spec files: `model`, `runner`, `expected_runtime`, `output_dir`.
3. **PR detection** — how does the runner declare "I created PR #X"? Convention: write the PR URL to `~/openclaw/experiments/<branch-slug>/_pr_url.txt` at completion.
4. **Cross-host coordination** — if Brando dispatches the same branch twice in quick succession, refuse the second; or queue?

## Status

| Date | Status |
|------|--------|
| 2026-05-08 | Skeleton drafted. Setup questions pending. Implementation deferred until Phase 6.6 of [`MASTER_PLAN.md`](../MASTER_PLAN.md) (after mercury2 install). |
