#!/usr/bin/env bash
# TLDR: Mac-side driver that stands up the Stanford-enterprise Claude Code profile (`claude-su` /
# `clauded-su`) on every SNAP node — pushes a long-lived setup-token grant to DFS, runs the reviewed
# install_su_node.sh on each node, installs the shared /dfs/scratch0/brando9/bin entry points, and
# smoke-tests the wrapper.
#
# Get the grant first, on the mac, from the Stanford profile (opens a browser):
#   CLAUDE_CONFIG_DIR=$HOME/.claude-su claude setup-token
#   umask 077; printf '%s' '<sk-ant-oat...>' > ~/keys/claude_su_oauth_token.txt
#
# Usage (from the mac):
#   bash ~/agents-config/scripts/push_claude_su_snap.sh                  # all default hosts
#   bash ~/agents-config/scripts/push_claude_su_snap.sh skampere1        # just one
#   SKIP_SMOKE=1 bash ~/agents-config/scripts/push_claude_su_snap.sh     # no LLM call at the end
#
# Token source, in order: $CLAUDE_SU_OAUTH_TOKEN, then $CLAUDE_SU_TOKEN_FILE
# (default ~/keys/claude_su_oauth_token.txt). The token is never passed as an argv.
#
# Why a setup-token and not the Keychain credential JSON (the Vals route): OAuth refresh tokens
# ROTATE ON USE, so one credential set shared by the mac + N nodes logs the others out. A setup
# token is long-lived and read-only to the wrapper, so every node can hold the same one.
set -euo pipefail
umask 077

DFS_ROOT="/dfs/scratch0/brando9"
SU_REMOTE="$DFS_ROOT/.claude-su-remote"
DOMAIN="stanford.edu"
DEFAULT_HOSTS=(skampere1 skampere2 skampere3 mercury1 mercury2)
HOSTS=("$@"); [ ${#HOSTS[@]} -eq 0 ] && HOSTS=("${DEFAULT_HOSTS[@]}")
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER="$HERE/install_su_node.sh"
ENTRY="$HERE/su_remote_entry.sh"
SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15)

log() { printf '[push-su] %s\n' "$*"; }
die() { printf '[push-su] FATAL: %s\n' "$*" >&2; exit 1; }

[ -f "$INSTALLER" ] || die "missing $INSTALLER"
[ -f "$ENTRY" ]     || die "missing $ENTRY"

TOKEN="${CLAUDE_SU_OAUTH_TOKEN:-}"
TOKEN_FILE="${CLAUDE_SU_TOKEN_FILE:-$HOME/keys/claude_su_oauth_token.txt}"
if [ -z "$TOKEN" ]; then
  [ -s "$TOKEN_FILE" ] || die "no token. Run: CLAUDE_CONFIG_DIR=\$HOME/.claude-su claude setup-token
  then save it:  umask 077; printf '%s' '<token>' > $TOKEN_FILE"
  TOKEN="$(tr -d ' \t\r\n' < "$TOKEN_FILE")"
fi
[[ "$TOKEN" =~ ^sk-ant-oat[0-9]{2}-[A-Za-z0-9_-]{32,}$ ]] || die "token is not a Claude Code setup token (sk-ant-oat..)"

# Identity guard: the local Stanford profile must actually be the Stanford account before its grant
# lands on a shared filesystem. Override with CLAUDE_SU_EXPECT_ACCOUNT=<substring>, "" to skip.
EXPECT_ACCOUNT="${CLAUDE_SU_EXPECT_ACCOUNT-stanford.edu}"
ACCT_EMAIL="$(python3 -c '
import json,sys
try: print((json.load(open(sys.argv[1])).get("oauthAccount") or {}).get("emailAddress") or "")
except Exception: print("")' "$HOME/.claude-su/.claude.json")"
if [ -n "$EXPECT_ACCOUNT" ]; then
  case "$ACCT_EMAIL" in
    *"$EXPECT_ACCOUNT"*) log "local profile account: $ACCT_EMAIL (matches '$EXPECT_ACCOUNT')" ;;
    *) die "~/.claude-su belongs to '${ACCT_EMAIL:-unknown}', not '$EXPECT_ACCOUNT'.
  Log in first:  CLAUDE_CONFIG_DIR=\$HOME/.claude-su claude   then /login
  Re-run with CLAUDE_SU_EXPECT_ACCOUNT=<substring> (or \"\") if this is intended." ;;
  esac
fi

OK_HOSTS=(); BAD_HOSTS=(); GRANT_DONE=0
for h in "${HOSTS[@]}"; do
  log "=== $h ==="
  if ! scp -q "${SSH_OPTS[@]}" "$INSTALLER" "$ENTRY" "$h.$DOMAIN:/tmp/"; then
    log "$h: scp FAILED — skipping"; BAD_HOSTS+=("$h"); continue
  fi
  # The grant lives on DFS and is shared by every node, so it is written exactly once, through the
  # first node that answered. It travels on stdin — never as an argument, which would hit `ps`.
  if [ "$GRANT_DONE" -eq 0 ]; then
    if printf '%s' "$TOKEN" | ssh "${SSH_OPTS[@]}" "$h.$DOMAIN" \
        "umask 077 && mkdir -p '$SU_REMOTE' && chmod 700 '$SU_REMOTE' && cat > '$SU_REMOTE/oauth-token' && chmod 600 '$SU_REMOTE/oauth-token' && ls -l '$SU_REMOTE/oauth-token'" \
        2>&1 | sed "s/^/  [$h] grant: /"; then
      GRANT_DONE=1
      # Second copy under the shared keys dir: SNAP job runners (e.g. expt-89 Phase B on skampere2)
      # watch ~/keys/claude_su_oauth_token.txt, not the wrapper's protected grant path.
      printf '%s' "$TOKEN" | ssh "${SSH_OPTS[@]}" "$h.$DOMAIN" \
        "umask 077 && mkdir -p '$DFS_ROOT/keys' && cat > '$DFS_ROOT/keys/claude_su_oauth_token.txt' && chmod 600 '$DFS_ROOT/keys/claude_su_oauth_token.txt' && ls -l '$DFS_ROOT/keys/claude_su_oauth_token.txt'" \
        2>&1 | sed "s/^/  [$h] keys-copy: /" || log "$h: keys-dir copy failed (wrapper grant still written)"
    else
      log "$h: writing the DFS grant FAILED — skipping"; BAD_HOSTS+=("$h"); continue
    fi
  fi
  set +e
  ssh "${SSH_OPTS[@]}" "$h.$DOMAIN" 'bash -lc "
    install -m 700 /tmp/install_su_node.sh \$HOME/.install_su_node.sh &&
    bash \$HOME/.install_su_node.sh; rc=\$?;
    mkdir -p /dfs/scratch0/brando9/bin &&
    install -m 755 /tmp/su_remote_entry.sh /dfs/scratch0/brando9/bin/claude-su &&
    install -m 755 /tmp/su_remote_entry.sh /dfs/scratch0/brando9/bin/clauded-su &&
    install -m 755 /tmp/su_remote_entry.sh /dfs/scratch0/brando9/bin/claude-stanford &&
    install -m 755 /tmp/su_remote_entry.sh /dfs/scratch0/brando9/bin/clauded-stanford;
    rm -f /tmp/install_su_node.sh /tmp/su_remote_entry.sh \$HOME/.install_su_node.sh;
    exit \$rc"' 2>&1 | sed "s/^/  [$h] /"
  rc=${PIPESTATUS[0]}
  set -e
  if [ "$rc" -ne 0 ]; then log "$h: install FAILED (rc=$rc)"; BAD_HOSTS+=("$h"); continue; fi
  OK_HOSTS+=("$h")
done
[ ${#OK_HOSTS[@]} -gt 0 ] || die "no node completed setup (tried: ${HOSTS[*]})"

for h in "${OK_HOSTS[@]}"; do
  log "=== $h: verify ==="
  ssh "${SSH_OPTS[@]}" "$h.$DOMAIN" 'bash -lc "
    printf \"  which: %s\n\" \"\$(command -v clauded-stanford || echo MISSING)\"
    printf \"  ver  : %s\n\" \"\$(claude-su --version 2>&1 | head -1)\"
  "' 2>&1 | sed "s/^/  [$h] /"
  if [ "${SKIP_SMOKE:-0}" != "1" ]; then
    ssh "${SSH_OPTS[@]}" "$h.$DOMAIN" 'bash -lc "cd \$HOME && timeout 180 clauded-su -p \"Reply with exactly: SU-OK\" 2>&1 | tail -3"' \
      2>&1 | sed "s/^/  [$h] smoke: /" || log "$h: smoke test failed"
  fi
done
[ ${#BAD_HOSTS[@]} -eq 0 ] || log "NOT deployed: ${BAD_HOSTS[*]}"
log "done. Use 'clauded-stanford' (alias: clauded-su) or 'claude-stanford' (alias: claude-su) on any SNAP node."
