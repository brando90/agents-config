# INDEX.md — Master Routing Table

Load only the docs relevant to your current task.

---

## Global Rules (always active)

1. **Never commit secrets.** Use environment variables or reference existing config files (`~/keys/`, `~/.ssh/config`).
2. **Prefer pointers over full context loading.** Reference file paths; load on demand.
3. **Verify before pushing.** Review diffs for secrets, unintended changes, broken imports.
4. **Before reporting done on any non-trivial task, dispatch a cross-agent reviewer.** See [`workflows/qa-gating.md`](workflows/qa-gating.md).
5. **Keep `agents-config` self-consistent.** When modifying this repo, ensure INDEX.md, README.md, and listed doc paths remain accurate.

---

## Machine Configs

Load the one matching your current environment.

- [`machine/ampere1.md`](machine/ampere1.md) — GPU cluster node (A100/H100)
- [`machine/snap.md`](machine/snap.md) — Stanford SNAP cluster
- [`machine/sherlock.md`](machine/sherlock.md) — Stanford Sherlock HPC
- [`machine/marlowe.md`](machine/marlowe.md) — Stanford Marlowe cluster
- [`machine/mac.md`](machine/mac.md) — local macOS dev machine

## Workflows

- [`workflows/qa-gating.md`](workflows/qa-gating.md) — cross-agent review protocol (default-on)
- [`workflows/git-worktrees.md`](workflows/git-worktrees.md) — worktree isolation for parallel agents
- [`workflows/expts-and-results.md`](workflows/expts-and-results.md) — experiment structure and results reporting

