# INDEX.md — Master Routing Table

Load only the docs relevant to your current task.

---

## Global Rules (always active)

1. **Never commit secrets.** Use environment variables or reference existing config files (`~/keys/`, `~/.ssh/config`).
2. **Prefer references over full context loading.** Cite file paths as text (e.g., `~/agent-config/machine/mac.md`); load the file only when the task needs it. A "reference" here is a written path to a doc — not a symlink or memory address.
3. **Verify before pushing.** Review diffs for secrets, unintended changes, broken imports.
4. **Before sending your final response on any non-trivial user request, dispatch a cross-agent reviewer.** One QA pass per user-assigned task, not per commit. See [`workflows/qa-gating.md`](workflows/qa-gating.md).
5. **Keep `agents-config` self-consistent.** When modifying this repo, ensure INDEX.md, README.md, and listed doc paths remain accurate.
6. **Use explicit anchored paths in prose doc references and commands.** Write `~/agent-config/INDEX.md` or `~/veribench/docs/agent-docs/INDEX.md`, never bare relative references like `docs/agent-docs/`. The user works across many repos and machines, so unanchored paths are ambiguous without context.
7. **Re-read agent-config files after any edit.** If you or the user modify any file under `~/agent-config/` (for example `~/agent-config/INDEX.md`, `~/agent-config/README.md`, files under `~/agent-config/workflows/`, or files under `~/agent-config/machine/`), immediately re-read the changed file(s) so your context stays current for the rest of the conversation.

---

## Machine Configs

Load the one matching your current environment. Machine docs contain only behavioral constraints and gotchas — not discoverable specs. Run bash commands (`uname -m`, `nvidia-smi`, etc.) to inspect hardware at runtime.

- [`machine/ampere1.md`](machine/ampere1.md) — GPU cluster node (A100/H100)
- [`machine/snap.md`](machine/snap.md) — Stanford SNAP cluster
- [`machine/sherlock.md`](machine/sherlock.md) — Stanford Sherlock HPC
- [`machine/marlowe.md`](machine/marlowe.md) — Stanford Marlowe cluster
- [`machine/mac.md`](machine/mac.md) — local macOS dev machine

## Workflows

- [`workflows/qa-gating.md`](workflows/qa-gating.md) — cross-agent review protocol (default-on)
- [`workflows/git-worktrees.md`](workflows/git-worktrees.md) — worktree isolation for parallel agents
- [`workflows/expts-and-results.md`](workflows/expts-and-results.md) — experiment structure and results reporting
