#!/usr/bin/env bash
# TLDR: Shared (DFS) entry point for the Stanford-enterprise Codex profile; it only dispatches to
# the node-local wrapper so CODEX_HOME (auth.json, sessions, history) stays on the node.
# Install under both the short `-su` and explicit `-stanford` names (see push_codex_su_snap.sh).
set -euo pipefail
command_name=$(basename "$0")
case "$command_name" in
  codex-su|codex-stanford) node_command=codex-su ;;
  codexd-su|codexd-stanford) node_command=codexd-su ;;
  *) echo 'Install as codex-su, codexd-su, codex-stanford, or codexd-stanford' >&2; exit 1 ;;
esac
entry="/lfs/$(hostname -s)/0/brando9/.local/bin/$node_command"
if [ ! -x "$entry" ]; then
  echo "Stanford Codex node runtime missing: run install_codex_su_node.sh on this node" >&2
  exit 1
fi
exec "$entry" "$@"
