# Workflow: `clauded` Alias (Skip Permissions Mode)

Documents the `clauded` alias for running Claude Code with `--dangerously-skip-permissions`.

---

## What It Is

```bash
alias clauded='claude --dangerously-skip-permissions'
```

This skips all permission prompts. Claude Code will read, write, execute, and delete without asking. Every tool call is auto-approved.

---

## When to Use It

- **Trusted, isolated environments:** A Docker container, a disposable VM, or a git worktree you can nuke.
- **Batch automation:** Running Claude Code in a script where no human is present to click "approve."
- **Repetitive tasks:** When you've already approved the same permission 50 times and trust the pattern.
- **Time-sensitive work:** When the permission prompts are slowing you down on well-understood tasks.

---

## When NOT to Use It

- **Shared machines** where Claude Code could affect other users' files.
- **Production environments** or repos deployed to live systems.
- **Repos with secrets** (`.env` files, API keys) that Claude Code might accidentally commit or print.
- **Unfamiliar codebases** where you're not sure what Claude Code might modify.
- **First run on a new task** — use normal mode first to understand what Claude wants to do, then switch to `clauded` once you trust the pattern.

---

## Best Practices

1. **Use with git worktrees.** If something goes wrong, `git checkout .` or delete the worktree. See [`git-worktrees.md`](git-worktrees.md).
2. **Review the diff after.** Even in skip-permissions mode, review what changed before committing.
3. **Set it per-session, not globally.** Don't add `clauded` to your shell profile's default. Use it intentionally.
4. **Combine with byobu.** Run `clauded` in a named byobu session so you can detach and reattach without losing context.

---

## Setup

Add to your `.bashrc` or `.zshrc`:

```bash
alias clauded='claude --dangerously-skip-permissions'
```

Or use it inline without an alias:

```bash
claude --dangerously-skip-permissions -p "refactor the utils module"
```
