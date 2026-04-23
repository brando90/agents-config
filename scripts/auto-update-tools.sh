#!/usr/bin/env bash
# Auto-update Claude Code and Codex CLI to latest versions.
# Called by Claude Code SessionStart hook and can be run manually.
# Safe to run concurrently — uses lock files and suppresses errors.
set -euo pipefail

LOCKFILE="${HOME}/.claude/.update.lock"
DFS_PREFIX="/dfs/scratch0/brando9"

# Remove stale lock (older than 5 minutes)
if [ -f "$LOCKFILE" ]; then
  find "$LOCKFILE" -mmin +5 -delete 2>/dev/null || true
fi

# Skip if another update is running
if [ -f "$LOCKFILE" ]; then
  exit 0
fi

trap 'rm -f "$LOCKFILE"' EXIT
echo $$ > "$LOCKFILE"

# Update Claude Code (installed at DFS prefix, shared across all SNAP nodes)
npm install --prefix "$DFS_PREFIX" -g @anthropic-ai/claude-code@latest >/dev/null 2>&1 || true

# Update Codex CLI (installed via nvm global)
npm install -g @openai/codex@latest >/dev/null 2>&1 || true
