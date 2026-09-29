#!/usr/bin/env bash
# TLDR: Shared (DFS) entry point for the personal Claude profile (brandojazz@gmail.com); it only dispatches to
# the node-local runtime so sessions, caches and the runtime binary never live on the shared FS.
# Install under claude, clauded, claude-personal and clauded-personal.
set -euo pipefail
command_name=$(basename "$0")
case "$command_name" in
  claude|claude-personal) node_command=claude-personal ;;
  clauded|clauded-personal) node_command=clauded-personal ;;
  *) echo 'Install as claude, clauded, claude-personal or clauded-personal' >&2; exit 1 ;;
esac
entry="/lfs/$(hostname -s)/0/brando9/.local/bin/$node_command"
if [ ! -x "$entry" ]; then
  echo "Personal node runtime missing: run install_personal_node.sh on this node" >&2
  exit 1
fi
exec "$entry" "$@"
