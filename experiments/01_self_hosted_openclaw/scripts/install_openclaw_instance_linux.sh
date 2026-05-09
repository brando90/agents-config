#!/usr/bin/env bash
# Install OpenClaw on a Linux SNAP node (mercury2-style).
#
# Idempotent: re-running is safe and skips work already done.
#
# Differences vs install_openclaw_instance.sh (macOS):
#   - No launchd / launchctl / plist steps; gateway runs in a tmux session
#     respawned by ~/openclaw/run_gateway_respawn.sh.
#   - @reboot cron entry restarts the tmux session after node reboot
#     (waits for DFS, runs krenew first; mirrors machine/snap.md pattern).
#   - 5-min health-watcher cron entry installed alongside.
#   - Defaults to Anthropic Claude Haiku 4.5 backed by ~/keys/anthropic_api_key.txt
#     (the openai-codex / chatgpt OAuth path is currently flaky on Linux —
#     see notes at the bottom of this file).
#
# Prerequisites the script does NOT do for you (must be present first):
#   - Node >= 22.14 (recommend 24 via nvm; SNAP nvm dir is /dfs/scratch0/<user>/.nvm)
#   - codex CLI logged in (for Codex Pro fallback / future codex-auth wiring):
#       codex login   # interactive ChatGPT OAuth
#   - tmux on PATH
#   - ~/keys/openclaw_telegram_bot_token.txt — must be THIS host's bot token
#       (per-host bots; do NOT share across hosts — see concepts.md Q1)
#       chmod 600
#   - ~/keys/anthropic_api_key.txt — Anthropic API key for the default model
#       chmod 600
#   - Kerberos keytab + krenew.sh in /dfs/scratch0/<user>/bin/ (already standard
#     on SNAP; see machine/snap.md "How keytab reauth works")
#
# Usage:
#   bash ~/agents-config/experiments/01_self_hosted_openclaw/scripts/install_openclaw_instance_linux.sh

set -euo pipefail

REPO_ROOT="${HOME}/agents-config"
EXP_DIR="${REPO_ROOT}/experiments/01_self_hosted_openclaw"
TEMPLATE="${EXP_DIR}/config/openclaw.json.template"
OPENCLAW_DIR="${HOME}/.openclaw"
TELEGRAM_TOKEN_FILE="${HOME}/keys/openclaw_telegram_bot_token.txt"
ANTHROPIC_KEY_FILE="${HOME}/keys/anthropic_api_key.txt"
OC_WORK_DIR="${HOME}/openclaw"
TMUX_SESSION="openclaw-gateway"
RESPAWN_WRAPPER="${OC_WORK_DIR}/run_gateway_respawn.sh"
REBOOT_WRAPPER="${OC_WORK_DIR}/start_openclaw_at_reboot.sh"

log() { printf '[install-linux] %s\n' "$*"; }
die() { printf '[install-linux] ERROR: %s\n' "$*" >&2; exit 1; }

# --- prereq checks ---
[[ "$(uname -s)" == "Linux" ]] || die "this script is for Linux; use install_openclaw_instance.sh on macOS"
[[ -f "$TEMPLATE" ]]           || die "config template not found at $TEMPLATE — did you 'git -C ~/agents-config pull'?"
command -v node  >/dev/null    || die "node not in PATH (source ~/.bashrc to load nvm)"
command -v npm   >/dev/null    || die "npm not in PATH"
command -v codex >/dev/null    || die "codex CLI missing — install + run 'codex login' first"
command -v tmux  >/dev/null    || die "tmux not in PATH"
[[ -f "$TELEGRAM_TOKEN_FILE" ]] || die "missing $TELEGRAM_TOKEN_FILE — create per-host bot via @BotFather, save token here"
[[ "$(stat -c '%a' "$TELEGRAM_TOKEN_FILE")" == "600" ]] \
  || die "$TELEGRAM_TOKEN_FILE permissions must be 600"
[[ -f "$ANTHROPIC_KEY_FILE" ]]  || die "missing $ANTHROPIC_KEY_FILE — needed for default Anthropic backend"

mkdir -p "$OC_WORK_DIR"/{audit,experiments,logs}

# --- verify the Telegram token actually corresponds to a real bot ---
TOKEN=$(tr -d '\n' < "$TELEGRAM_TOKEN_FILE")
BOT_USERNAME=$(curl -s --max-time 8 "https://api.telegram.org/bot${TOKEN}/getMe" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['result']['username']) if d.get('ok') else sys.exit(1)" \
  || die "Telegram getMe failed — token at $TELEGRAM_TOKEN_FILE is invalid")
log "verified Telegram bot: @${BOT_USERNAME}"

# --- install OpenClaw npm package if missing ---
if ! command -v openclaw >/dev/null; then
  log "installing openclaw via npm (writes to nvm prefix on DFS, shared across SNAP nodes)"
  npm install -g openclaw@latest
else
  log "openclaw already installed: $(openclaw --version 2>&1 | head -1)"
fi

# --- bootstrap ~/.openclaw/openclaw.json via 'openclaw onboard' ---
if [[ ! -f "${OPENCLAW_DIR}/openclaw.json" ]]; then
  log "running 'openclaw onboard --non-interactive --accept-risk --auth-choice codex'"
  openclaw onboard --non-interactive --accept-risk --auth-choice codex --skip-health || true
fi

# --- install codex provider plugin (silent if already installed) ---
if ! openclaw plugins list 2>/dev/null | grep -q "@openclaw/codex"; then
  log "installing @openclaw/codex plugin"
  openclaw plugins install @openclaw/codex 2>&1 | tail -3
fi

# --- render config: merge template into existing config, inject tokens + keys ---
log "rendering ${OPENCLAW_DIR}/openclaw.json (preserving onboarded fields)"
TELEGRAM_TOKEN_FILE="$TELEGRAM_TOKEN_FILE" \
ANTHROPIC_KEY_FILE="$ANTHROPIC_KEY_FILE" \
TEMPLATE="$TEMPLATE" \
OPENCLAW_JSON="${OPENCLAW_DIR}/openclaw.json" \
python3 <<'PYEOF'
import json, os, secrets
from pathlib import Path

template = Path(os.environ['TEMPLATE'])
out      = Path(os.environ['OPENCLAW_JSON'])
tg_path  = Path(os.environ['TELEGRAM_TOKEN_FILE'])
ak_path  = Path(os.environ['ANTHROPIC_KEY_FILE'])

cfg = json.loads(template.read_text())
existing = {}
if out.exists():
    try: existing = json.loads(out.read_text())
    except Exception: pass

merged = dict(existing)

# Plugins from template
merged["plugins"] = cfg.get("plugins", {})

# Channels from template
merged.setdefault("channels", {})
merged["channels"]["telegram"] = cfg.get("channels", {}).get("telegram", {"enabled": True})

# Agents.defaults: keep existing workspace, take model + harness from template
# but pin to anthropic/claude-haiku-4-5 for Linux (known-working path)
merged.setdefault("agents", {}).setdefault("defaults", {})
template_defaults = cfg.get("agents", {}).get("defaults", {})
for k, v in template_defaults.items():
    merged["agents"]["defaults"][k] = v
# Override the model to anthropic on Linux
merged["agents"]["defaults"]["model"] = {"primary": "anthropic/claude-haiku-4-5"}
# Drop embeddedHarness on Linux — codex chatgpt-OAuth flow is flaky here
merged["agents"]["defaults"].pop("embeddedHarness", None)

# Gateway: keep existing token, ensure mode/bind/auth
merged.setdefault("gateway", {})
merged["gateway"].setdefault("mode", "local")
merged["gateway"].setdefault("bind", "loopback")
merged["gateway"].setdefault("auth", {})
merged["gateway"]["auth"].setdefault("mode", "token")
merged["gateway"]["auth"].setdefault("token", secrets.token_hex(32))

# Telegram bot token from ~/keys/
merged["channels"]["telegram"]["enabled"] = True
merged["channels"]["telegram"]["botToken"] = tg_path.read_text().strip()
merged["channels"]["telegram"].pop("_comment", None)

# Anthropic API key in env.vars (via shellEnvFallback path)
merged.setdefault("env", {})
merged["env"].setdefault("shellEnv", {"enabled": True})
merged["env"].setdefault("vars", {})
merged["env"]["vars"]["ANTHROPIC_API_KEY"] = ak_path.read_text().strip()

out.write_text(json.dumps(merged, indent=2) + "\n")
out.chmod(0o600)
print(f"wrote {out} (mode 600)")
PYEOF

# --- write the respawn wrapper ---
log "writing respawn wrapper to $RESPAWN_WRAPPER"
cat > "$RESPAWN_WRAPPER" <<'EOF'
#!/usr/bin/env bash
# Respawn wrapper: keep openclaw gateway alive in this tmux session.
# Crashes get auto-restarted with backoff. Logs to ~/openclaw/gateway.log.
set -u
LOG="$HOME/openclaw/gateway.log"
echo "[$(date '+%F %T')] respawn wrapper starting on $(hostname -s)" >> "$LOG"
while true; do
  echo "[$(date '+%F %T')] launching openclaw gateway run" >> "$LOG"
  openclaw gateway run --force 2>&1 | tee -a "$LOG"
  rc=$?
  echo "[$(date '+%F %T')] gateway exited rc=$rc; sleeping 5s before respawn" >> "$LOG"
  sleep 5
done
EOF
chmod 755 "$RESPAWN_WRAPPER"

# --- write the @reboot wrapper ---
log "writing @reboot wrapper to $REBOOT_WRAPPER"
cat > "$REBOOT_WRAPPER" <<'EOF'
#!/usr/bin/env bash
# @reboot wrapper: relaunch openclaw gateway in tmux after a node reboot.
# Pattern mirrors /dfs/scratch0/brando9/bin/start_watcher_at_reboot.sh.
set -u
LOG="$HOME/openclaw/start_at_reboot.log"
log() { echo "[$(date '+%F %T')] $*" >> "$LOG"; }
log "boot wrapper starting on $(hostname -s)"

# Wait for DFS to come up (up to 5 min)
for _ in $(seq 1 60); do
  [ -d /dfs/scratch0/brando9 ] && break
  sleep 5
done
log "DFS check complete"

# Renew Kerberos via keytab
if [ -x /dfs/scratch0/brando9/bin/krenew.sh ]; then
  /dfs/scratch0/brando9/bin/krenew.sh >> "$LOG" 2>&1 || true
fi

# Source bashrc so nvm + PATH are loaded
if [ -f "$HOME/.bashrc" ]; then
  # shellcheck disable=SC1091
  . "$HOME/.bashrc" >/dev/null 2>&1 || true
fi

if tmux has-session -t openclaw-gateway 2>/dev/null; then
  log "openclaw-gateway tmux session already exists — no relaunch needed"
else
  log "launching openclaw-gateway tmux session"
  tmux new-session -d -s openclaw-gateway "bash -lc '$HOME/openclaw/run_gateway_respawn.sh'"
fi
log "boot wrapper done"
EOF
chmod 755 "$REBOOT_WRAPPER"

# --- launch gateway in tmux (idempotent) ---
if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
  log "tmux session '$TMUX_SESSION' already running"
else
  log "launching gateway in tmux session '$TMUX_SESSION'"
  tmux new-session -d -s "$TMUX_SESSION" "bash -lc '$RESPAWN_WRAPPER'"
fi

# --- install/refresh cron entries (idempotent) ---
log "installing cron entries (@reboot relaunch + 5-min health watcher)"
TMP=$(mktemp)
crontab -l 2>/dev/null \
  | grep -v "start_openclaw_at_reboot" \
  | grep -v "openclaw-health-watcher" \
  > "$TMP" || true
{
  cat "$TMP"
  echo "@reboot $REBOOT_WRAPPER"
  echo "*/5 * * * * bash \$HOME/agents-config/experiments/01_self_hosted_openclaw/scripts/openclaw-health-watcher.sh >> \$HOME/openclaw/watcher.log 2>&1"
} | crontab -
rm -f "$TMP"

# --- wait for gateway to come up + smoke test ---
log "waiting up to 90s for gateway to be ready"
SMOKE_OK=0
for _ in $(seq 1 18); do
  if curl -s --max-time 4 http://127.0.0.1:18789/health 2>/dev/null | grep -q '"status":"live"'; then
    if openclaw infer model run --gateway --prompt "say only the word PONG" 2>/dev/null | grep -q "PONG"; then
      SMOKE_OK=1
      break
    fi
  fi
  sleep 5
done

if [ "$SMOKE_OK" != "1" ]; then
  log "smoke test FAILED — see ~/openclaw/gateway.log + 'openclaw doctor'"
  exit 1
fi
log "✓ smoke test passed (PONG via gateway+anthropic)"

# --- finish + manual steps reminder ---
cat <<EOF

================================================================================
[install-linux] OpenClaw is up on $(hostname).

What's done:
  - openclaw $(openclaw --version 2>&1 | head -1)
  - gateway running in tmux session: $TMUX_SESSION
  - respawn wrapper: $RESPAWN_WRAPPER
  - @reboot cron entry: $REBOOT_WRAPPER
  - 5-min health-watcher cron entry
  - Telegram channel wired to @${BOT_USERNAME}
  - default model: anthropic/claude-haiku-4-5 (via env.vars.ANTHROPIC_API_KEY)

Still TODO manually on this host (one-time):
  1. Open Telegram, /start the bot @${BOT_USERNAME}, complete pairing if prompted:
       openclaw pairing approve telegram <CODE>
  2. (Optional) Wire Gmail (browser OAuth) on a Mac, then scp:
       scp <mac>:~/.openclaw/agents/main/agent/auth-profiles.json \\
           ~/.openclaw/agents/main/agent/auth-profiles.json
  3. Verify: openclaw channels status   (should show 'running, connected')

Operational:
  - Tail logs:    tail -f ~/openclaw/gateway.log
  - Watcher log:  tail -f ~/openclaw/watcher.log
  - Health:       curl -s http://127.0.0.1:18789/health
  - Restart:      tmux kill-session -t $TMUX_SESSION  (respawn wrapper rebuilds)

Known gotcha:
  The openai-codex / ChatGPT-OAuth flow ('--auth-choice openai-codex') currently
  requires interactive TTY. Linux installer defaults to anthropic. Fix-forward:
  re-run 'openclaw configure --section model' interactively if you want codex,
  or wait for an upstream non-interactive option.
================================================================================
EOF
