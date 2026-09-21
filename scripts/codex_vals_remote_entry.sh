#!/usr/bin/env bash
# TLDR: Dispatch shared codex-vals names to the node-local Vals Codex wrappers.
set -euo pipefail
command_name=$(basename "$0")
case "$command_name" in codex-vals|codexd-vals) ;; *) exit 1;; esac
entry="/lfs/$(hostname -s)/0/brando9/.local/bin/$command_name"
[ -x "$entry" ] || { echo 'Vals Codex node runtime missing' >&2; exit 1; }
exec "$entry" "$@"
