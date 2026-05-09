# Standing Order — Coding-Task Dispatch (general "go fix X for me")

**TLDR:** Brando DMs `/code <repo> <task>` (or free-form *"update agents-config to add X"* / *"in brandomiranda blog, fix the Y typo"*). OpenClaw on the target host checks out a new branch, runs the agent (`claude --headless` by default; `codex --full-auto -m gpt-5.5 -c 'model_reasoning_effort="xhigh"'` if Brando says yolo), commits + pushes the branch, opens a PR, and DMs Brando the PR link. Sister to [`experiment_dispatch.md`](./experiment_dispatch.md) but for arbitrary repos, not just experiment branches.

## Goal

Collapse "I want to make a small change to one of my repos" → "ssh to a host, clone if needed, branch, run claude, review, push, open PR" into one Telegram command. Off-load the linear plumbing to OpenClaw; Brando reviews on his phone and merges.

## When this fires

- **Brando-initiated (Telegram)** — `/code <repo> <task description>` — e.g. `/code agents-config add a CI workflow for markdown lint`.
- **Brando-initiated (Telegram)** — free-form: *"update brandomiranda blog with a post about VeriBench accept"*.
- **Brando-initiated (Telegram)** — `/code <repo> --runner codex --yolo <task>` to use Codex CLI in `--full-auto` mode instead of Claude Code headless.

**Never** dispatched automatically. Each coding task requires Brando's explicit invocation.

## Inputs

1. **Repo** — short name resolved against a known-repos table (`config/repos.yml` — see Open setup questions). Defaults: `agents-config` → `~/agents-config`, `brandomiranda` → `~/brando90/brandomiranda`, `veribench` → `~/veribench`, etc.
2. **Task** — the natural-language change request.
3. **Host** — `mac-air` (default, fast iteration) / `mac-pro` (off the laptop you're using) / `mercury2` (long-running compute / low-priority).
4. **Runner** — `claude` (default — Claude Code headless) or `codex` (Codex CLI `--full-auto` aka "yolo" mode). Spec frontmatter or `--runner` flag overrides.
5. **PR style** — `--draft` (default; safer) or `--ready`.

## Workflow

1. **Capture**: Brando sends the command.
2. **Resolve**: repo short-name → working directory; ensure target host is reachable; ensure `cd <repo> && git status` is clean (else refuse: "uncommitted changes in <repo>; commit/stash first").
3. **Plan**: classify task complexity (trivial / standard / risky); pick branch name slug (`claude/<short-task-slug>` or `codex/<short-task-slug>`); pick runner per Inputs.5.
4. **Show**: preview — repo, host, branch name, runner, task description, estimated runtime if known.
5. **Approve (Brando)**: `post` to dispatch / `edit: --runner codex` to swap runner / `cancel` to abort.
6. **Execute**:
   - SSH to target host (skip if already there).
   - `cd <repo> && git fetch && git checkout -b <branch>`.
   - Open new tmux session named `code-<branch-slug>`.
   - Inside tmux, launch the runner:
     - **Claude (default)**: `claude --headless --prompt "<task description>" --output-dir ~/openclaw/coding/<branch-slug>/`
     - **Codex yolo**: `codex exec --full-auto -m gpt-5.5 -c 'model_reasoning_effort="xhigh"' "<task description>"`
   - Detach.
7. **Heartbeat**: every 15 min, post `[host] code-<branch-slug> RUNNING @ <ts> | tail: <last-line-of-log>` to `openclaw-ops`.
8. **Completion**: when tmux session exits, runner has typically committed + pushed. Verify:
   - `git log <branch> ^main` shows commits.
   - `git push origin <branch>` succeeded (idempotent if runner pushed already).
   - `gh pr create --draft` (default) with the task description as body.
9. **Notify**: per [`README.md`](./README.md) Default Safety Rule 8:
   - Telegram reply in the originating chat: `✅ <repo> code task done — <PR-url>`.
   - Email Brando (3-CC per Trigger Rule 26): subject `OpenClaw: code-<branch-slug> done — <task>`; body lists files changed (diff stat) + PR URL + log location.
10. **Log**: `~/openclaw/audit/coding_dispatched.jsonl`.

## Outputs

- A new branch on the target repo with the change.
- An open PR (draft by default).
- Heartbeats in `openclaw-ops`.
- Telegram + email notifications per the canonical completion-notification rule.
- Audit log entry.

## Safety rules

- **Approval level:** `approve_to_dispatch` (running a coding agent that opens a draft PR is reversible — the PR is still draft + still Brando-merged).
- **Branch sanity:** refuse to push to `main` / `master` directly. Always create a branch.
- **Repo allowlist:** `config/repos.yml` maps short-name → path + allowed-hosts. Refuse if the repo isn't in the allowlist (avoids "go fix bug in `~/.ssh/config`").
- **Resource ceiling:** refuse if mercury2 is already running > 2 OpenClaw coding/experiment tasks concurrently.
- **PR-content sanity:** if the runner produced no commits OR the diff is empty, don't open a PR; DM Brando: `⚠️ runner exited cleanly but produced no diff — check log <path>`.
- **Secret scan:** before `git push`, run `git diff <branch> ^main | grep -iE 'token|secret|password|api[_-]?key'` — if any hit, DM Brando the diff line(s) and require a fresh `post` before pushing.
- **Yolo mode (Codex `--full-auto`)** is allowed but logged louder — heartbeat tag is `RUNNING-YOLO` so Brando can see at a glance which dispatches are unsupervised. The `--full-auto` flag means the codex CLI auto-approves its own actions; treat it as Brando-pre-authorized only because it's invoked through this approved standing order.

## Open setup questions

1. **`config/repos.yml`** — populate with Brando's actual repos:
   ```yaml
   agents-config:
     path: ~/agents-config
     allowed-hosts: [mac-air, mac-pro, mercury2]
   brandomiranda:
     path: ~/brando90/brandomiranda   # or wherever
     allowed-hosts: [mac-air, mac-pro]
   veribench:
     path: ~/veribench
     allowed-hosts: [mac-pro, mercury2]   # not on the Air for compute
   ultimate-utils:
     path: ~/ultimate-utils
     allowed-hosts: [mac-air, mac-pro, mercury2]
   ```
2. **PR template per repo** — should `gh pr create` use a per-repo PR template? If yes, point to it.
3. **Runner default per repo** — Brando might prefer `codex --yolo` for `agents-config` (high-trust) but `claude` for `veribench` (research code, more careful). Encode in `repos.yml`.
4. **Auto-merge?** — for tiny tasks (< 5-line diffs, all in markdown/comments), should there be a "yolo + auto-merge" mode that opens a non-draft PR + enables auto-merge if CI passes? Probably no for v1. Track in TODO.
5. **Cross-repo coordination** — what if a task spans 2 repos (e.g. "update agents-config + brandomiranda blog with the same release notes")? V1: refuse and ask Brando to issue 2 separate `/code` commands. V2: design a multi-repo dispatch.

## Status

| Date | Status |
|------|--------|
| 2026-05-09 | Skeleton drafted (autonomous setup pass). Setup questions pending. Implementation deferred until Phase 6.x (after experiment_dispatch.md is proven on mercury2). |
