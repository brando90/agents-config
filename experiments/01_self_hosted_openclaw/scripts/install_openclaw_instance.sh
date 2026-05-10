#!/usr/bin/env bash
# Install OpenClaw on a fresh machine (macOS or Linux).
#
# Idempotent: run as many times as you want. Skips work that's already done.
#
# Usage:
#   bash ~/agents-config/experiments/01_self_hosted_openclaw/scripts/install_openclaw_instance.sh
#
# Prerequisites the script does NOT do for you (must be present first):
#   - Node 22.14+ (recommend 24)
#   - codex CLI logged in to your ChatGPT/Codex Pro account (run `codex login` once)
#   - ~/keys/openclaw_telegram_bot_token.txt (mode 600, scp'd from instance #1)
#   - For Gmail: you'll do the OAuth in a browser via this script's last step
#
# What it DOES:
#   - macOS-only: writes ~/.npmrc cafile=/etc/ssl/cert.pem if missing (fixes Homebrew Node SSL)
#   - npm install -g openclaw@latest (skips if already current version)
#   - Renders ~/.openclaw/openclaw.json from the template in agents-config
#   - Generates a fresh per-machine gateway.auth.token
#   - Wires Telegram channel from the token file
#   - Installs the launchd/systemd-user daemon
#   - Prints next steps for wiring Gmail/Calendar/Drive via the `gog` skill (gogcli),
#     since Gmail is NOT a stock OpenClaw channel — see MASTER_PLAN.md §"Gmail / Calendar / Drive via gog skill"

set -euo pipefail

REPO_ROOT="${HOME}/agents-config"
EXP_DIR="${REPO_ROOT}/experiments/01_self_hosted_openclaw"
TEMPLATE="${EXP_DIR}/config/openclaw.json.template"
OPENCLAW_DIR="${HOME}/.openclaw"
TELEGRAM_TOKEN_FILE="${HOME}/keys/openclaw_telegram_bot_token.txt"

log() { printf '[install] %s\n' "$*"; }
die() { printf '[install] ERROR: %s\n' "$*" >&2; exit 1; }

# --- prereq checks ---
[[ -f "$TEMPLATE" ]] || die "config template not found at $TEMPLATE — did you 'git -C ~/agents-config pull'?"
command -v node >/dev/null   || die "node not in PATH"
command -v npm  >/dev/null   || die "npm not in PATH"
command -v codex >/dev/null  || die "codex CLI missing — install it and run 'codex login' first"
[[ -f "$TELEGRAM_TOKEN_FILE" ]] || die "missing $TELEGRAM_TOKEN_FILE (scp it from instance #1)"
[[ "$(stat -f '%Lp' "$TELEGRAM_TOKEN_FILE" 2>/dev/null || stat -c '%a' "$TELEGRAM_TOKEN_FILE")" == "600" ]] \
  || die "$TELEGRAM_TOKEN_FILE permissions must be 600"

# --- macOS Homebrew Node SSL fix ---
if [[ "$(uname -s)" == "Darwin" ]] && [[ ! -f "${HOME}/.npmrc" ]]; then
  log "writing ~/.npmrc cafile fix (macOS Homebrew Node)"
  echo "cafile=/etc/ssl/cert.pem" > "${HOME}/.npmrc"
fi

# --- install OpenClaw if missing or out of date ---
if ! command -v openclaw >/dev/null; then
  log "installing openclaw via npm (global)"
  npm install -g openclaw@latest
else
  log "openclaw already installed: $(openclaw --version 2>&1 | head -1)"
fi

# --- bootstrap ~/.openclaw via onboard (idempotent if already done) ---
if [[ ! -f "${OPENCLAW_DIR}/openclaw.json" ]]; then
  log "running 'openclaw onboard --non-interactive --accept-risk' to bootstrap config dir"
  openclaw onboard --non-interactive --accept-risk || true
fi

# --- render config from template (preserve existing per-host token if present) ---
mkdir -p "${OPENCLAW_DIR}"
log "rendering ${OPENCLAW_DIR}/openclaw.json from template"
python3 - <<'PYEOF'
import json, os, secrets
from pathlib import Path

template_path = Path(os.environ['HOME']) / "agents-config/experiments/01_self_hosted_openclaw/config/openclaw.json.template"
out_path      = Path(os.environ['HOME']) / ".openclaw/openclaw.json"
token_path    = Path(os.environ['HOME']) / "keys/openclaw_telegram_bot_token.txt"

cfg = json.loads(template_path.read_text())

# Preserve existing per-host gateway token if already set; otherwise generate fresh.
existing = {}
if out_path.exists():
    try:
        existing = json.loads(out_path.read_text())
    except Exception:
        pass

existing_token = (
    existing.get("gateway", {}).get("auth", {}).get("token")
    or secrets.token_hex(32)
)
cfg.setdefault("gateway", {}).setdefault("auth", {})["mode"] = "token"
cfg["gateway"]["auth"]["token"] = existing_token

# Inject Telegram bot token from ~/keys/ (never commit the literal value)
bot_token = token_path.read_text().strip()
cfg.setdefault("channels", {}).setdefault("telegram", {})
cfg["channels"]["telegram"]["enabled"] = True
cfg["channels"]["telegram"]["botToken"] = bot_token
cfg["channels"]["telegram"].pop("_comment", None)

out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(cfg, indent=2) + "\n")
out_path.chmod(0o600)
print(f"wrote {out_path} (mode 600, gateway token {'preserved' if existing.get('gateway') else 'generated'})")
PYEOF

# --- force tools.profile = messaging (chat replies silently fail with "coding") ---
# The default "coding" profile bundles image_gen + web_search, which require
# reasoning>=low. The Telegram auto-reply path invokes the agent at minimal
# reasoning, so every incoming message hits OpenAI HTTP 400 and dies silently.
# See runbook.md "When the bot doesn't reply" #3 for the failure signature.
log "setting tools.profile=messaging (required for Telegram chat replies to work)"
openclaw config set tools.profile messaging 2>&1 | tail -2 || true

# --- patch broken nativeHookRelay (blocks ALL shell tools) ---
# Upstream codex extension registers a relay then loses lookup at PreToolUse
# time ("native hook relay not found"). 1-line patch disables the hook chain;
# codex falls back to its own sandbox/approval (already yolo+danger-full-access
# in ~/.codex/config.toml). Idempotent: skips if already patched. Re-applies
# after any `npm install -g openclaw@latest` that overwrites node_modules.
# Full background: runbook.md "Shell exec — local patch required".
HARNESS_JS="$(npm root -g)/openclaw/dist/extensions/codex/harness.js"
if [[ -f "$HARNESS_JS" ]]; then
  if grep -q 'OPENCLAW LOCAL PATCH' "$HARNESS_JS"; then
    log "harness.js already patched (nativeHookRelay disabled) — skipping"
  else
    log "patching $HARNESS_JS to disable broken nativeHookRelay"
    cp -n "$HARNESS_JS" "${HARNESS_JS}.bak.preopenclawpatch"
    python3 - "$HARNESS_JS" <<'PYEOF'
import sys
path = sys.argv[1]
src = open(path).read()
needle = 'return runCodexAppServerAttempt(params, { pluginConfig: options?.pluginConfig });'
patch = (
    '// OPENCLAW LOCAL PATCH (runbook.md "Shell exec — local patch required"):\n'
    '\t\t\t// disable broken nativeHookRelay so codex falls back to its own sandbox/approval.\n'
    '\t\t\treturn runCodexAppServerAttempt(params, { pluginConfig: options?.pluginConfig, nativeHookRelay: { enabled: false } });'
)
if needle not in src:
    print(f"[install] WARN: patch needle not found in {path}; upstream may have changed — skipping", file=sys.stderr)
    sys.exit(0)
open(path, 'w').write(src.replace(needle, patch, 1))
print(f"[install] patched {path}")
PYEOF
  fi
else
  log "WARN: $HARNESS_JS not found — skipping shell-exec patch"
fi

# --- install + start daemon ---
log "installing daemon (launchd on macOS / systemd-user on Linux)"
openclaw onboard --install-daemon --non-interactive --accept-risk 2>&1 | tail -5 || true
sleep 4

# --- macOS-only: patch the launchd plist with the env vars OpenClaw needs ---
if [[ "$(uname -s)" == "Darwin" ]]; then
  PLIST="${HOME}/Library/LaunchAgents/ai.openclaw.gateway.plist"
  if [[ -f "$PLIST" ]]; then
    log "patching launchd plist with NODE_EXTRA_CA_CERTS + IPv4-first DNS"
    python3 - <<PYEOF
import plistlib
p = plistlib.loads(open("$PLIST", "rb").read())
env = p.setdefault("EnvironmentVariables", {})
env["NODE_EXTRA_CA_CERTS"] = "/etc/ssl/cert.pem"
env["NODE_OPTIONS"] = "--dns-result-order=ipv4first --use-system-ca"
open("$PLIST", "wb").write(plistlib.dumps(p))
PYEOF
    launchctl bootout "gui/$(id -u)/ai.openclaw.gateway" 2>/dev/null || true
    sleep 2
    launchctl bootstrap "gui/$(id -u)" "$PLIST"
    sleep 6
  fi
fi

# --- smoke test ---
log "smoke test: openclaw infer model run --gateway --prompt 'PONG'"
if openclaw infer model run --gateway --prompt "say only the word PONG" 2>&1 | grep -q "PONG"; then
  log "✓ smoke test passed"
else
  die "smoke test failed — see 'openclaw doctor' and 'openclaw logs'"
fi

# --- finish + manual steps reminder ---
cat <<EOF

================================================================================
[install] OpenClaw is up on this host.

What's done:
  - openclaw $(openclaw --version 2>&1 | head -1)
  - daemon running (gateway port 18789)
  - Telegram channel wired

What you still need to do MANUALLY on this host:
  1. Open Telegram, /start the bot. The agent's auto-reply will issue a
     pairing code; approve it with:
       openclaw pairing list --channel telegram          # find <CODE>
       openclaw pairing approve --channel telegram <CODE>
  2. Wire Gmail / Calendar / Drive via the bundled \`gog\` skill (NOT
     \`openclaw channels add --channel google\` — that channel is Google Chat,
     not Gmail; see MASTER_PLAN.md §"Gmail ... via gog skill"):
       brew install gogcli
       gog auth credentials set ~/keys/client_secret_*.apps.googleusercontent.com.json
       gog auth add YOUR_GOOGLE_EMAIL@gmail.com    # browser OAuth, once
       openclaw skills info gog                     # expect: "✓ Ready"
  3. (If this is instance #2 or #3) scp the gog OAuth tokens from instance #1
     to skip the browser OAuth dance:
       # macOS source/destination:
       scp -r instance-1:'~/Library/Application\\ Support/gogcli/' \\
              ~/Library/Application\\ Support/gogcli/
       # Linux destination uses ~/.config/gogcli/ instead.

When done, verify with:
  openclaw channels status                           # telegram connected
  openclaw skills info gog                           # ✓ Ready
  gog -a YOUR_EMAIL@gmail.com gmail list "is:unread" --max 1 -p

Recurring ops (token swap, restart, "bot won't reply" triage) are documented
in: experiments/01_self_hosted_openclaw/runbook.md
================================================================================
EOF
