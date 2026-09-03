#!/usr/bin/env bash
# TLDR: SessionStart hook — records this Claude Code session's id, tmux window, cwd and config dir
# into ~/.agent-board/sessions/ so agent_board.py can label it in Brando's notation (e.g. ccv_l11).
# Never blocks and never fails the session: every step is best-effort.

set -u
OUT_DIR="$HOME/.agent-board/sessions"
mkdir -p "$OUT_DIR" 2>/dev/null || exit 0

# Claude Code passes a JSON payload on stdin.
# a session spawned by the board's own summarizer must not appear on the board
[ "${AGENT_BOARD_SUMMARIZER:-}" = "1" ] && exit 0

PAYLOAD="$(cat 2>/dev/null || true)"

get() { printf '%s' "$PAYLOAD" | /usr/bin/python3 -c "
import json,sys
try: print(json.load(sys.stdin).get('$1','') or '')
except Exception: print('')
" 2>/dev/null; }

SID="$(get session_id)"
[ -n "$SID" ] || exit 0
# The id becomes a filename: accept only UUID-ish characters so a crafted payload cannot
# escape OUT_DIR (e.g. "../../x"). Anything else is silently ignored.
case "$SID" in
  *[!A-Za-z0-9-]*|"") exit 0 ;;
esac
[ "${#SID}" -le 64 ] || exit 0
# Refuse to operate through a symlinked sessions dir (the pruner deletes files in it).
[ -L "$OUT_DIR" ] && exit 0
CWD="$(get cwd)"
TRANSCRIPT="$(get transcript_path)"

# tmux window this session lives in -> the "_l11" part of the label
TMUX_NAME=""
if [ -n "${TMUX:-}" ]; then
  TMUX_NAME="$(tmux display-message -p '#{session_name}' 2>/dev/null || true)"
fi

# which Claude config this session is using -> cc (personal) vs ccv (Vals)
CFG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

/usr/bin/python3 - "$OUT_DIR/$SID.json" "$SID" "$CWD" "$TRANSCRIPT" "$TMUX_NAME" "$CFG" <<'PY' 2>/dev/null || true
import json, sys, time
path, sid, cwd, transcript, tmux, cfg = sys.argv[1:7]
with open(path, "w") as fh:
    json.dump({"session_id": sid, "cwd": cwd, "transcript": transcript,
               "tmux": tmux, "config_dir": cfg, "started_at": time.time(),
               "host": __import__("socket").gethostname()}, fh)
PY

# Prune registrations whose transcript is gone or untouched for a week.
/usr/bin/python3 - "$OUT_DIR" <<'PY' 2>/dev/null || true
import glob, json, os, time
cut = time.time() - 7 * 86400
root = os.path.realpath(__import__("sys").argv[1])
for f in glob.glob(os.path.join(root, "*.json")):
    try:
        if os.path.islink(f) or os.path.dirname(os.path.realpath(f)) != root:
            continue                      # never follow a link out of the sessions dir
        d = json.load(open(f))
        t = d.get("transcript") or ""
        if (t and not os.path.exists(t)) or os.path.getmtime(f) < cut:
            os.remove(f)
    except Exception:
        pass
PY

exit 0
