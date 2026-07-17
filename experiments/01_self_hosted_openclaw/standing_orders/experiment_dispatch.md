# Standing Order — Click-Button Experiment Dispatch

**TLDR:** Brando sends `/experiment <branch-name>` in Telegram. OpenClaw on mercury2 (or Pro) checks out the branch, reads its top-level `cc_prompt.md` (or equivalent spec), runs the experiment in a tmux session, posts heartbeats to `openclaw-ops`, and DMs Brando on completion with results + PR link.

## Goal

Collapse "I want to run experiment X" → "ssh to mercury2, tmux new, git checkout, read prompt, paste into Claude Code, wait" into one Telegram command. Off-load running experiments from Brando's laptop to mercury2's compute.

## When this fires

- **Brando-initiated (Telegram)** — `/experiment <branch-name> [--host mercury2|mac-pro] [--model gpt-5.6-sol] [--runner claude|codex]`.

**Never** dispatched automatically. Each experiment requires Brando's explicit invocation.

## Inputs

1. **Branch name** — the experiment branch to check out (e.g. `claude/foo-bar-XYZ`).
2. **Host** — `mercury2` (default for compute-heavy) or `mac-pro` (default for local-only experiments).
3. **Spec path** — defaults to `<branch-root>/cc_prompt.md` or `<branch-root>/experiments/<NN>_<name>/cc_prompt.md`; configurable via `--spec`.
4. **Runner** — `claude` (Claude Code headless) or `codex` (Codex CLI exec); defaults to whatever the spec frontmatter declares.
5. **Model** — defaults to whatever the spec declares; configurable via `--model`.

## Workflow

1. **Capture**: Brando sends the command.
2. **Validate**: branch exists on origin; spec file exists at expected path; host is reachable.
3. **Show**: preview — branch, target host, spec path, runner, model, estimated runtime if known.
4. **Approve (Brando)**: `post` to dispatch; `edit: --host mac-pro` to swap host; `cancel` to abort.
5. **Execute**:
   - SSH to target host.
   - `cd ~/agents-config && git fetch && git checkout <branch>`.
   - Open new tmux session named `experiment-<branch-slug>`.
   - Inside tmux, launch the runner (one of):
     - **Claude (default)**: `claude --headless --prompt "$(cat <spec>)" --output-dir ~/openclaw/experiments/<branch-slug>/`
     - **Codex CLI**: `codex exec --full-auto -m gpt-5.6-sol -c 'model_reasoning_effort="xhigh"' "$(cat <spec>)"`
     - Per-experiment override declared in spec frontmatter.
   - Detach.
6. **Heartbeat**: every 15 min, post `[host] experiment-<branch-slug> RUNNING @ <ts> | tail: <last-line-of-log>` to `openclaw-ops`.
7. **Completion**: when tmux session exits, post `[host] experiment-<branch-slug> DONE @ <ts> | exit: <code>` and DM Brando with: branch, runtime, log tail, output dir, PR link if a PR was created.
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
- **mercury2 unavailability** — when mercury2 is down for slurm migration, fail over to mac-pro with a louder warning, or refuse and ask Brando to wait.

## Open setup questions

1. **Runner default** — `claude --headless` or `codex exec`? Brando uses both; spec frontmatter could declare per-experiment.
2. **Spec frontmatter schema** — define a YAML header for spec files: `model`, `runner`, `expected_runtime`, `output_dir`.
3. **PR detection** — how does the runner declare "I created PR #X"? Convention: write the PR URL to `~/openclaw/experiments/<branch-slug>/_pr_url.txt` at completion.
4. **Cross-host coordination** — if Brando dispatches the same branch twice in quick succession, refuse the second; or queue?

## Status

| Date | Status |
|------|--------|
| 2026-05-08 | Skeleton drafted. Setup questions pending. Implementation deferred until Phase 6.6 of [`MASTER_PLAN.md`](../MASTER_PLAN.md) (after mercury2 install). |
