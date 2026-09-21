#!/usr/bin/env bash
# TLDR: Shared (DFS) entry point for the Stanford-enterprise Claude profile; it only dispatches to
# the node-local runtime so sessions, caches and the runtime binary never live on the shared FS.
# Install under both the short `-su` and explicit `-stanford` names (see push_claude_su_snap.sh).
set -euo pipefail
command_name=$(basename "$0")
case "$command_name" in
  claude-su|claude-stanford) node_command=claude-su ;;
  clauded-su|clauded-stanford) node_command=clauded-su ;;
  *) echo 'Install as claude-su, clauded-su, claude-stanford, or clauded-stanford' >&2; exit 1 ;;
esac
entry="/lfs/$(hostname -s)/0/brando9/.local/bin/$node_command"
if [ ! -x "$entry" ]; then
  echo "Stanford node runtime missing: run install_su_node.sh on this node" >&2
  exit 1
fi
exec "$entry" "$@"
