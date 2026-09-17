#!/usr/bin/env bash
# TLDR: Shared (DFS) entry point for the Stanford-enterprise Codex profile; it only dispatches to
# the node-local wrapper so CODEX_HOME (auth.json, sessions, history) stays on the node.
# Install as /dfs/scratch0/brando9/bin/codex-su and .../codexd-su (see push_codex_su_snap.sh).
set -euo pipefail
command_name=$(basename "$0")
case "$command_name" in codex-su|codexd-su) ;; *) echo 'Install as codex-su or codexd-su' >&2; exit 1;; esac
entry="/lfs/$(hostname -s)/0/brando9/.local/bin/$command_name"
if [ ! -x "$entry" ]; then
  echo "Stanford Codex node runtime missing: run install_codex_su_node.sh on this node" >&2
  exit 1
fi
exec "$entry" "$@"
