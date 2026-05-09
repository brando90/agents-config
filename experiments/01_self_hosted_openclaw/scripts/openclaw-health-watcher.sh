#!/usr/bin/env bash
# openclaw-health-watcher.sh
#
# Self-healing liveness check for the OpenClaw gateway on this host.
#
# Cross-platform: macOS uses launchd, Linux uses tmux+respawn wrapper
# (see machine/snap.md and start_openclaw_at_reboot.sh).
#
# Three checks; if any fails it escalates: restart → full reset (clear
# plugin-runtime-deps cache + reload) → DM Brando via openclaw-ops if even
# the full reset doesn't recover.
#
# Schedule every 5 minutes:
#
#   # macOS launchd: see install instructions at the bottom of this file.
#   # Linux cron:
#   */5 * * * *  bash ~/agents-config/experiments/01_self_hosted_openclaw/scripts/openclaw-health-watcher.sh >> ~/openclaw/watcher.log 2>&1
#
# Exits 0 if healthy or self-healed; 1 if it gave up.

set -u

HOST_SHORT="${HOSTNAME:-$(hostname 2>/dev/null || printf unknown)}"
HOST_SHORT="${HOST_SHORT%%.*}"
LOG_PREFIX="$(date '+%F %T') openclaw-watcher [${HOST_SHORT}]"
HOST_TAG="${OPENCLAW_HOST:-${HOST_SHORT}}"
PLAT="$(uname -s)"
TMUX_SESSION="openclaw-gateway"

log() { echo "$LOG_PREFIX $*"; }

# Source bashrc on Linux so nvm + PATH are available under cron
if [ "$PLAT" = "Linux" ] && [ -f "$HOME/.bashrc" ]; then
  # shellcheck disable=SC1091
  . "$HOME/.bashrc" >/dev/null 2>&1 || true
fi

RESPAWN_WRAPPER="$HOME/openclaw/run_gateway_respawn.sh"

run_with_timeout() {
  local seconds="$1"
  shift
  if command -v timeout >/dev/null 2>&1; then
    timeout "$seconds" "$@"
  elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$seconds" "$@"
  else
    "$@"
  fi
}

is_gateway_alive() {
  case "$PLAT" in
    Darwin) launchctl list 2>/dev/null | grep -q ai.openclaw.gateway ;;
    Linux)  command -v tmux >/dev/null 2>&1 && tmux has-session -t "$TMUX_SESSION" 2>/dev/null ;;
    *)      return 1 ;;
  esac
}

start_gateway() {
  case "$PLAT" in
    Darwin)
      launchctl load "$HOME/Library/LaunchAgents/ai.openclaw.gateway.plist" 2>&1 | sed "s/^/$LOG_PREFIX /"
      ;;
    Linux)
      if ! command -v tmux >/dev/null 2>&1; then
        log "ERROR: tmux not in PATH — cannot start gateway"
        return 1
      fi
      if [ -x "$RESPAWN_WRAPPER" ]; then
        tmux new-session -d -s "$TMUX_SESSION" "bash -lc '$RESPAWN_WRAPPER'"
      else
        log "ERROR: $RESPAWN_WRAPPER missing — cannot start gateway"
        return 1
      fi
      ;;
    *)
      log "ERROR: unsupported platform $PLAT"
      return 1
      ;;
  esac
}

restart_gateway() {
  case "$PLAT" in
    Darwin)
      openclaw gateway restart >/dev/null 2>&1 || true
      ;;
    Linux)
      # Kill the inner gateway process; respawn wrapper will relaunch within ~5s.
      pkill -f 'openclaw gateway run' 2>/dev/null || true
      ;;
    *)
      return 1
      ;;
  esac
}

full_reset() {
  case "$PLAT" in
    Darwin)
      launchctl unload "$HOME/Library/LaunchAgents/ai.openclaw.gateway.plist" 2>/dev/null || true
      pkill -f 'openclaw gateway run' 2>/dev/null || true
      sleep 3
      rm -rf "$HOME/.openclaw/plugin-runtime-deps"
      launchctl load "$HOME/Library/LaunchAgents/ai.openclaw.gateway.plist"
      ;;
    Linux)
      tmux kill-session -t "$TMUX_SESSION" 2>/dev/null || true
      pkill -f 'openclaw gateway run' 2>/dev/null || true
      sleep 3
      rm -rf "$HOME/.openclaw/plugin-runtime-deps"
      start_gateway
      ;;
    *)
      return 1
      ;;
  esac
}

channels_connected() {
  run_with_timeout 12 openclaw channels status 2>/dev/null \
    | grep -q "Telegram default:.*running.*connected"
}

# 1. Is the gateway daemon/session running?
if ! is_gateway_alive; then
  log "FAIL: gateway not running — starting"
  start_gateway
  sleep 30
fi

# 2. Channels status — must show Telegram running+connected
if ! channels_connected; then
  log "FAIL: telegram channel not running+connected — restarting gateway"
  restart_gateway
  sleep 30

  # Recheck
  if ! channels_connected; then
    log "FAIL: still not connected after restart — running full reset (clear plugin cache)"
    full_reset
    log "full reset issued; waiting up to 5 min for plugin reinstall"
    for _ in $(seq 1 60); do
      sleep 5
      if channels_connected; then
        log "OK: telegram recovered after full reset"
        break
      fi
    done
  fi
fi

# 3. Final liveness — channels OK + PONG round-trip
if channels_connected \
  && run_with_timeout 60 openclaw infer model run --gateway --prompt "say only the word PONG" 2>/dev/null \
    | grep -q "PONG"; then
  log "HEALTHY: gateway+telegram+model round-trip OK"
  exit 0
fi

# Couldn't recover — escalate
log "GIVE-UP: still unhealthy after restart + full reset"

# Try to DM the ops channel if at least the gateway is up
openclaw message send \
  --channel telegram \
  --target "openclaw-ops" \
  --message "🚨 [${HOST_TAG}] watcher could not recover gateway — Brando, please check ~/openclaw/watcher.log" \
  >/dev/null 2>&1 || true

exit 1

# ─── Install as a launchd job on macOS (5-min interval) ──────────────────────
#
# cat > ~/Library/LaunchAgents/ai.openclaw.health-watcher.plist <<'PLIST'
# <?xml version="1.0" encoding="UTF-8"?>
# <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
#  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
# <plist version="1.0">
# <dict>
#   <key>Label</key><string>ai.openclaw.health-watcher</string>
#   <key>ProgramArguments</key>
#   <array>
#     <string>/bin/bash</string>
#     <string>-lc</string>
#     <string>$HOME/agents-config/experiments/01_self_hosted_openclaw/scripts/openclaw-health-watcher.sh &gt;&gt; $HOME/openclaw/watcher.log 2&gt;&amp;1</string>
#   </array>
#   <key>StartInterval</key><integer>300</integer>
#   <key>RunAtLoad</key><true/>
# </dict>
# </plist>
# PLIST
# launchctl load ~/Library/LaunchAgents/ai.openclaw.health-watcher.plist
#
# Verify: tail -f ~/openclaw/watcher.log
#
# ─── Linux (mercury2 / SNAP) — tmux + cron pattern ──────────────────────────
# Requires a respawn wrapper at ~/openclaw/run_gateway_respawn.sh that runs
# `openclaw gateway run` in a while-true loop (created by
# install_openclaw_instance_linux.sh). Add to user crontab:
#   */5 * * * * bash ~/agents-config/experiments/01_self_hosted_openclaw/scripts/openclaw-health-watcher.sh >> ~/openclaw/watcher.log 2>&1
