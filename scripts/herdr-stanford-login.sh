#!/usr/bin/env bash
# Establish ordinary Stanford SSH masters; no secrets are stored by this script.
# Herdr uses its own managed socket: this is not Herdr reachability verification.
set -euo pipefail
if [[ ! -t 0 ]]; then
  echo 'Run this in an interactive Mac terminal so Stanford can request password/Duo.' >&2
  exit 2
fi
for host in "$@"; do
  case "$host" in sherlock|farmshare) ;; *) echo "Unsupported host: $host" >&2; exit 2;; esac
done
if [[ $# == 0 ]]; then set -- sherlock farmshare; fi
for host in "$@"; do
  printf '\n=== %s: Stanford login (password/Duo stay in SSH) ===\n' "$host"
  if ! ssh -O check "$host" 2>/dev/null; then
    ssh -MNf "$host"
  fi
  ssh -o BatchMode=yes "$host" 'hostname; id -un'
done
printf '\nSSH login verified. Return to the agent to finish scheduler placement and Herdr verification.\n'
