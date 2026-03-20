# INDEX.md — Master Routing Table

Load only the docs relevant to your current task.

---

## Global Rules (always active)

1. **Never commit secrets.** Use environment variables or gitignored `private/` dirs.
2. **Prefer pointers over full context loading.** Reference file paths; load on demand.
3. **Verify before pushing.** Review diffs for secrets, unintended changes, broken imports.
4. **Match scope to request.** Only modify what was asked for.
5. **Record exact model IDs.** Log exact identifiers (e.g., `claude-opus-4-6`) for reproducibility.
6. **Before reporting done on any non-trivial task, dispatch a cross-agent reviewer.** See [`workflows/qa-gating.md`](workflows/qa-gating.md).
7. **Keep `agents-config` self-consistent.** When modifying this repo, ensure INDEX.md, README.md, and listed doc paths remain accurate.

---

## Machine Configs

Load the one matching your current environment.

- [`machine/public/ampere1.md`](machine/public/ampere1.md) — GPU cluster node (A100/H100)
- [`machine/public/snap.md`](machine/public/snap.md) — Stanford SNAP cluster
- [`machine/public/sherlock.md`](machine/public/sherlock.md) — Stanford Sherlock HPC
- [`machine/public/marlowe.md`](machine/public/marlowe.md) — Stanford Marlowe cluster
- [`machine/public/mac.md`](machine/public/mac.md) — local macOS dev machine
- [`machine/public/TEMPLATE.md`](machine/public/TEMPLATE.md) — blank template for new machines

## Workflows

- [`workflows/qa-gating.md`](workflows/qa-gating.md) — cross-agent review protocol (default-on)
- [`workflows/byobu-agents.md`](workflows/byobu-agents.md) — parallel agent sessions via byobu
- [`workflows/git-worktrees.md`](workflows/git-worktrees.md) — worktree isolation for parallel agents
- [`workflows/clauded-usage.md`](workflows/clauded-usage.md) — `clauded` alias and skip-permissions
- [`workflows/expts-and-results.md`](workflows/expts-and-results.md) — experiment structure and results reporting

## Conventions

- [`conventions/general-coding.md`](conventions/general-coding.md) — commit, branch, PR conventions
- [`conventions/agent-prompt-builder-rules.md`](conventions/agent-prompt-builder-rules.md) — meta-rules for writing agent prompts
