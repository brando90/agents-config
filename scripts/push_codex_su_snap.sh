#!/usr/bin/env bash
# TLDR: Mac-side driver that stands up the Stanford-enterprise Codex profile (`codex-su` /
# `codexd-su`) on every SNAP node — runs install_codex_su_node.sh on each node, copies the mac
# ~/.codex-su/auth.json into the node-local CODEX_HOME over stdin, installs the shared
# /dfs/scratch0/brando9/bin entry points, and verifies `codex-su login status`.
#
# Log in on the mac first (opens a browser; pick the Stanford enterprise workspace):
#   CODEX_HOME=$HOME/.codex-su codex login          # or: codex-su login
#
# Usage (from the mac):
#   bash ~/agents-config/scripts/push_codex_su_snap.sh                 # all default hosts
#   bash ~/agents-config/scripts/push_codex_su_snap.sh skampere1       # just one
#   AUTH_MODE=device bash ~/agents-config/scripts/push_codex_su_snap.sh   # no auth copy; print
#                                                                         # per-node device-login cmd
#   SKIP_SMOKE=1 bash ~/agents-config/scripts/push_codex_su_snap.sh    # no model call at the end
#
# Credential note: Codex ChatGPT tokens refresh in place, so the mac and N nodes sharing one
# auth.json can race each other out of a session. AUTH_MODE=device gives each node its own grant
# (`codex-su login --device-auth` on the node, finish in a browser) and avoids that entirely;
# AUTH_MODE=copy (the default) is the one-shot, no-browser-per-node route.
set -euo pipefail
umask 077

DFS_ROOT="/dfs/scratch0/brando9"
DOMAIN="stanford.edu"
AUTH_MODE="${AUTH_MODE:-copy}"
DEFAULT_HOSTS=(skampere1 skampere2 skampere3 mercury1 mercury2)
HOSTS=("$@"); [ ${#HOSTS[@]} -eq 0 ] && HOSTS=("${DEFAULT_HOSTS[@]}")
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER="$HERE/install_codex_su_node.sh"
ENTRY="$HERE/codex_su_remote_entry.sh"
LOCAL_PROFILE="${CODEX_SU_DIR:-$HOME/.codex-su}"
SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15)

log() { printf '[push-codex-su] %s\n' "$*"; }
die() { printf '[push-codex-su] FATAL: %s\n' "$*" >&2; exit 1; }

[ -f "$INSTALLER" ] || die "missing $INSTALLER"
[ -f "$ENTRY" ]     || die "missing $ENTRY"

AUTH_JSON=""
if [ "$AUTH_MODE" = copy ]; then
  [ -s "$LOCAL_PROFILE/auth.json" ] || die "no $LOCAL_PROFILE/auth.json.
  Log in on the mac first:  CODEX_HOME=$LOCAL_PROFILE codex login
  (or re-run with AUTH_MODE=device to log each node in separately)"
  # Identity guard: refuse to ship an API-key login to the cluster — that is personal billing,
  # not the Stanford subscription. Override with CODEX_SU_EXPECT_MODE="" to skip.
  AUTH_INFO="$(python3 -c '
import json,sys
d=json.load(open(sys.argv[1]))
print(d.get("auth_mode") or ("apikey" if d.get("OPENAI_API_KEY") else "unknown"),
      (d.get("tokens") or {}).get("account_id") or "no-account-id")' "$LOCAL_PROFILE/auth.json")"
  AUTH_M="${AUTH_INFO%% *}"
  EXPECT_MODE="${CODEX_SU_EXPECT_MODE-chatgpt}"
  if [ -n "$EXPECT_MODE" ] && [ "$AUTH_M" != "$EXPECT_MODE" ]; then
    die "$LOCAL_PROFILE/auth.json is auth_mode='$AUTH_M', expected '$EXPECT_MODE' (subscription login).
  Refusing to push an API-key credential to the cluster."
  fi
  log "local profile auth: $AUTH_INFO"
  AUTH_JSON="$(cat "$LOCAL_PROFILE/auth.json")"
fi

OK_HOSTS=(); BAD_HOSTS=()
for h in "${HOSTS[@]}"; do
  log "=== $h ==="
  if ! scp -q "${SSH_OPTS[@]}" "$INSTALLER" "$ENTRY" "$h.$DOMAIN:/tmp/"; then
    log "$h: scp FAILED — skipping"; BAD_HOSTS+=("$h"); continue
  fi
  set +e
  ssh "${SSH_OPTS[@]}" "$h.$DOMAIN" 'bash -lc "
    install -m 700 /tmp/install_codex_su_node.sh \$HOME/.install_codex_su_node.sh &&
    bash \$HOME/.install_codex_su_node.sh; rc=\$?;
    mkdir -p /dfs/scratch0/brando9/bin &&
    install -m 755 /tmp/codex_su_remote_entry.sh /dfs/scratch0/brando9/bin/codex-su &&
    install -m 755 /tmp/codex_su_remote_entry.sh /dfs/scratch0/brando9/bin/codexd-su;
    rm -f /tmp/install_codex_su_node.sh /tmp/codex_su_remote_entry.sh \$HOME/.install_codex_su_node.sh;
    exit \$rc"' 2>&1 | sed "s/^/  [$h] /"
  rc=${PIPESTATUS[0]}
  set -e
  if [ "$rc" -ne 0 ]; then log "$h: install FAILED (rc=$rc)"; BAD_HOSTS+=("$h"); continue; fi

  if [ "$AUTH_MODE" = copy ]; then
    # auth.json travels on stdin, never as an argument.
    if ! printf '%s' "$AUTH_JSON" | ssh "${SSH_OPTS[@]}" "$h.$DOMAIN" \
        'bash -lc "umask 077 && p=/lfs/\$(hostname -s)/0/brando9/.codex-su && cat > \$p/auth.json && chmod 600 \$p/auth.json && python3 -c \"import json;d=json.load(open(\\\"\$p/auth.json\\\"));print(\\\"[remote] auth.json ok mode=\\\"+str(d.get(\\\"auth_mode\\\")))\""' \
        2>&1 | sed "s/^/  [$h] auth: /"; then
      log "$h: auth copy FAILED"; BAD_HOSTS+=("$h"); continue
    fi
  else
    log "  [$h] auth: AUTH_MODE=device — run on the node:  ssh $h.$DOMAIN -t 'bash -lc \"codex-su login --device-auth\"'"
  fi
  OK_HOSTS+=("$h")
done
[ ${#OK_HOSTS[@]} -gt 0 ] || die "no node completed setup (tried: ${HOSTS[*]})"

for h in "${OK_HOSTS[@]}"; do
  log "=== $h: verify ==="
  ssh "${SSH_OPTS[@]}" "$h.$DOMAIN" 'bash -lc "
    printf \"  which : %s\n\" \"\$(command -v codexd-su || echo MISSING)\"
    printf \"  ver   : %s\n\" \"\$(codex-su --version 2>&1 | head -1)\"
    printf \"  login : %s\n\" \"\$(codex-su login status 2>&1 | head -1)\"
  "' 2>&1 | sed "s/^/  [$h] /"
  if [ "${SKIP_SMOKE:-0}" != "1" ] && [ "$AUTH_MODE" = copy ]; then
    ssh "${SSH_OPTS[@]}" "$h.$DOMAIN" 'bash -lc "cd /dfs/scratch0/brando9 && timeout 240 codexd-su exec --skip-git-repo-check \"Reply with exactly: SU-OK\" < /dev/null 2>&1 | tail -3"' \
      2>&1 | sed "s/^/  [$h] smoke: /" || log "$h: smoke test failed"
  fi
done
[ ${#BAD_HOSTS[@]} -eq 0 ] || log "NOT deployed: ${BAD_HOSTS[*]}"
log "done. Use 'codexd-su' (full-trust) or 'codex-su' on any SNAP node."
