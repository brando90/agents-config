# Workflow: Git Worktrees for Parallel Agent Isolation

Use git worktrees to give each parallel agent its own isolated working copy of the repo.

---

## Why This Matters

If two agents edit the same repo directory simultaneously, they'll overwrite each other's changes. Git worktrees solve this by creating separate checkout directories that share the same `.git` history.

Each agent gets:
- Its own branch
- Its own working directory
- Full git history access
- No file conflicts with other agents

---

## Setup

### Create worktrees for parallel agents

```bash
cd ~/project   # your main repo checkout

# Create a worktree for Claude Code
git worktree add ../project-cc-work cc-feature-branch
# Creates ~/project-cc-work/ on branch cc-feature-branch

# Create a worktree for Codex
git worktree add ../project-codex-work codex-feature-branch
# Creates ~/project-codex-work/ on branch codex-feature-branch
```

### Point each agent at its worktree

```bash
# Terminal 1: Claude Code
cd ~/project-cc-work && claude

# Terminal 2: Codex
cd ~/project-codex-work && codex
```

---

## Managing Worktrees

```bash
# List all worktrees
git worktree list

# Remove a worktree after merging
git worktree remove ../project-cc-work

# Prune stale worktree references
git worktree prune
```

---

## Combining with Byobu

```bash
#!/bin/bash
# parallel-agents.sh — Full setup for parallel isolated agents
PROJECT="$HOME/my-project"
cd "$PROJECT"

# Create worktrees
git worktree add ../my-project-cc agent-cc-branch 2>/dev/null || true
git worktree add ../my-project-codex agent-codex-branch 2>/dev/null || true

# Launch byobu sessions
byobu new-session -d -s cc-work
byobu send-keys -t cc-work "cd ../my-project-cc && claude" Enter

byobu new-session -d -s codex-work
byobu send-keys -t codex-work "cd ../my-project-codex && codex" Enter

echo "Parallel agents running in isolated worktrees."
```

---

## Rules

- Never have two agents working in the same worktree directory.
- Always create a fresh branch for each worktree to avoid checkout conflicts.
- Clean up worktrees after merging: `git worktree remove <path>`.
- The main checkout (`~/project/`) can still be used for manual work or a third agent.
