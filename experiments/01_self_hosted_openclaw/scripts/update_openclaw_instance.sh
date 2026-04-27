#!/usr/bin/env bash
# Pull the latest config from agents-config and re-apply on this host.
#
# Use this when you've edited openclaw.json.template, agent-prompt.md,
# or admin-filter.txt on one host and want to propagate to the others.
#
# Usage:
#   bash ~/agents-config/experiments/01_self_hosted_openclaw/scripts/update_openclaw_instance.sh

set -euo pipefail

log() { printf '[update] %s\n' "$*"; }

REPO_ROOT="${HOME}/agents-config"
EXP_DIR="${REPO_ROOT}/experiments/01_self_hosted_openclaw"

log "git pull agents-config"
git -C "$REPO_ROOT" pull --ff-only

log "re-running install script (idempotent — preserves per-host gateway token)"
bash "${EXP_DIR}/scripts/install_openclaw_instance.sh"

log "restarting gateway to pick up any config changes"
openclaw gateway restart 2>&1 | tail -3 || true
sleep 4

log "verifying smoke test still passes"
if openclaw infer model run --gateway --prompt "say only the word PONG" 2>&1 | grep -q "PONG"; then
  log "✓ post-update smoke test passed"
else
  log "⚠ post-update smoke test FAILED — check 'openclaw doctor' and 'openclaw logs'" >&2
  exit 1
fi
