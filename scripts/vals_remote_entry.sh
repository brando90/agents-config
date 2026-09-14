#!/usr/bin/env bash
# Canonical shared entry point; runtime/session files stay on the current node.
set -euo pipefail
command_name=$(basename "$0")
case "$command_name" in claude-vals|clauded-vals) ;; *) echo 'Install as claude-vals or clauded-vals' >&2; exit 1;; esac
entry="/lfs/$(hostname -s)/0/brando9/.local/bin/$command_name"
if [ ! -x "$entry" ]; then
  echo "Vals node runtime missing: run the reviewed install_vals_node.sh on this node" >&2
  exit 1
fi
exec "$entry" "$@"
