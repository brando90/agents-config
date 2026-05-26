#!/usr/bin/env bash
# Respawn the openclaw gateway tmux session if it has died.
#
# Wired into crontab as:  */2 * * * * /dfs/scratch0/<user>/agents-config/experiments/01_self_hosted_openclaw/scripts/openclaw-watchdog.sh
# Equivalent of openclaw-health-watcher.sh (macOS) but Linux/tmux-flavored.
#
# Cheap: 99% of invocations are a single tmux has-session check that exits 0.
set -euo pipefail

LOG_DIR="${HOME}/.openclaw/logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/watchdog-$(date +%F).log"

if tmux has-session -t openclaw-gateway 2>/dev/null; then
  exit 0
fi

# Session is gone — restart it.
{
  echo "=== $(date -Is) openclaw-gateway session missing; respawning ==="
  # shellcheck disable=SC1090
  source "${HOME}/.bashrc" 2>/dev/null || true
  tmux new-session -d -s openclaw-gateway \
    "bash -lc 'openclaw gateway run 2>&1 | tee -a ${LOG_DIR}/gateway-\$(date +%F).log'"
  sleep 5
  if tmux has-session -t openclaw-gateway 2>/dev/null; then
    echo "=== respawn OK ==="
  else
    echo "=== respawn FAILED ==="
    exit 1
  fi
} >>"$LOG" 2>&1
