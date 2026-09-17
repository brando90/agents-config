#!/usr/bin/env bash
# TLDR: Shared (DFS) entry point for the Stanford-enterprise Claude profile; it only dispatches to
# the node-local runtime so sessions, caches and the runtime binary never live on the shared FS.
# Install as /dfs/scratch0/brando9/bin/claude-su and .../clauded-su (see push_claude_su_snap.sh).
set -euo pipefail
command_name=$(basename "$0")
case "$command_name" in claude-su|clauded-su) ;; *) echo 'Install as claude-su or clauded-su' >&2; exit 1;; esac
entry="/lfs/$(hostname -s)/0/brando9/.local/bin/$command_name"
if [ ! -x "$entry" ]; then
  echo "Stanford node runtime missing: run install_su_node.sh on this node" >&2
  exit 1
fi
exec "$entry" "$@"
