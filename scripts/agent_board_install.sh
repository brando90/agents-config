#!/usr/bin/env bash
# TLDR: Installs the agent board on a Mac from this repo: two launchd jobs (HTML render every 20s,
# AI summaries every 5 min), the `board` / `board-open` zsh aliases, and the SessionStart hook in
# every Claude Code config dir — idempotent, so re-running after a `git pull` is safe.
# Usage: bash ~/agents-config/scripts/agent_board_install.sh [--dry-run]
set -euo pipefail

DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1
SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOARD="$SCRIPTS/agent_board.py"
HOOK="$SCRIPTS/agent_session_register.sh"
PY="$(command -v python3 || echo /usr/bin/python3)"
AGENTS="$HOME/Library/LaunchAgents"
LOGDIR="$HOME/.agent-board"
PATHS="/opt/homebrew/bin:$HOME/homebrew/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

say() { printf '%s\n' "$*"; }
run() { if [ "$DRY" = 1 ]; then say "  [dry-run] $*"; else "$@"; fi; }

[ "$(uname)" = "Darwin" ] || { say "launchd install is macOS-only (SNAP nodes are polled from the Mac, they need nothing)"; exit 0; }
[ -f "$BOARD" ] || { say "missing $BOARD"; exit 1; }
mkdir -p "$LOGDIR" "$AGENTS"

# ---- launchd jobs -------------------------------------------------------------------------
write_plist() {  # label, interval, run-at-load, err-log, args...
  local label="$1" interval="$2" atload="$3" err="$4"; shift 4
  local plist="$AGENTS/$label.plist" args=""
  for a in "$@"; do args+="    <string>$a</string>"$'\n'; done
  local body
  body=$(cat <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key><array>
    <string>$PY</string>
    <string>$BOARD</string>
$args  </array>
  <key>StartInterval</key><integer>$interval</integer>
  <key>RunAtLoad</key><$atload/>
  <key>StandardErrorPath</key><string>$err</string>
  <key>EnvironmentVariables</key><dict>
    <key>HOME</key><string>$HOME</string>
    <key>PATH</key><string>$PATHS</string>
  </dict>
</dict></plist>
EOF
)
  if [ "$DRY" = 1 ]; then
    say "  [dry-run] would write $plist and (re)load it"
    return
  fi
  printf '%s\n' "$body" > "$plist"
  plutil -lint "$plist" >/dev/null
  launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$plist"
  say "  loaded $label (every ${interval}s)"
}

say "launchd:"
write_plist com.brando.agentboard 20 true "$LOGDIR/agentboard.err" --html --snap --quiet
write_plist com.brando.agentboard.summarize 300 false "$LOGDIR/agentboard.summarize.err" \
  --summarize --summarize-limit 6 --quiet

# ---- zsh aliases --------------------------------------------------------------------------
say "zsh aliases:"
if grep -q '# >>> agent board >>>' "$HOME/.zshrc" 2>/dev/null; then
  say "  already in ~/.zshrc"
else
  block=$(cat <<'EOF'

# >>> agent board >>>
# Terminal view of every live Claude/Codex session; the HTML board is regenerated every
# 20s by the launchd job com.brando.agentboard and lives at ~/.agent-board/board.html
alias board="python3 ~/agents-config/scripts/agent_board.py --hours 24"
alias board-open="open file://$HOME/.agent-board/board.html"
# <<< agent board <<<
EOF
)
  if [ "$DRY" = 1 ]; then say "  [dry-run] would append the alias block to ~/.zshrc"; else printf '%s\n' "$block" >> "$HOME/.zshrc"; say "  appended to ~/.zshrc"; fi
fi

# ---- SessionStart hook in every Claude Code config dir -------------------------------------
say "SessionStart hook:"
for cfg in "$HOME/.claude" "$HOME/.claude-vals"; do
  [ -d "$cfg" ] || continue
  settings="$cfg/settings.json"
  [ -f "$settings" ] || echo '{}' > "$settings"
  "$PY" - "$settings" "$HOOK" "$DRY" <<'PY'
import json, os, shutil, sys, time
path, hook, dry = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
short = "~/agents-config/scripts/" + os.path.basename(hook)
cmd = "bash " + short
try:
    d = json.load(open(path))
except Exception as e:
    print(f"  {path}: cannot parse ({e}); add the hook by hand: {cmd}")
    sys.exit(0)
groups = d.setdefault("hooks", {}).setdefault("SessionStart", [])
present = any(os.path.basename(hook) in (h.get("command") or "")
              for g in groups if isinstance(g, dict) for h in g.get("hooks", []) if isinstance(h, dict))
if present:
    print(f"  {path}: already registered")
elif dry:
    print(f"  [dry-run] would add {cmd!r} to {path}")
else:
    entry = {"type": "command", "command": cmd, "timeout": 10, "async": True}
    if groups and isinstance(groups[0], dict) and isinstance(groups[0].get("hooks"), list):
        groups[0]["hooks"].append(entry)
    else:
        groups.append({"hooks": [entry]})
    shutil.copy(path, path + ".bak." + time.strftime("%Y%m%d-%H%M%S"))
    with open(path, "w") as fh:
        json.dump(d, fh, indent=2)
        fh.write("\n")
    print(f"  {path}: added {cmd}")
PY
done

say "done. Open the board with: board   (terminal)   or   board-open   (browser)"
