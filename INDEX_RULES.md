# INDEX_RULES.md — Global Rules & Doc Routing

Load only the docs relevant to your current task.

---

## Global Rules (always active)

1. **Never commit secrets.** Use environment variables or reference existing config files (`~/keys/`, `~/.ssh/config`).
2. **Prefer references over full context loading.** Cite file paths as text (e.g., `~/agent-config/machine/mac.md`); load the file only when the task needs it. A "reference" here is a written path to a doc — not a symlink or memory address.
3. **Verify before pushing.** Review diffs for secrets, unintended changes, broken imports.
4. **Before sending your final response on any non-trivial user request, run the two-step QA chain.** (a) **Correctness QA:** dispatch a cross-agent reviewer to catch logic errors and broken behavior — see [`workflows/qa-correctness.md`](workflows/qa-correctness.md). (b) **Structural QA:** after correctness passes, run the anti-degradation refactoring gate on repos with substantial source code — see [`workflows/qa-structural.md`](workflows/qa-structural.md). One QA chain per user-assigned task, not per commit. Structural QA may be skipped for markdown-only repos or trivial changes.
5. **Keep `agents-config` self-consistent.** When modifying this repo, ensure INDEX_RULES.md, README.md, and listed doc paths remain accurate.
6. **Use explicit anchored paths in prose doc references and commands.** Write `~/agent-config/INDEX_RULES.md` or `~/veribench/docs/agent-docs/INDEX.md`, never bare relative references like `docs/agent-docs/`. The user works across many repos and machines, so unanchored paths are ambiguous without context.
7. **Re-read agent-config files after any edit.** If you or the user modify any file under `~/agent-config/` (for example `~/agent-config/INDEX_RULES.md`, `~/agent-config/README.md`, files under `~/agent-config/workflows/`, or files under `~/agent-config/machine/`), immediately re-read the changed file(s) so your context stays current for the rest of the conversation.
8. **End with a TLDR.** After completing a task, finish your response with a 1–2 sentence summary of what was done.
9. **Refresh agents-config before each new user task.** At the start of every non-trivial user request: (1) `git -C ~/agent-config pull` to fetch remote changes, (2) re-read `~/agent-config/INDEX_RULES.md` into your active context so the current session has the latest rules and doc references, (3) if the pull brought changes, also re-read any changed machine or workflow files relevant to your current environment. For long sessions (over 1 hour), also refresh mid-task — check with `date` and compare to your last pull. Push any uncommitted agents-config changes and run QA if changes were pulled from another agent.

---

## Machine Configs

Load the one matching your current environment. Machine docs contain only behavioral constraints and gotchas — not discoverable specs. Run bash commands (`uname -m`, `nvidia-smi`, etc.) to inspect hardware at runtime.

- [`machine/ampere1.md`](machine/ampere1.md) — SNAP ampere1 node (8x A100-80GB)
- [`machine/snap.md`](machine/snap.md) — Stanford SNAP cluster
- [`machine/sherlock.md`](machine/sherlock.md) — Stanford Sherlock HPC
- [`machine/marlowe.md`](machine/marlowe.md) — Stanford Marlowe cluster
- [`machine/mac.md`](machine/mac.md) — local macOS dev machine

## Workflows

- [`workflows/qa-correctness.md`](workflows/qa-correctness.md) — cross-agent correctness review (step 1 of QA chain)
- [`workflows/qa-structural.md`](workflows/qa-structural.md) — anti-degradation structural refactoring gate (step 2 of QA chain)
- [`workflows/git-worktrees.md`](workflows/git-worktrees.md) — worktree isolation for parallel agents
- [`workflows/expts-and-results.md`](workflows/expts-and-results.md) — experiment structure and results reporting
- [`workflows/repo-init.md`](workflows/repo-init.md) — migrating repos to agents-config (from old monolithic CLAUDE.md / /init)
