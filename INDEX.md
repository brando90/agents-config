# INDEX.md — Master Routing Table

This is the central index for all agent documentation. Load only the docs relevant to your current task.

---

## Global Rules (always active)

These rules apply to every task, every agent, every repo. Do not skip them.

1. **Never commit secrets.** No API keys, tokens, passwords, or private IPs in tracked files. Use environment variables or files in gitignored `private/` directories.
2. **Prefer pointers over full context loading.** Only inline content the agent always needs regardless of task. For everything else, reference the file path and let the agent load it on demand. <!-- TODO: define pointer-vs-full-load policy precisely (default: pointers, inline only for critical global rules) -->
3. **Verify before pushing.** After completing code edits, review the diff before pushing or creating a PR. Check for accidental secret inclusion, unintended file changes, and broken imports.
4. **Match scope to request.** Only modify what was asked for. Don't refactor surrounding code, add unsolicited features, or "improve" files you weren't asked to touch.
5. **Record exact model IDs.** When running experiments or evaluations, always log the exact model identifier used (e.g., `claude-opus-4-6`, `gpt-5.4`) for reproducibility.
6. **After completing any non-trivial task, dispatch a cross-agent reviewer before reporting done.** See [`workflows/qa-gating.md`](workflows/qa-gating.md) for dispatch commands. Reviewers fix with minimal changes only — never refactor or overcomplicate what was already committed.

---

## QA Gating (default-on)

**This is default-on, not opt-in.** After completing any non-trivial task, dispatch a cross-agent reviewer:
- If you are CC → dispatch `codex` (or `clauded -p` if Codex unavailable)
- If you are Codex → dispatch `clauded -p`
- Reviewer fixes with **minimal changes only** — no refactoring, no overcomplicating
- Skip only for trivial edits, or if user says "skip review"
- Reviewers do NOT dispatch reviewers (no recursion)

Full protocol + dispatch commands: [`workflows/qa-gating.md`](workflows/qa-gating.md)

---

## Doc Registry

### Machine Configs

Context about the machines you're working on. Load the one matching your current environment.

| Doc | Path | Description |
|:----|:-----|:------------|
| Ampere1 | [`machine/public/ampere1.md`](machine/public/ampere1.md) | GPU cluster node template (A100/H100) |
| SNAP | [`machine/public/snap.md`](machine/public/snap.md) | Stanford SNAP cluster template |
| Mac | [`machine/public/mac.md`](machine/public/mac.md) | Local macOS dev machine template |
| Sherlock | [`machine/public/sherlock.md`](machine/public/sherlock.md) | Stanford Sherlock HPC cluster template |
| Marlowe | [`machine/public/marlowe.md`](machine/public/marlowe.md) | Stanford Marlowe cluster template |
| Template | [`machine/public/TEMPLATE.md`](machine/public/TEMPLATE.md) | Blank template for new machines |

### Workflows

How to run agents, manage parallel sessions, and review code.

| Doc | Path | Description |
|:----|:-----|:------------|
| Byobu Agents | [`workflows/byobu-agents.md`](workflows/byobu-agents.md) | Run parallel agent sessions using byobu |
| Git Worktrees | [`workflows/git-worktrees.md`](workflows/git-worktrees.md) | Worktree isolation for parallel agents |
| QA Gating | [`workflows/qa-gating.md`](workflows/qa-gating.md) | Cross-agent review protocol (**default after every non-trivial task**) |
| clauded Usage | [`workflows/clauded-usage.md`](workflows/clauded-usage.md) | `clauded` alias and skip-permissions patterns |
| Experiments & Results | [`workflows/expts-and-results.md`](workflows/expts-and-results.md) | Experiment structure, results storage, reporting conventions |

### Conventions

Coding standards and prompt-writing rules.

| Doc | Path | Description |
|:----|:-----|:------------|
| General Coding | [`conventions/general-coding.md`](conventions/general-coding.md) | Commit, branch, PR conventions |
| Prompt Builder Rules | [`conventions/agent-prompt-builder-rules.md`](conventions/agent-prompt-builder-rules.md) | Meta-rules for writing agent instructions |
