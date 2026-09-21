#!/usr/bin/env bash
# TLDR: Idempotently install/update Cursor Agent (`agent`), Grok Build (`grok`), and Antigravity (`agy`) on a Mac or SNAP node, without letting Grok steal the `agent` command or installing the deprecated Gemini CLI.

set -uo pipefail

DFS_ROOT="${SNAP_DFS_ROOT:-/dfs/scratch0/brando9}"
MODE="install"
STATUS_ONLY=0
FAILED=0

usage() {
  cat <<'EOF'
Usage: install_agent_clis.sh [--install|--update|--status]

Installs or updates the coding-agent CLIs that are not the Claude Code / Codex
NVM packages:

  agent / cursor-agent   Cursor Agent CLI   https://cursor.com/install
  grok                   Grok Build CLI     https://x.ai/cli/install.sh
  agy / antigravity      Antigravity CLI    https://antigravity.google/cli/install.sh

Does NOT install @google/gemini-cli (the deprecated Gemini CLI). Google-model
coding-agent work uses `agy` signed into a Google account.

On SNAP (Linux + /dfs/scratch0/brando9), binaries go under the DFS home so every
node sees the same install; wrappers land in /dfs/scratch0/brando9/bin (already
on PATH). Grok also ships an `agent` binary — this script never puts that on
PATH, because Cursor owns `agent`.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --install) MODE="install" ;;
    --update) MODE="update" ;;
    --status) STATUS_ONLY=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

is_snap() {
  [ "$(uname -s)" = Linux ] && [ -d "$DFS_ROOT" ]
}

if is_snap; then
  CLI_HOME="$DFS_ROOT"
  WRAP_DIR="$DFS_ROOT/bin"
else
  CLI_HOME="$HOME"
  WRAP_DIR="$HOME/.local/bin"
fi

LOCAL_BIN="$CLI_HOME/.local/bin"
CURSOR_VERSIONS="$CLI_HOME/.local/share/cursor-agent/versions"
GROK_BIN_DIR="$CLI_HOME/.grok/bin"
mkdir -p "$LOCAL_BIN" "$WRAP_DIR"

log() { printf '[%s] %s\n' "$(date '+%m-%d-%Y %H:%M:%S %Z')" "$*"; }
ok() { printf 'OK    %s\n' "$*"; }
warn() { printf 'WARN  %s\n' "$*"; }
err() { printf 'ERROR %s\n' "$*"; FAILED=1; }

run_to() {
  # Bound a command without requiring GNU timeout(1) (missing on stock macOS).
  _secs="$1"
  shift
  python3 - "$_secs" "$@" <<'PY'
import subprocess
import sys

limit = int(sys.argv[1])
cmd = sys.argv[2:]
try:
    raise SystemExit(subprocess.run(cmd, timeout=limit).returncode)
except subprocess.TimeoutExpired:
    raise SystemExit(124)
PY
}

version_of() {
  _bin="$1"
  if [ ! -x "$_bin" ]; then
    printf 'missing'
    return
  fi
  run_to 20 "$_bin" --version 2>/dev/null | head -1 | tr -d '\r' || printf 'unknown'
}

latest_cursor_agent() {
  ls -1dt "$CURSOR_VERSIONS"/*/cursor-agent 2>/dev/null | head -1 || true
}

restore_cursor_agent() {
  _src="$(latest_cursor_agent)"
  if [ -z "$_src" ] || [ ! -x "$_src" ]; then
    return 1
  fi
  ln -sfn "$_src" "$LOCAL_BIN/agent"
  ln -sfn "$_src" "$LOCAL_BIN/cursor-agent"
  if is_snap; then
    write_wrapper "$WRAP_DIR/agent" "$LOCAL_BIN/agent"
    write_wrapper "$WRAP_DIR/cursor-agent" "$LOCAL_BIN/cursor-agent"
  fi
  return 0
}

agent_points_at_grok() {
  _target="$(readlink "$1" 2>/dev/null || true)"
  case "$_target" in
    *grok*) return 0 ;;
    *) return 1 ;;
  esac
}

write_wrapper() {
  _dest="$1" _target="$2"
  cat > "$_dest" <<EOF
#!/usr/bin/env bash
# TLDR: DFS-shared wrapper so every SNAP node runs the same $_target binary.
exec "$_target" "\$@"
EOF
  chmod 755 "$_dest"
}

strip_grok_path_block() {
  # Grok's installer prepends ~/.grok/bin to PATH, which would make `agent`
  # resolve to Grok. Cursor owns that command name.
  for _rc in "$HOME/.zshrc" "$HOME/.bashrc" "$CLI_HOME/.zshrc" "$CLI_HOME/.bashrc"; do
    [ -f "$_rc" ] || continue
    if grep -qs 'grok installer' "$_rc"; then
      _tmp="$_rc.tmp.$$"
      awk '
        /# >>> grok installer >>>/ { skip=1; next }
        /# <<< grok installer <<</ { skip=0; next }
        !skip { print }
      ' "$_rc" > "$_tmp" && mv "$_tmp" "$_rc"
      log "removed Grok PATH block from $_rc so Cursor keeps \`agent\`"
    fi
  done
}

protect_cursor_agent() {
  strip_grok_path_block
  if [ -e "$LOCAL_BIN/agent" ] && agent_points_at_grok "$LOCAL_BIN/agent"; then
    warn "Grok overwrote $LOCAL_BIN/agent; restoring Cursor Agent"
    restore_cursor_agent || err "could not restore Cursor Agent symlink"
  fi
  if [ -L "$LOCAL_BIN/agent" ] || [ -e "$LOCAL_BIN/agent" ]; then
    if agent_points_at_grok "$LOCAL_BIN/agent"; then
      err "Cursor \`agent\` still points at Grok after restore"
    fi
  fi
  # Never leave a Grok \`agent\` on a PATH directory we control.
  if [ -L "$LOCAL_BIN/agent" ] && agent_points_at_grok "$LOCAL_BIN/agent"; then
    rm -f "$LOCAL_BIN/agent"
  fi
  if [ -L "$WRAP_DIR/agent" ] && agent_points_at_grok "$WRAP_DIR/agent"; then
    rm -f "$WRAP_DIR/agent"
  fi
}

install_cursor_agent() {
  log "Cursor Agent: install/update (HOME=$CLI_HOME)"
  if [ -x "$LOCAL_BIN/cursor-agent" ] || [ -x "$LOCAL_BIN/agent" ]; then
    if HOME="$CLI_HOME" run_to 120 "$LOCAL_BIN/cursor-agent" update 2>/dev/null \
      || HOME="$CLI_HOME" run_to 120 "$LOCAL_BIN/agent" update 2>/dev/null; then
      ok "cursor-agent update: $(version_of "$LOCAL_BIN/agent")"
      restore_cursor_agent || true
      return
    fi
    log "cursor-agent update failed or missing; running official installer"
  fi
  _installer="$(mktemp /tmp/cursor-agent-install.XXXXXX.sh)"
  if ! curl -fsSL https://cursor.com/install -o "$_installer"; then
    err "failed to download https://cursor.com/install"
    rm -f "$_installer"
    return
  fi
  if ! HOME="$CLI_HOME" bash "$_installer"; then
    err "cursor.com/install failed"
    rm -f "$_installer"
    return
  fi
  rm -f "$_installer"
  restore_cursor_agent || err "Cursor Agent installed but symlink missing"
  ok "cursor-agent: $(version_of "$LOCAL_BIN/agent")"
}

install_grok() {
  log "Grok Build: install/update (GROK_BIN_DIR=$GROK_BIN_DIR)"
  mkdir -p "$GROK_BIN_DIR"
  if [ -x "$GROK_BIN_DIR/grok" ]; then
    if HOME="$CLI_HOME" GROK_BIN_DIR="$GROK_BIN_DIR" run_to 120 "$GROK_BIN_DIR/grok" update 2>/dev/null; then
      ok "grok update: $(version_of "$GROK_BIN_DIR/grok")"
      ln -sfn "$GROK_BIN_DIR/grok" "$LOCAL_BIN/grok"
      [ "$WRAP_DIR" != "$LOCAL_BIN" ] && write_wrapper "$WRAP_DIR/grok" "$GROK_BIN_DIR/grok"
      protect_cursor_agent
      return
    fi
    log "grok update failed or unsupported; running official installer"
  fi
  _installer="$(mktemp /tmp/grok-install.XXXXXX.sh)"
  if ! curl -fsSL https://x.ai/cli/install.sh -o "$_installer"; then
    err "failed to download https://x.ai/cli/install.sh"
    rm -f "$_installer"
    return
  fi
  # SHELL= stops the installer from rewriting .bashrc/.zshrc (it would put
  # ~/.grok/bin first, stealing the \`agent\` command). PATH during install
  # omits $LOCAL_BIN so it does not symlink Grok over Cursor's agent.
  if ! HOME="$CLI_HOME" GROK_BIN_DIR="$GROK_BIN_DIR" SHELL= \
       env PATH="/usr/bin:/bin:/usr/sbin:/sbin" bash "$_installer"; then
    err "x.ai/cli/install.sh failed"
    rm -f "$_installer"
    protect_cursor_agent
    return
  fi
  rm -f "$_installer"
  if [ ! -x "$GROK_BIN_DIR/grok" ]; then
    err "grok binary missing after installer: $GROK_BIN_DIR/grok"
    protect_cursor_agent
    return
  fi
  ln -sfn "$GROK_BIN_DIR/grok" "$LOCAL_BIN/grok"
  if is_snap; then
    write_wrapper "$WRAP_DIR/grok" "$GROK_BIN_DIR/grok"
  fi
  protect_cursor_agent
  ok "grok: $(version_of "$GROK_BIN_DIR/grok")"
}

install_agy() {
  log "Antigravity CLI: install/update (agy -> $LOCAL_BIN/agy)"
  if [ -x "$LOCAL_BIN/agy" ]; then
    ok "agy already present: $(version_of "$LOCAL_BIN/agy") (self-updates on run)"
  else
    _installer="$(mktemp /tmp/agy-install.XXXXXX.sh)"
    if ! curl -fsSL https://antigravity.google/cli/install.sh -o "$_installer"; then
      err "failed to download https://antigravity.google/cli/install.sh"
      rm -f "$_installer"
      return
    fi
    if is_snap; then
      _agy_home="$(mktemp -d /tmp/agy-home.XXXXXX)"
      # Dummy HOME so `agy install` cannot rewrite the shared DFS .bashrc.
      if ! HOME="$_agy_home" bash "$_installer" --dir "$LOCAL_BIN"; then
        err "antigravity.google/cli/install.sh failed"
        rm -rf "$_agy_home" "$_installer"
        return
      fi
      rm -rf "$_agy_home"
    else
      if ! HOME="$CLI_HOME" bash "$_installer" --dir "$LOCAL_BIN"; then
        err "antigravity.google/cli/install.sh failed"
        rm -f "$_installer"
        return
      fi
    fi
    rm -f "$_installer"
    [ -x "$LOCAL_BIN/agy" ] || err "agy missing after installer"
  fi
  ln -sfn "$LOCAL_BIN/agy" "$LOCAL_BIN/antigravity"
  if is_snap; then
    write_wrapper "$WRAP_DIR/agy" "$LOCAL_BIN/agy"
    write_wrapper "$WRAP_DIR/antigravity" "$LOCAL_BIN/agy"
  fi
  ok "agy: $(version_of "$LOCAL_BIN/agy")"
}

warn_deprecated_gemini() {
  _g="$(command -v gemini 2>/dev/null || true)"
  if [ -n "$_g" ]; then
    warn "deprecated Gemini CLI present at $_g ($(version_of "$_g")). Do not install it on SNAP. Google coding-agent work uses \`agy\`."
  else
    ok "deprecated Gemini CLI not on PATH"
  fi
}

print_status() {
  echo "host=$(hostname -s) os=$(uname -s)/$(uname -m) cli_home=$CLI_HOME"
  printf '%-16s %-10s %s\n' "cli" "path" "version"
  for _name_path in \
    "agent:$LOCAL_BIN/agent" \
    "cursor-agent:$LOCAL_BIN/cursor-agent" \
    "grok:$GROK_BIN_DIR/grok" \
    "agy:$LOCAL_BIN/agy" \
    "claude:$(command -v claude 2>/dev/null || true)" \
    "codex:$(command -v codex 2>/dev/null || true)"; do
    _name="${_name_path%%:*}"
    _path="${_name_path#*:}"
    [ -n "$_path" ] || _path="missing"
    printf '%-16s %-10s %s\n' "$_name" "$(version_of "$_path")" "$_path"
  done
  echo "--- auth (no secrets) ---"
  if [ -x "$LOCAL_BIN/agent" ]; then
    HOME="$CLI_HOME" run_to 20 "$LOCAL_BIN/agent" status 2>/dev/null \
      | grep -Ei 'logged|not authenticated|email|subscription|account' \
      | head -8 || echo "agent status: unavailable"
  else
    echo "agent: not installed"
  fi
  if [ -x "$GROK_BIN_DIR/grok" ]; then
    if HOME="$CLI_HOME" run_to 20 "$GROK_BIN_DIR/grok" login --help >/dev/null 2>&1; then
      HOME="$CLI_HOME" run_to 20 "$GROK_BIN_DIR/grok" status 2>/dev/null \
        | grep -Ei 'logged|not |account|user|email' | head -8 \
        || echo "grok: installed; run: grok login"
    else
      echo "grok: installed; run: grok login"
    fi
  else
    echo "grok: not installed"
  fi
  if [ -x "$LOCAL_BIN/agy" ]; then
    echo "agy: installed; first run signs into a Google account (browser on Mac, URL+code on SNAP SSH)."
  else
    echo "agy: not installed"
  fi
  warn_deprecated_gemini
}

if [ "$STATUS_ONLY" -eq 1 ]; then
  print_status
  exit 0
fi

log "start mode=$MODE host=$(hostname -s) cli_home=$CLI_HOME"
install_cursor_agent
install_grok
install_agy
protect_cursor_agent
warn_deprecated_gemini
print_status

if [ "$FAILED" -ne 0 ]; then
  log "completed with errors"
  exit 1
fi
log "success"
exit 0
