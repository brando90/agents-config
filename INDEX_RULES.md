# INDEX_RULES.md — Global Rules & Doc Routing

Load only the docs relevant to your current task.

---

## Global Rules (always active)

1. **Never commit secrets.** Use environment variables or reference existing config files (`~/keys/`, `~/.ssh/config`).
2. **Prefer references over full context loading.** Cite file paths as text (e.g., `~/agents-config/machine/mac.md`); load the file only when the task needs it. A "reference" here is a written path to a doc — not a symlink or memory address.
3. **Verify before pushing.** Review diffs for secrets, unintended changes, broken imports.
4. **Before sending your final response on any non-trivial user request, dispatch a cross-agent reviewer.** One QA pass per user-assigned task, not per commit. See [`workflows/qa-gating.md`](workflows/qa-gating.md).
5. **Keep `agents-config` self-consistent.** When modifying this repo, ensure INDEX_RULES.md, README.md, and listed doc paths remain accurate.
6. **Use explicit anchored paths in prose doc references and commands.** Write `~/agents-config/INDEX_RULES.md` or `~/veribench/docs/agent-docs/INDEX.md`, never bare relative references like `docs/agent-docs/`. The user works across many repos and machines, so unanchored paths are ambiguous without context.
7. **Re-read agent-config files after any edit.** If you or the user modify any file under `~/agents-config/` (for example `~/agents-config/INDEX_RULES.md`, `~/agents-config/README.md`, files under `~/agents-config/workflows/`, or files under `~/agents-config/machine/`), immediately re-read the changed file(s) so your context stays current for the rest of the conversation.
8. **End every response with a TLDR.** Every response — not just task completion — must end with a `**TLDR:**` line: 1–2 sentences summarizing what was done or decided. This applies to all agents (Claude Code, Codex, etc.).
9. **Refresh agents-config before each new user task.** At the start of every non-trivial user request: (1) `git -C ~/agents-config pull` to fetch remote changes, (2) re-read `~/agents-config/INDEX_RULES.md` into your active context so the current session has the latest rules and doc references, (3) if the pull brought changes, also re-read any changed machine or workflow files relevant to your current environment. For long sessions (over 1 hour), also refresh mid-task — check with `date` and compare to your last pull. Push any uncommitted agents-config changes and run QA if changes were pulled from another agent.
10. **Always use `ls -la` (not `ls`) when listing directories for keys, tokens, configs, or credentials.** Hidden (dot-prefixed) files are common for sensitive data — plain `ls` omits them. This applies to any directory likely to hold secrets (e.g., `~/keys/`, `~/.ssh/`, `~/.config/`).
11. **Keep PRs short.** The PR description must start with a **Summary** section of 5–10 bullet points max (one line each). Follow with a short **Test plan** (2–3 bullets). Include links (W&B Report URLs, relevant docs). After these two sections, an optional **Appendix** may contain extended details, file lists, or context — but assume the reader stops after the summary. No walls of text.

---

## Machine Configs

Load the one matching your current environment. Machine docs contain only behavioral constraints and gotchas — not discoverable specs. Run bash commands (`uname -m`, `nvidia-smi`, etc.) to inspect hardware at runtime.

- [`machine/ampere1.md`](machine/ampere1.md) — SNAP ampere1 node (8x A100-80GB)
- [`machine/skampere1.md`](machine/skampere1.md) — SNAP skampere1 node (8x A100-80GB)
- [`machine/snap.md`](machine/snap.md) — Stanford SNAP cluster
- [`machine/sherlock.md`](machine/sherlock.md) — Stanford Sherlock HPC
- [`machine/marlowe.md`](machine/marlowe.md) — Stanford Marlowe cluster
- [`machine/mac.md`](machine/mac.md) — local macOS dev machine

## Workflows

- [`workflows/qa-gating.md`](workflows/qa-gating.md) — cross-agent review protocol (default-on)
- [`workflows/git-worktrees.md`](workflows/git-worktrees.md) — worktree isolation for parallel agents
- [`workflows/expts-and-results.md`](workflows/expts-and-results.md) — experiment structure and results reporting
- [`workflows/tweprints.md`](workflows/tweprints.md) — tweet thread format for research announcements
- [`workflows/blog-posts.md`](workflows/blog-posts.md) — SAIL-style blog post format for research projects
