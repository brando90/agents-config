# Workflow: Parallel Agent Sessions with Byobu

<!-- TODO: clarify why byobu over tmux more thoroughly, document broken-install edge cases -->

Run multiple AI coding agents in parallel using byobu terminal multiplexer sessions.

---

## Why Byobu over tmux

Byobu wraps tmux with sane defaults: persistent status bar, intuitive keybindings, automatic session resumption on SSH reconnect. You get tmux power without the config overhead.

```bash
# Install
sudo apt install byobu   # Linux
brew install byobu        # macOS

# Enable byobu on login (optional)
byobu-enable
```

---

## Session Naming Convention

Name sessions by agent and task for easy identification:

```
<agent>-<project>-<task>
```

Examples:
- `cc-veribench-exp04` — Claude Code working on veribench experiment 04
- `codex-harbor-bugfix` — Codex fixing a Harbor bug
- `cc-review-pr15` — Claude Code reviewing PR #15

---

## Running Parallel Agents

### Launch sessions

```bash
# Session 1: Claude Code on task A
byobu new-session -d -s cc-project-taskA
byobu send-keys -t cc-project-taskA 'cd ~/project && claude' Enter

# Session 2: Codex on task B
byobu new-session -d -s codex-project-taskB
byobu send-keys -t codex-project-taskB 'cd ~/project && codex' Enter

# Session 3: Claude Code on a different repo
byobu new-session -d -s cc-other-repo
byobu send-keys -t cc-other-repo 'cd ~/other-repo && claude' Enter
```

### Monitor sessions

```bash
# List all sessions
byobu list-sessions

# Attach to a specific session
byobu attach -t cc-project-taskA

# Switch between sessions (inside byobu)
# F3 = previous window, F4 = next window
# Shift+F3 = previous session, Shift+F4 = next session
```

### Launcher script example

```bash
#!/bin/bash
# launch-agents.sh — Start parallel agent sessions for a project
PROJECT_DIR="$HOME/veribench"

# Claude Code on experiment work
byobu new-session -d -s cc-exp
byobu send-keys -t cc-exp "cd $PROJECT_DIR && claude" Enter

# Codex on test writing
byobu new-session -d -s codex-tests
byobu send-keys -t codex-tests "cd $PROJECT_DIR && codex" Enter

echo "Sessions started. Use 'byobu list-sessions' to see them."
echo "Attach with: byobu attach -t <session-name>"
```

---

## Important: File Conflict Avoidance

When running multiple agents on the same repo, use **git worktrees** to give each agent its own working copy. See [`git-worktrees.md`](git-worktrees.md).

Without worktrees, two agents editing the same file will create conflicts and corrupt each other's work.

---

## Key Bindings (Byobu defaults)

| Key | Action |
|:----|:-------|
| F2 | New window |
| F3 / F4 | Previous / next window |
| Shift+F2 | Split horizontally |
| Ctrl+F2 | Split vertically |
| Shift+F3 / F4 | Previous / next session |
| F6 | Detach |
| F8 | Rename window |
