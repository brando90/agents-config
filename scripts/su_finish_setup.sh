#!/usr/bin/env bash
# TLDR: one command to finish the Stanford-enterprise Claude setup after the browser login — mints the
# setup-token grant, stores it at ~/keys/claude_su_oauth_token.txt (mode 600), pushes it to SNAP with
# push_claude_su_snap.sh, and tells any waiting SNAP job that its route is live.
#
#   1) in a terminal:  claude-su      ->  /login  ->  pick the Stanford account
#   2) then:           bash ~/agents-config/scripts/su_finish_setup.sh [host ...]
#
# The token is read from a hidden prompt and never appears in argv, history or a log.
set -euo pipefail
umask 077
PROFILE="$HOME/.claude-su"
TOKEN_FILE="$HOME/keys/claude_su_oauth_token.txt"
HOSTS=("$@"); [ ${#HOSTS[@]} -eq 0 ] && HOSTS=(skampere1 skampere2)
die() { printf '[su-finish] FATAL: %s\n' "$*" >&2; exit 1; }
log() { printf '[su-finish] %s\n' "$*"; }

[ -d "$PROFILE" ] || die "profile $PROFILE missing — run the mac setup first (workflows/multi-account-agent-clis.md)"
ACCT=$(python3 -c '
import json,sys
try: print((json.load(open(sys.argv[1])).get("oauthAccount") or {}).get("emailAddress") or "")
except Exception: print("")' "$PROFILE/.claude.json")
[ -n "$ACCT" ] || die "$PROFILE is not logged in yet. Run:  claude-su   then /login  (pick the Stanford account)"
log "profile account: $ACCT"
case "$ACCT" in *stanford.edu*) ;; *) log "WARNING: that is not a stanford.edu address — continuing because you asked for this profile" ;; esac

if [ -s "$TOKEN_FILE" ]; then
  log "reusing the grant already at $TOKEN_FILE"
else
  log "minting a setup token (a browser window opens; approve it, then copy the sk-ant-oat... value)"
  CLAUDE_CONFIG_DIR="$PROFILE" claude setup-token || die "setup-token failed (an enterprise org can disable long-lived tokens; if so, say so and we use a per-node device login instead)"
  read -rs -p "[su-finish] paste the token (hidden): " TOKEN; echo
  [[ "$TOKEN" =~ ^sk-ant-oat[0-9]{2}-[A-Za-z0-9_-]{32,}$ ]] || die "that does not look like a setup token"
  mkdir -p "$HOME/keys"; printf '%s' "$TOKEN" > "$TOKEN_FILE"; chmod 600 "$TOKEN_FILE"; unset TOKEN
  log "saved $TOKEN_FILE (mode 600)"
fi

log "pushing to SNAP: ${HOSTS[*]}"
CLAUDE_SU_TOKEN_FILE="$TOKEN_FILE" bash "$(dirname "${BASH_SOURCE[0]}")/push_claude_su_snap.sh" "${HOSTS[@]}"
cat <<'NOTE'
[su-finish] done. Any SNAP job waiting on the Stanford route picks it up within 5 minutes —
[su-finish] e.g. the expt-89 Phase B base564 runner in tmux vb-89-base564-run-09-16-2026 on skampere2:
[su-finish]   ssh brando9@skampere2.stanford.edu 'tmux capture-pane -p -t vb-89-base564-run-09-16-2026 | tail'
NOTE
