#!/usr/bin/env bash
# TLDR: Keep the shared SNAP NVM installs of Claude Code and Codex current without writing to a shadow prefix or hiding failures.

set -uo pipefail

DFS_ROOT="${SNAP_DFS_ROOT:-/dfs/scratch0/brando9}"
NVM_DIR="$DFS_ROOT/.nvm"
CACHE_DIR="$DFS_ROOT/.cache"
LOCK_DIR="$CACHE_DIR/agent-cli-update.lock"
STAMP_FILE="$CACHE_DIR/agent-cli-update.stamp"
LOG_FILE="$CACHE_DIR/agent-cli-update.log"
MAX_AGE_MINUTES="${SNAP_TOOL_UPDATE_MAX_AGE_MINUTES:-360}"
FORCE=0
[ "${1:-}" = --force ] && FORCE=1

if [ "$(uname)" = Darwin ]; then
  npm install -g @anthropic-ai/claude-code@latest @openai/codex@latest
  if command -v brew >/dev/null 2>&1; then
    brew upgrade --cask antigravity >/dev/null 2>&1 || true
  fi
  exit 0
fi

umask 077
mkdir -p "$CACHE_DIR"
if [ ! -e "$LOG_FILE" ]; then
  printf '# TLDR: This log records attempts to update the canonical shared SNAP agent command-line tools.\n' >"$LOG_FILE"
fi
chmod 600 "$LOG_FILE"
exec >>"$LOG_FILE" 2>&1
printf '[%s] host=%s start force=%s\n' "$(date -Is)" "$(hostname -s)" "$FORCE"

if [ "$FORCE" -eq 0 ] && [ -f "$STAMP_FILE" ] &&
   find "$STAMP_FILE" -mmin -"$MAX_AGE_MINUTES" -print -quit 2>/dev/null | grep -q .; then
  printf '[%s] fresh stamp; skip (max_age=%sm)\n' "$(date -Is)" "$MAX_AGE_MINUTES"
  exit 0
fi

LOCK_OWNER="$LOCK_DIR/owner"
LOCK_ACQUIRED=0
_lock_host="$(hostname -s)"
if mkdir "$LOCK_DIR" 2>/dev/null; then
  LOCK_ACQUIRED=1
else
  _owner_line="$(tail -1 "$LOCK_OWNER" 2>/dev/null || true)"
  set -- $_owner_line
  _owner_pid="${1:-}" _owner_host="${2:-}"
  if [ "$_owner_host" = "$_lock_host" ] && [ -n "$_owner_pid" ] && ! kill -0 "$_owner_pid" 2>/dev/null; then
    rm -f -- "$LOCK_OWNER"
    rmdir "$LOCK_DIR" 2>/dev/null || true
    mkdir "$LOCK_DIR" 2>/dev/null && LOCK_ACQUIRED=1
    [ "$LOCK_ACQUIRED" -eq 0 ] || printf '[%s] reclaimed dead local updater lock\n' "$(date -Is)"
  elif [ ! -e "$LOCK_OWNER" ] &&
       find "$LOCK_DIR" -maxdepth 0 -mmin +20 -print -quit 2>/dev/null | grep -q .; then
    rmdir "$LOCK_DIR" 2>/dev/null || true
    mkdir "$LOCK_DIR" 2>/dev/null && LOCK_ACQUIRED=1
    [ "$LOCK_ACQUIRED" -eq 0 ] || printf '[%s] reclaimed legacy empty updater lock\n' "$(date -Is)"
  fi
fi
if [ "$LOCK_ACQUIRED" -ne 1 ]; then
  printf '[%s] another updater owns the lock (%s); leave it intact\n' "$(date -Is)" "${_owner_line:-owner record pending}"
  exit 75
fi
printf '# TLDR: This file identifies the process holding the shared SNAP agent-tool updater lock.\n%s %s\n' "$$" "$_lock_host" >"$LOCK_OWNER"
release_lock() {
  rm -f -- "$LOCK_OWNER"
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap release_lock EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

if [ ! -s "$NVM_DIR/nvm.sh" ]; then
  printf '[%s] ERROR missing %s/nvm.sh\n' "$(date -Is)" "$NVM_DIR"
  exit 1
fi

export NVM_DIR
# shellcheck disable=SC1090
. "$NVM_DIR/nvm.sh" >/dev/null 2>&1
if ! nvm use default --silent >/dev/null 2>&1; then
  printf '[%s] ERROR NVM has no usable default Node.js version\n' "$(date -Is)"
  exit 1
fi

NPM_PREFIX="$(npm prefix -g 2>/dev/null || true)"
case "$NPM_PREFIX" in
  "$NVM_DIR"/versions/node/*) ;;
  *)
    printf '[%s] ERROR npm global prefix is %s, expected a dynamic path below %s/versions/node\n' \
      "$(date -Is)" "${NPM_PREFIX:-missing}" "$NVM_DIR"
    exit 1
    ;;
esac

FAILED=0
update_one() {
  _package="$1" _binary="$2"
  _latest="$(timeout 45 npm view "$_package" version 2>/dev/null || true)"
  _current_output="$(timeout 30 "$NPM_PREFIX/bin/$_binary" --version 2>&1)"
  _current_rc=$?
  _current="$(printf '%s\n' "$_current_output" | grep -oE '[0-9]+(\.[0-9]+)+' | head -1)"
  if [ -z "$_latest" ]; then
    printf '[%s] ERROR registry lookup failed for %s\n' "$(date -Is)" "$_package"
    FAILED=1
    return
  fi
  if [ "$_current_rc" -eq 0 ] && [ "$_current" = "$_latest" ]; then
    printf '[%s] current %s=%s path=%s/bin/%s\n' "$(date -Is)" "$_binary" "$_current" "$NPM_PREFIX" "$_binary"
    return
  fi
  printf '[%s] update %s current=%s latest=%s prefix=%s\n' \
    "$(date -Is)" "$_binary" "${_current:-missing}" "$_latest" "$NPM_PREFIX"
  if timeout 300 npm install -g "$_package@$_latest"; then
    _after="$(timeout 30 "$NPM_PREFIX/bin/$_binary" --version 2>&1)"
    _after_rc=$?
    _after_first="$(printf '%s\n' "$_after" | head -1)"
    _after_version="$(printf '%s\n' "$_after" | grep -oE '[0-9]+(\.[0-9]+)+' | head -1)"
    if [ "$_after_rc" -eq 0 ] && [ "$_after_version" = "$_latest" ]; then
      printf '[%s] updated %s=%s: %s\n' "$(date -Is)" "$_binary" "$_after_version" "$_after_first"
    else
      printf '[%s] ERROR installed %s but expected=%s observed=%s rc=%s: %s\n' \
        "$(date -Is)" "$_binary" "$_latest" "${_after_version:-missing}" "$_after_rc" "$_after_first"
      FAILED=1
    fi
  else
    printf '[%s] ERROR npm install failed for %s\n' "$(date -Is)" "$_package"
    FAILED=1
  fi
}

update_one @anthropic-ai/claude-code claude
update_one @openai/codex codex

if [ "$FAILED" -ne 0 ]; then
  printf '[%s] completed with errors; see this log and rerun with --force\n' "$(date -Is)"
  exit 1
fi

printf '# TLDR: A successful canonical SNAP agent command-line tool update completed at %s.\n' "$(date -Is)" >"$STAMP_FILE"
printf '[%s] success prefix=%s\n' "$(date -Is)" "$NPM_PREFIX"
