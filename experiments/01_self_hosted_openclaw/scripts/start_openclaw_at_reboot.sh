#!/usr/bin/env bash
# Re-launch the openclaw gateway in tmux after a SNAP node reboot.
#
# Wired into crontab as:  @reboot /dfs/scratch0/<user>/agents-config/experiments/01_self_hosted_openclaw/scripts/start_openclaw_at_reboot.sh
# Mirrors the watcher pattern in machine/snap.md:108-120.
#
# Logs to /tmp/start_openclaw_at_reboot_<host>.log so post-mortem of a failed
# boot is recoverable even before DFS comes up.
set -euo pipefail

LOG="/tmp/start_openclaw_at_reboot_$(hostname -s).log"
exec >>"$LOG" 2>&1
echo "=== $(date -Is) start_openclaw_at_reboot ==="

DFS_USER_ROOT="/dfs/scratch0/$(id -un)"

# 1. Wait for DFS to come up (up to ~5 min).
for i in $(seq 1 60); do
  [[ -d "$DFS_USER_ROOT" ]] && break
  sleep 5
done
[[ -d "$DFS_USER_ROOT" ]] || { echo "DFS never came up; aborting"; exit 1; }

# 2. Refresh Kerberos before touching anything AFS/DFS-protected.
if [[ -x "${DFS_USER_ROOT}/bin/krenew.sh" ]]; then
  "${DFS_USER_ROOT}/bin/krenew.sh" || echo "krenew.sh exited non-zero (continuing)"
fi

# 3. Source .bashrc to pick up NVM (node is needed by openclaw) + LFS HOME override.
# shellcheck disable=SC1090
source "${HOME}/.bashrc" 2>/dev/null || true

# 4. (Re)launch gateway in tmux — idempotent.
tmux kill-session -t openclaw-gateway 2>/dev/null || true
sleep 1
tmux new-session -d -s openclaw-gateway \
  "bash -lc 'openclaw gateway run 2>&1 | tee -a ~/.openclaw/logs/gateway-\$(date +%F).log'"

# 5. Sanity check.
sleep 8
if tmux has-session -t openclaw-gateway 2>/dev/null; then
  echo "=== launched: tmux session openclaw-gateway live ==="
else
  echo "=== FAILED to start tmux session openclaw-gateway ==="
  exit 1
fi
