#!/usr/bin/env bash
# Install OpenClaw on a SNAP Linux GPU node (mercury2, skampere1, …).
#
# Sibling of install_openclaw_instance.sh (macOS). Different daemon path:
# no launchd — uses tmux + @reboot cron + watchdog cron instead (per
# machine/snap.md:104-120 watcher pattern).
#
# Idempotent: run as many times as you want. Skips work that's already done.
# Driven by experiments/01_self_hosted_openclaw/snap_telegram_setup_plan.md.
#
# Usage (from the SNAP node itself):
#   bash ~/agents-config/experiments/01_self_hosted_openclaw/scripts/install_openclaw_instance_linux.sh
#
# Prerequisites the script does NOT do for you (Step 2 of the runbook):
#   - DFS scratch mounted at /dfs/scratch0/<user>
#   - ~/agents-config checked out on DFS (per machine/snap.md New Node Setup)
#   - Kerberos keytab + 4h krenew cron already installed
#   - Node 22.14+ via NVM (sourced from ~/.bashrc)
#   - codex CLI logged in (`codex login` once)
#   - ~/keys/openclaw_telegram_bot_token.txt (mode 600) — token from @BotFather
#
# What it DOES (idempotent):
#   - Symlinks ~/.openclaw → /dfs/scratch0/<user>/.openclaw (DFS-backed state)
#   - npm install -g openclaw@latest under NVM prefix
#   - Renders ~/.openclaw/openclaw.json from the shared template
#   - Generates a fresh per-host gateway.auth.token (preserved on re-runs)
#   - Installs @reboot + watchdog cron entries (preserves any existing krenew line)
#   - Launches tmux session `openclaw-gateway` immediately (no reboot needed)
#   - Smoke test: `openclaw infer model run --gateway --prompt 'PONG'`

set -euo pipefail

REPO_ROOT="${HOME}/agents-config"
EXP_DIR="${REPO_ROOT}/experiments/01_self_hosted_openclaw"
TEMPLATE="${EXP_DIR}/config/openclaw.json.template"
OPENCLAW_DIR="${HOME}/.openclaw"
TELEGRAM_TOKEN_FILE="${HOME}/keys/openclaw_telegram_bot_token.txt"
DFS_USER_ROOT="/dfs/scratch0/$(id -un)"
DFS_OPENCLAW_STATE="${DFS_USER_ROOT}/.openclaw"
REBOOT_SCRIPT="${EXP_DIR}/scripts/start_openclaw_at_reboot.sh"
WATCHDOG_SCRIPT="${EXP_DIR}/scripts/openclaw-watchdog.sh"
LOGROTATE_CONF="${EXP_DIR}/config/snap-logrotate.conf"

log() { printf '[install-linux] %s\n' "$*"; }
die() { printf '[install-linux] ERROR: %s\n' "$*" >&2; exit 1; }

[[ "$(uname -s)" == "Linux" ]] || die "this script is Linux-only — use install_openclaw_instance.sh on macOS"

# --- prereq checks ---
[[ -f "$TEMPLATE" ]] || die "config template not found at $TEMPLATE — did you 'git -C ~/agents-config pull'?"
[[ -d "$DFS_USER_ROOT" ]] || die "DFS not mounted at $DFS_USER_ROOT — 'cd /dfs/scratch0' to trigger AutoFS, then retry"
command -v node >/dev/null  || die "node not in PATH — source ~/.bashrc first (NVM loads node)"
command -v npm  >/dev/null  || die "npm not in PATH"
command -v codex >/dev/null || die "codex CLI missing — install it and run 'codex login' first"
command -v tmux >/dev/null  || die "tmux not in PATH"
[[ -f "$TELEGRAM_TOKEN_FILE" ]] || die "missing $TELEGRAM_TOKEN_FILE — create it from @BotFather token (mode 600)"
[[ "$(stat -c '%a' "$TELEGRAM_TOKEN_FILE")" == "600" ]] \
  || die "$TELEGRAM_TOKEN_FILE permissions must be 600 (currently $(stat -c '%a' "$TELEGRAM_TOKEN_FILE"))"
[[ -x "$REBOOT_SCRIPT"   ]] || die "missing executable $REBOOT_SCRIPT"
[[ -x "$WATCHDOG_SCRIPT" ]] || die "missing executable $WATCHDOG_SCRIPT"

# --- Slurm guard: warn loudly if this node is gated ---
# Heuristic: if the user can ssh in but pam_slurm_adopt is active, the @reboot
# cron will silently fail post-reboot. Better to surface it now.
if [[ -f /etc/pam.d/sshd ]] && grep -q 'pam_slurm_adopt' /etc/pam.d/sshd 2>/dev/null; then
  log "⚠ pam_slurm_adopt detected on $(hostname). Reboot survival via @reboot cron may not work."
  log "  See machine/snap.md:81-103 for the Slurm-migration table and sbatch-wrapper plan."
fi

# --- DFS-backed state dir (symlink ~/.openclaw → DFS) ---
mkdir -p "${DFS_OPENCLAW_STATE}/logs"
if [[ -L "$OPENCLAW_DIR" ]]; then
  TARGET="$(readlink -f "$OPENCLAW_DIR" || true)"
  [[ "$TARGET" == "$DFS_OPENCLAW_STATE" ]] || die "$OPENCLAW_DIR symlink points to $TARGET, not $DFS_OPENCLAW_STATE; refusing to overwrite"
  log "~/.openclaw already symlinked to DFS"
elif [[ -e "$OPENCLAW_DIR" ]]; then
  die "$OPENCLAW_DIR exists as a real dir — move it to $DFS_OPENCLAW_STATE manually, then re-run"
else
  ln -sfn "$DFS_OPENCLAW_STATE" "$OPENCLAW_DIR"
  log "symlinked ~/.openclaw → $DFS_OPENCLAW_STATE"
fi

# --- install OpenClaw if missing or out of date ---
if ! command -v openclaw >/dev/null; then
  log "installing openclaw via npm (global, under NVM prefix)"
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

# --- launch / relaunch tmux session immediately (no reboot needed for first run) ---
log "(re)launching tmux session 'openclaw-gateway'"
tmux kill-session -t openclaw-gateway 2>/dev/null || true
sleep 1
tmux new-session -d -s openclaw-gateway \
  "bash -lc 'openclaw gateway run 2>&1 | tee -a ~/.openclaw/logs/gateway-\$(date +%F).log'"
sleep 6

# --- install / refresh crontab entries (preserve krenew + anything unrelated) ---
log "installing @reboot + watchdog crontab entries (preserves krenew + foreign lines)"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT
(crontab -l 2>/dev/null || true) \
  | grep -vE "start_openclaw_at_reboot|openclaw-watchdog|openclaw/logs/.logrotate" \
  > "$TMP_CRON"
{
  printf '@reboot %s\n'                  "$REBOOT_SCRIPT"
  printf '*/2 * * * * %s\n'              "$WATCHDOG_SCRIPT"
  printf '5 4 * * * /usr/sbin/logrotate -s %s/.openclaw/logs/.logrotate.state %s\n' \
         "$DFS_USER_ROOT" "$LOGROTATE_CONF"
} >> "$TMP_CRON"
crontab "$TMP_CRON"
log "crontab now contains:"
crontab -l | grep -E "krenew|openclaw|logrotate" | sed 's/^/  /'

# --- smoke test ---
log "smoke test: openclaw infer model run --gateway --prompt 'PONG'"
if openclaw infer model run --gateway --prompt "say only the word PONG" 2>&1 | grep -q "PONG"; then
  log "✓ smoke test passed"
else
  die "smoke test failed — see 'openclaw doctor' and 'openclaw logs', and tmux attach -t openclaw-gateway"
fi

# --- finish + manual steps reminder ---
cat <<EOF

================================================================================
[install-linux] OpenClaw is up on $(hostname).

What's done:
  - openclaw $(openclaw --version 2>&1 | head -1)
  - tmux session 'openclaw-gateway' running (attach: tmux attach -t openclaw-gateway)
  - State on DFS: $DFS_OPENCLAW_STATE
  - @reboot + watchdog + logrotate cron entries installed
  - Smoke test passed

What you still need to do MANUALLY on this host (Steps 4.6, 4.7 of the runbook):
  1. Pair the bot in Telegram (DM @ultimate_brando9_sk_<host>_bot, then if prompted):
       openclaw pairing approve telegram <CODE>
  2. Register the heartbeat cron:
       openclaw cron add \\
         --id heartbeat-$(hostname -s) \\
         --cron "*/15 * * * *" \\
         --action send-channel \\
         --channel telegram --target openclaw-ops \\
         --message "[$(hostname -s)-openclaw] alive @ \\\$(date -u +%FT%TZ)"
  3. Copy gogcli auth from instance #1 (if not already done):
       scp <air>:~/Library/Application\\ Support/gogcli/credentials.json \\
           ~/.config/gogcli/credentials.json
       chmod 600 ~/.config/gogcli/credentials.json
       gog gmail list --max-results 1

Verify end-to-end:
  - tmux attach -t openclaw-gateway     # gateway logs
  - openclaw channels status            # telegram should be green
  - Within 15 min, openclaw-ops channel should show: [<host>-openclaw] alive @ ...
================================================================================
EOF
