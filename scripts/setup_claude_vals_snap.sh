#!/bin/bash
# TLDR: Idempotently installs Brando's Vals AI Claude Code profile on a Stanford SNAP node —
# the `claude-vals` / `clauded-vals` wrappers, the shared config dir on DFS, and the per-node
# $HOME symlink. Secrets are NEVER written by this script; push them with push_claude_vals_creds.sh.
#
# Usage (run ON a SNAP node, once per node):
#   bash ~/agents-config/scripts/setup_claude_vals_snap.sh [--force]
#
# --force overwrites settings.json / CLAUDE.md / the wrappers with the canonical versions below.
# Without it, existing files are left alone (so local tweaks on DFS survive re-runs).
set -euo pipefail

DFS_ROOT="${DFS_ROOT:-/dfs/scratch0/brando9}"
AFS_ROOT="${AFS:-/afs/cs.stanford.edu/u/brando9}"
VALS_DIR="$DFS_ROOT/.claude-vals"
DFS_BIN="$DFS_ROOT/bin"
AFS_BIN="$AFS_ROOT/bin"
BASHRC="$DFS_ROOT/.bashrc"
FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1

log() { printf '[claude-vals] %s\n' "$*"; }

# --- 0. sanity: DFS must be mounted, else we would silently build a per-node island ----------
if [ ! -d "$DFS_ROOT" ]; then
  echo "[claude-vals] FATAL: $DFS_ROOT not mounted on $(hostname). Run 'ls /dfs/scratch0/brando9' to trigger automount, then retry." >&2
  exit 1
fi

# --- 1. shared config dir on DFS (one profile for every SNAP node) ---------------------------
mkdir -p "$VALS_DIR"
chmod 700 "$VALS_DIR"
log "config dir: $VALS_DIR"

write_if_needed() {  # $1=path, stdin=content
  local path="$1"
  if [ -e "$path" ] && [ "$FORCE" -eq 0 ]; then
    log "keep    $path (exists; --force to overwrite)"
    cat > /dev/null
  else
    cat > "$path"
    log "write   $path"
  fi
}

# Mirrors the mac's ~/.claude-vals/settings.json, plus the SNAP-standard SessionStart hook that
# keeps the agent CLIs fresh (agents-config INDEX_RULES.md Hard Rule 7).
write_if_needed "$VALS_DIR/settings.json" <<'EOF'
{
  "model": "opus[1m]",
  "modelSettings": {
    "claude-opus-5": {
      "effortLevel": "xhigh"
    }
  },
  "skipDangerousModePermissionPrompt": true,
  "theme": "dark",
  "inputNeededNotifEnabled": true,
  "agentPushNotifEnabled": true,
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/agents-config/scripts/auto-update-tools.sh",
            "timeout": 60,
            "async": true
          }
        ]
      }
    ]
  }
}
EOF

write_if_needed "$VALS_DIR/CLAUDE.md" <<'EOF'
This profile is for Vals AI work, kept separate from the personal Claude Code login.

## Response style
Always end responses with a TL;DR: at least 1 sentence, only longer than
3-4 sentences when really necessary. Be direct and quick, not padded.
EOF

# Skip first-run onboarding (theme/login walkthrough) and pre-accept the folder-trust prompt for
# the dirs actually worked in on SNAP. Node's process.cwd() resolves symlinks, so the project keys
# are the physical /dfs and /lfs paths.
if [ ! -e "$VALS_DIR/.claude.json" ] || [ "$FORCE" -eq 1 ]; then
  python3 - "$VALS_DIR/.claude.json" "$DFS_ROOT" "$HOME" <<'EOF'
import json, os, sys
path, dfs_root, home = sys.argv[1], sys.argv[2], sys.argv[3]
cfg = {}
if os.path.exists(path):
    try:
        cfg = json.load(open(path))
    except Exception:
        cfg = {}
cfg.setdefault("hasCompletedOnboarding", True)
cfg.setdefault("theme", "dark")
projects = cfg.setdefault("projects", {})
trusted = [dfs_root, home] + [
    os.path.join(dfs_root, d) for d in ("veribench", "agents-config", "cert-judge")
]
for p in trusted:
    entry = projects.setdefault(p, {})
    entry["hasTrustDialogAccepted"] = True
    entry.setdefault("allowedTools", [])
    entry.setdefault("history", [])
json.dump(cfg, open(path, "w"), indent=2)
print(f"[claude-vals] write   {path} (onboarding skipped, {len(trusted)} dirs pre-trusted)")
EOF
  chmod 600 "$VALS_DIR/.claude.json"
else
  log "keep    $VALS_DIR/.claude.json (exists; --force to overwrite)"
fi

# --- 2. wrappers in both PATH bin dirs (AFS = always mounted, DFS = fallback) -----------------
# Same two-location pattern as the existing `clauded` script.
make_wrapper() {  # $1=dest path, $2=extra claude flags
  local dest="$1" flags="$2"
  cat > "$dest" <<EOF
#!/bin/bash
# TLDR: Claude Code under Brando's Vals AI profile (CLAUDE_CONFIG_DIR=~/.claude-vals)$( [ -n "$flags" ] && printf ', permissions skipped' ).
# Installed by ~/agents-config/scripts/setup_claude_vals_snap.sh — edit there, not here.

# Force the Vals OAuth login: Claude Code prefers these over the profile's OAuth if set.
# CLAUDE_CODE_OAUTH_TOKEN in particular is Brando's PERSONAL token and would hijack this profile.
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN CLAUDE_CODE_OAUTH_TOKEN \\
      CLAUDE_CODE_USE_BEDROCK CLAUDE_CODE_USE_VERTEX

# Per-node \$HOME symlink is the intended path; fall back to DFS if a node was never set up.
VALS_DIR="\$HOME/.claude-vals"
[ -d "\$VALS_DIR" ] || VALS_DIR="$VALS_DIR"

# Resolve a claude binary that actually RUNS. Two traps this avoids:
#  * non-interactive shells (ssh 'cmd', cron, tmux send-keys) don't source .bashrc, so nvm is absent;
#  * some nodes carry a stale root-owned /usr/local/bin/claude -> ../lib/node_modules/... symlink whose
#    target is gone. It sits early in a minimal PATH and `command -v` still reports it, so exec dies
#    with "No such file or directory". `[ -x ]` follows the link and rejects it.
export NVM_DIR="$DFS_ROOT/.nvm"
CLAUDE_BIN=""
_try() { [ -n "\$1" ] && [ -x "\$1" ] && CLAUDE_BIN="\$1"; }
# The DFS nvm copy FIRST, newest by mtime: it is the one that actually gets updated, and the one a
# login shell resolves. Nodes also carry an old root-owned /usr/local/bin/claude (2.1.75) that wins
# in a minimal PATH and, on mercury, crashes against the system node — never let that be the pick.
_try "\$(ls -t "\$NVM_DIR"/versions/node/*/bin/claude 2>/dev/null | head -1)"
[ -n "\$CLAUDE_BIN" ] || _try "\$(command -v claude 2>/dev/null || true)"
if [ -z "\$CLAUDE_BIN" ]; then
  # shellcheck disable=SC1091
  [ -s "\$NVM_DIR/nvm.sh" ] && . "\$NVM_DIR/nvm.sh" >/dev/null 2>&1
  _try "\$(command -v claude 2>/dev/null || true)"
fi
if [ -z "\$CLAUDE_BIN" ]; then
  echo "\$(basename "\$0"): no working 'claude' binary found (looked in \$NVM_DIR/versions/node/*/bin and PATH)" >&2
  exit 127
fi

exec env CLAUDE_CONFIG_DIR="\$VALS_DIR" "\$CLAUDE_BIN" $flags "\$@"
EOF
  chmod 755 "$dest"
  log "wrapper $dest"
}

for bin in "$DFS_BIN" "$AFS_BIN"; do
  if mkdir -p "$bin" 2>/dev/null && [ -w "$bin" ]; then
    make_wrapper "$bin/claude-vals" ""
    make_wrapper "$bin/clauded-vals" "--dangerously-skip-permissions"
  else
    log "SKIP    $bin (not writable — AFS token expired? run 'aklog' and re-run)"
  fi
done

# --- 3. per-node $HOME symlink ---------------------------------------------------------------
LINK="$HOME/.claude-vals"
if [ -L "$LINK" ]; then
  [ "$(readlink "$LINK")" = "$VALS_DIR" ] || { ln -sfn "$VALS_DIR" "$LINK"; log "relink  $LINK -> $VALS_DIR"; }
  log "symlink $LINK -> $(readlink "$LINK")"
elif [ -d "$LINK" ]; then
  log "WARN    $LINK is a real directory, not a symlink to DFS."
  if [ -z "$(ls -A "$LINK")" ]; then
    rmdir "$LINK" && ln -sfn "$VALS_DIR" "$LINK" && log "symlink $LINK -> $VALS_DIR (replaced empty dir)"
  else
    log "WARN    it is non-empty; leaving it alone. Merge it into $VALS_DIR by hand, then re-run."
  fi
else
  ln -sfn "$VALS_DIR" "$LINK"
  log "symlink $LINK -> $VALS_DIR"
fi

# --- 4. document the commands in the shared .bashrc (idempotent marker block) -----------------
if [ -f "$BASHRC" ] && ! grep -q '>>> claude-vals >>>' "$BASHRC"; then
  cat >> "$BASHRC" <<'EOF'

# >>> claude-vals >>>
# Vals AI Claude Code profile (separate login/config from the personal one):
#   claude-vals   -> claude with CLAUDE_CONFIG_DIR=~/.claude-vals
#   clauded-vals  -> same + --dangerously-skip-permissions   (the `clauded` of the Vals profile)
# Both are scripts in $AFS/bin and /dfs/scratch0/brando9/bin (already on PATH above), installed by
# ~/agents-config/scripts/setup_claude_vals_snap.sh. Config lives on DFS at
# /dfs/scratch0/brando9/.claude-vals and is symlinked into each node's $HOME, so all SNAP nodes
# share one Vals profile + one credential file.
# <<< claude-vals <<<
EOF
  log "bashrc  appended claude-vals doc block to $BASHRC"
else
  log "bashrc  doc block already present (or $BASHRC missing)"
fi

# --- 5. report --------------------------------------------------------------------------------
echo
log "=== state on $(hostname) ==="
ls -ld "$VALS_DIR" "$LINK" 2>&1 | sed 's/^/[claude-vals]   /'
if [ -f "$VALS_DIR/.credentials.json" ]; then
  log "  credentials: present ($(stat -c '%a %s bytes %y' "$VALS_DIR/.credentials.json" 2>/dev/null | cut -c1-40))"
else
  log "  credentials: MISSING — from the mac run: bash ~/agents-config/scripts/push_claude_vals_creds.sh"
fi
command -v claude-vals >/dev/null 2>&1 && log "  claude-vals on PATH: $(command -v claude-vals)" \
  || log "  claude-vals NOT on PATH yet — open a new shell (or: export PATH=\"$DFS_BIN:\$PATH\")"
