#!/bin/bash
# TLDR: Mac-side driver that stands up the Vals AI Claude Code profile on every SNAP node — runs
# setup_claude_vals_snap.sh remotely, pipes the Vals OAuth credentials out of the mac Keychain into
# the DFS profile, copies the profile's auto-memories, and smoke-tests `clauded-vals` on each node.
#
# Usage (from the mac):
#   bash ~/agents-config/scripts/push_claude_vals_creds.sh                 # all default hosts
#   bash ~/agents-config/scripts/push_claude_vals_creds.sh skampere1       # just one
#   SKIP_SMOKE=1 bash ~/agents-config/scripts/push_claude_vals_creds.sh    # no LLM call at the end
#
# Credential note: Claude Code OAuth refresh tokens ROTATE ON USE. One credential set shared by the
# mac + N nodes means a refresh on one machine can invalidate the others ("refresh token was already
# used"). Prefer using one machine at a time, and re-run this script when a node says it is logged out.
set -euo pipefail

CFG_DIR="${CLAUDE_VALS_DIR:-$HOME/.claude-vals}"
DFS_ROOT="/dfs/scratch0/brando9"
VALS_DIR="$DFS_ROOT/.claude-vals"
DOMAIN="stanford.edu"
DEFAULT_HOSTS=(skampere1 skampere2 skampere3 mercury1 mercury2)
HOSTS=("$@"); [ ${#HOSTS[@]} -eq 0 ] && HOSTS=("${DEFAULT_HOSTS[@]}")
SETUP_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/setup_claude_vals_snap.sh"
SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15)

log() { printf '[push-vals] %s\n' "$*"; }
die() { printf '[push-vals] FATAL: %s\n' "$*" >&2; exit 1; }

[ -f "$SETUP_SRC" ] || die "missing $SETUP_SRC"
[ -d "$CFG_DIR" ]   || die "no local Vals profile at $CFG_DIR"

# --- credentials out of the mac Keychain -------------------------------------------------------
# Claude Code namespaces the Keychain entry by config dir: "Claude Code-credentials-<sha256(path)[:8]>"
# (the default ~/.claude profile uses the bare "Claude Code-credentials").
SVC_SUFFIX="$(printf '%s' "$CFG_DIR" | shasum -a 256 | cut -c1-8)"
SVC="Claude Code-credentials-${SVC_SUFFIX}"
# The DEFAULT profile (~/.claude) is the only one that uses the unsuffixed service name.
[ "$CFG_DIR" = "$HOME/.claude" ] && SVC="Claude Code-credentials"
CREDS="$(security find-generic-password -s "$SVC" -w 2>/dev/null || true)"
# Deliberately NO fallback to the bare "Claude Code-credentials" entry for a non-default profile:
# that is the PERSONAL login, and pushing it would hand the cluster the wrong account while every
# smoke test still passes.
[ -n "$CREDS" ] || die "no Keychain entry '$SVC' for profile $CFG_DIR.
  Log in once on the mac:  CLAUDE_CONFIG_DIR=$CFG_DIR claude   then /login
  (Refusing to fall back to the default 'Claude Code-credentials' entry — that is the personal login.)"

# Identity guard: the profile must be the account we think it is before it lands on a shared FS.
# Override with CLAUDE_VALS_EXPECT_ACCOUNT=<substring>, or set it to "" to skip the check.
EXPECT_ACCOUNT="${CLAUDE_VALS_EXPECT_ACCOUNT-vals.ai}"
ACCT_EMAIL="$(python3 -c '
import json,sys
try: print((json.load(open(sys.argv[1])).get("oauthAccount") or {}).get("emailAddress") or "")
except Exception: print("")' "$CFG_DIR/.claude.json")"
if [ -n "$EXPECT_ACCOUNT" ]; then
  case "$ACCT_EMAIL" in
    *"$EXPECT_ACCOUNT"*) log "profile account: $ACCT_EMAIL (matches '$EXPECT_ACCOUNT')" ;;
    *) die "profile $CFG_DIR belongs to '${ACCT_EMAIL:-unknown}', which does not match expected '$EXPECT_ACCOUNT'.
  Refusing to push it. Re-run with CLAUDE_VALS_EXPECT_ACCOUNT=<substring> (or \"\") if this is intended." ;;
  esac
fi
printf '%s' "$CREDS" | python3 -c '
import json,sys,datetime
o=json.load(sys.stdin)["claudeAiOauth"]
print("[push-vals] credential: sub=%s tier=%s refresh_expires=%s" % (
    o.get("subscriptionType"), o.get("rateLimitTier"),
    datetime.datetime.fromtimestamp(o["refreshTokenExpiresAt"]/1000).date()))' \
  || die "Keychain value is not valid Claude Code credential JSON"

OAUTH_ACCOUNT="$(python3 -c '
import json,sys
p=sys.argv[1]
try: print(json.dumps(json.load(open(p)).get("oauthAccount") or {}))
except Exception: print("{}")' "$CFG_DIR/.claude.json")"

# --- 1. run the installer on every node --------------------------------------------------------
OK_HOSTS=(); BAD_HOSTS=()
for h in "${HOSTS[@]}"; do
  log "=== $h: installing wrappers + config dir ==="
  if ! scp -q "${SSH_OPTS[@]}" "$SETUP_SRC" "$h.$DOMAIN:/tmp/setup_claude_vals_snap.sh"; then
    log "$h: scp FAILED — skipping this node"; BAD_HOSTS+=("$h"); continue
  fi
  # rc is captured BEFORE the cleanup rm, and read out of PIPESTATUS because the output goes
  # through sed — otherwise a failed install looks like a success.
  set +e
  ssh "${SSH_OPTS[@]}" "$h.$DOMAIN" \
    'bash -lc "bash /tmp/setup_claude_vals_snap.sh --force; rc=\$?; rm -f /tmp/setup_claude_vals_snap.sh; exit \$rc"' \
    2>&1 | sed "s/^/  [$h] /"
  rc=${PIPESTATUS[0]}
  set -e
  if [ "$rc" -ne 0 ]; then log "$h: setup FAILED (rc=$rc) — skipping this node"; BAD_HOSTS+=("$h"); continue; fi
  OK_HOSTS+=("$h")
done
[ ${#OK_HOSTS[@]} -gt 0 ] || die "no node completed setup (tried: ${HOSTS[*]}) — nothing to push credentials through"

# --- 2. credentials + account identity (DFS is shared, so push once, via a node that worked) ---
FIRST="${OK_HOSTS[0]}"
log "=== $FIRST: writing credentials into $VALS_DIR (shared by all nodes) ==="
printf '%s' "$CREDS" | ssh "${SSH_OPTS[@]}" "$FIRST.$DOMAIN" \
  "umask 077 && cat > '$VALS_DIR/.credentials.json' && chmod 600 '$VALS_DIR/.credentials.json' && python3 -c \"import json;json.load(open('$VALS_DIR/.credentials.json'));print('[remote] credentials.json valid JSON, mode 600')\""

log "=== $FIRST: merging oauthAccount into $VALS_DIR/.claude.json ==="
# The account JSON travels as a base64 argv (the heredoc already occupies the remote stdin).
ACCT_B64="$(printf '%s' "$OAUTH_ACCOUNT" | base64 | tr -d '\n')"
ssh "${SSH_OPTS[@]}" "$FIRST.$DOMAIN" "python3 - '$VALS_DIR/.claude.json' '$ACCT_B64'" <<'PYEOF'
import base64, json, sys, os
path = sys.argv[1]
acct = json.loads(base64.b64decode(sys.argv[2]).decode() or "{}")
cfg = json.load(open(path)) if os.path.exists(path) else {}
if acct:
    cfg["oauthAccount"] = acct
cfg["hasCompletedOnboarding"] = True
json.dump(cfg, open(path, "w"), indent=2)
os.chmod(path, 0o600)
print("[remote] .claude.json account:", (acct or {}).get("emailAddress", "(none)"),
      "org:", (acct or {}).get("organizationName", "(none)"))
PYEOF

# --- 3. auto-memories: remap the mac project keys to the SNAP physical paths --------------------
# Claude Code keys project state by cwd with "/" -> "-"; node resolves symlinks, so SNAP dirs are
# the physical /dfs (repos) and /lfs (home) paths.
log "=== $FIRST: copying profile auto-memories ==="
MEM_TMP="$(mktemp -d)"; trap 'rm -rf "$MEM_TMP"' EXIT
copied=0
for src in "$CFG_DIR"/projects/*/memory; do
  [ -d "$src" ] || continue
  key="$(basename "$(dirname "$src")")"
  case "$key" in
    -Users-*-veribench)   dst="-dfs-scratch0-brando9-veribench" ;;
    -Users-*-cert-judge)  dst="-dfs-scratch0-brando9-cert-judge" ;;
    -Users-*-agents-config) dst="-dfs-scratch0-brando9-agents-config" ;;
    *) continue ;;   # bare-$HOME and one-off dirs don't map to a stable SNAP path
  esac
  mkdir -p "$MEM_TMP/projects/$dst"
  cp -R "$src" "$MEM_TMP/projects/$dst/"
  n=$(ls -1 "$src" | wc -l | tr -d ' ')
  log "  $key -> $dst ($n memory files)"
  copied=$((copied + 1))
done
if [ "$copied" -gt 0 ]; then
  COPYFILE_DISABLE=1 tar --no-xattrs -C "$MEM_TMP" -cf - projects | ssh "${SSH_OPTS[@]}" "$FIRST.$DOMAIN" \
    "mkdir -p '$VALS_DIR' && tar -C '$VALS_DIR' -xf - && echo '[remote] memories unpacked into $VALS_DIR/projects'"
else
  log "  no mappable memory dirs found"
fi

# --- 4. verify on every node that was set up ---------------------------------------------------
[ ${#BAD_HOSTS[@]} -eq 0 ] || log "NOT deployed (setup failed): ${BAD_HOSTS[*]}"
for h in "${OK_HOSTS[@]}"; do
  log "=== $h: verify ==="
  ssh "${SSH_OPTS[@]}" "$h.$DOMAIN" 'bash -lc "
    printf \"  which: %s\n\" \"\$(command -v clauded-vals || echo MISSING)\"
    printf \"  link : %s\n\" \"\$(readlink \$HOME/.claude-vals || echo MISSING)\"
    printf \"  creds: %s\n\" \"\$(test -s \$HOME/.claude-vals/.credentials.json && echo present || echo MISSING)\"
    printf \"  ver  : %s\n\" \"\$(claude-vals --version 2>&1 | head -1)\"
  "' 2>&1 | sed "s/^/  [$h] /"
  if [ "${SKIP_SMOKE:-0}" != "1" ]; then
    ssh "${SSH_OPTS[@]}" "$h.$DOMAIN" 'bash -lc "cd \$HOME && timeout 180 clauded-vals -p \"Reply with exactly: VALS-OK\" 2>&1 | tail -3"' \
      2>&1 | sed "s/^/  [$h] smoke: /" || log "$h: smoke test failed"
  fi
done

log "done. Use 'clauded-vals' (yolo) or 'claude-vals' on any SNAP node."
