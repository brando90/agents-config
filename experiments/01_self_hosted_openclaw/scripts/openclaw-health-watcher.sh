#!/usr/bin/env bash
# openclaw-health-watcher.sh
#
# Self-healing liveness check for the OpenClaw gateway on this host.
#
# Runs three checks; if any fails it escalates: restart → full reset (clear
# plugin-runtime-deps cache + reload) → DM Brando via openclaw-ops if even
# the full reset doesn't recover.
#
# Schedule via launchd (preferred on macOS) or cron, every 5 minutes:
#
#   # launchd plist (~/Library/LaunchAgents/ai.openclaw.health-watcher.plist) —
#   # see install instructions at the bottom of this file.
#
#   # OR cron:
#   */5 * * * *  /Users/sanmikoyejo-mba-1/agents-config/experiments/01_self_hosted_openclaw/scripts/openclaw-health-watcher.sh >> ~/openclaw/watcher.log 2>&1
#
# Exits 0 if healthy or self-healed; 1 if it gave up.

set -u

LOG_PREFIX="$(date '+%F %T') openclaw-watcher [${HOSTNAME%%.*}]"
HOST_TAG="${OPENCLAW_HOST:-${HOSTNAME%%.*}}"

log() { echo "$LOG_PREFIX $*"; }

# 1. Is the gateway daemon running?
if ! launchctl list 2>/dev/null | grep -q ai.openclaw.gateway; then
  log "FAIL: gateway not in launchctl list — loading"
  launchctl load ~/Library/LaunchAgents/ai.openclaw.gateway.plist 2>&1 | sed "s/^/$LOG_PREFIX /"
  sleep 30
fi

# 2. Channels status — must show Telegram running+connected
if ! timeout 12 openclaw channels status 2>/dev/null | grep -q "Telegram default:.*running.*connected"; then
  log "FAIL: telegram channel not running+connected — restarting gateway"
  openclaw gateway restart >/dev/null 2>&1 || true
  sleep 30

  # Recheck
  if ! timeout 12 openclaw channels status 2>/dev/null | grep -q "Telegram default:.*running.*connected"; then
    log "FAIL: still not connected after restart — running full reset (clear plugin cache)"
    launchctl unload ~/Library/LaunchAgents/ai.openclaw.gateway.plist 2>/dev/null || true
    pkill -f openclaw 2>/dev/null || true
    sleep 3
    # rm -rf can fail with "Directory not empty" when openclaw-node is
    # still racing to recreate files. Fall back to mv-aside (works even
    # when rm fails); a broken-aside dir is harmless and gets garbage-
    # collected later.
    if ! rm -rf ~/.openclaw/plugin-runtime-deps 2>/dev/null; then
      log "WARN: rm failed; mv-aside fallback"
      mv ~/.openclaw/plugin-runtime-deps "$HOME/.openclaw/plugin-runtime-deps.broken.$(date +%s)" 2>/dev/null \
        || log "WARN: mv-aside also failed; gateway boot may still fail"
    fi
    launchctl load ~/Library/LaunchAgents/ai.openclaw.gateway.plist
    log "full reset issued; waiting up to 5 min for plugin reinstall"
    for _ in $(seq 1 60); do
      sleep 5
      if timeout 8 openclaw channels status 2>/dev/null | grep -q "Telegram default:.*running.*connected"; then
        log "OK: telegram recovered after full reset"
        break
      fi
    done
  fi
fi

# 3. Final liveness — channels OK + PONG round-trip
if timeout 30 openclaw infer model run --gateway --prompt "PONG" 2>/dev/null | grep -q "PONG"; then
  log "HEALTHY: gateway+telegram+codex round-trip OK"
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

# ─── Install as a launchd job (5-min interval) ──────────────────────────────
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
# ─── Linux (mercury2) — tmux + cron pattern from machine/snap.md ────────────
# Add to user crontab:
#   */5 * * * * bash ~/agents-config/experiments/01_self_hosted_openclaw/scripts/openclaw-health-watcher.sh >> ~/openclaw/watcher.log 2>&1
