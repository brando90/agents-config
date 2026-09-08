#!/usr/bin/env bash
# TLDR: deploy a Claude Code worker on THIS machine in its own detached byobu/tmux session -- attach with
# `byobu attach -t <name>` or drive it from the phone via Remote Control -- running `clauded` / `clauded-vals`
# at a chosen model + effort on a runbook file, and only report success once Claude Code has actually
# registered itself in that session. The local counterpart of ssh-submit.sh (SNAP nodes).
#
# Usage:
#   deploy_cc.sh --name <tmux-session> --cwd <dir> --prompt-file <runbook.md>
#                [--profile cc|ccv] [--model claude-fable-5-1] [--effort max] [--no-rc]
#                [--wait <seconds, default 120>] [--dry-run]
# Example:
#   ~/agents-config/scripts/deploy_cc.sh --name vb-fix-thms --cwd ~/veribench \
#     --prompt-file experiments/74_hard_subset_and_versioned_releases/scripts/fix_false_reference_theorems_cc_prompt.md
#
# What it does: starts a detached session on the byobu/tmux server (`byobu new-session` when byobu is
# installed, so a cold server gets the byobu profile) running an interactive login zsh in <cwd>, types
#   <wrapper> --remote-control <name> --model '<model>' --effort <effort> '<opening prompt>'
# into it, then polls Claude Code's own per-process registry (~/.claude*/sessions/<pid>.json, the same
# source the agent board uses) until a live process reports tmux session <name>. Exit 0 only then;
# exit 1 with the pane's last lines when nothing registered within --wait seconds (the session is left
# for you to inspect: `byobu attach -t <name>`, or `tmux kill-session -t '=<name>'`).
# The opening prompt tells the agent to read the runbook and carry it out end to end; nothing else is
# sent, so the whole brief lives in the file (Trigger Rule 36: TL;DR at both ends).
set -euo pipefail

usage() { sed -n '2,24p' "$0"; }
die() { echo "deploy_cc.sh: $*" >&2; exit 2; }
# a flag that takes a value: the value must exist, be non-empty and not look like another flag
val() { [ $# -ge 2 ] && [ -n "$2" ] && [ "${2#-}" = "$2" ] || die "$1 needs a value (got '${2:-}')"; printf '%s' "$2"; }

NAME=""; CWD=""; PROMPT=""; PROFILE=cc; MODEL=claude-fable-5-1; EFFORT=max; RC=1; DRY=0; WAIT=120
while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME=$(val "$@"); shift 2 ;;
    --cwd) CWD=$(val "$@"); shift 2 ;;
    --prompt-file) PROMPT=$(val "$@"); shift 2 ;;
    --profile) PROFILE=$(val "$@"); shift 2 ;;
    --model) MODEL=$(val "$@"); shift 2 ;;
    --effort) EFFORT=$(val "$@"); shift 2 ;;
    --wait) WAIT=$(val "$@"); shift 2 ;;
    --no-rc) RC=0; shift ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done
[ -n "$NAME" ] && [ -n "$CWD" ] && [ -n "$PROMPT" ] || die "need --name, --cwd and --prompt-file"
case "$NAME" in *[!A-Za-z0-9_-]*) die "--name may use letters, digits, _ and - only (it is a tmux target)" ;; esac
# model ids are like claude-fable-5-1 or claude-fable-5[1m] (Hard Rule 8); typed inside single quotes
case "$MODEL" in *[!A-Za-z0-9._\[\]-]*) die "--model may use letters, digits, . _ - [ ] only (got '$MODEL')" ;; esac
case "$EFFORT" in low|medium|high|xhigh|max) ;; *) die "--effort must be one of low medium high xhigh max (got '$EFFORT')" ;; esac
case "$WAIT" in *[!0-9]*|"") die "--wait must be a whole number of seconds" ;; esac
CWD=$(cd "$CWD" 2>/dev/null && pwd -P) || die "--cwd is not a directory: $CWD"
case "$PROMPT" in /*) ;; *) PROMPT="$CWD/$PROMPT" ;; esac
[ -f "$PROMPT" ] || die "--prompt-file not found: $PROMPT"
case "$PROMPT" in *\'*) die "the runbook path may not contain a single quote" ;; esac
case "$PROFILE" in
  cc) WRAPPER=clauded; REG_DIR="$HOME/.claude/sessions" ;;              # personal config (zsh alias)
  ccv) WRAPPER=clauded-vals; REG_DIR="$HOME/.claude-vals/sessions" ;;   # Vals config (zsh function)
  *) die "--profile must be cc or ccv" ;;
esac
WRAPPER=${DEPLOY_WRAPPER:-$WRAPPER}     # test hook: point at a missing command to exercise the failure path
LAUNCHER=$(command -v byobu || command -v tmux) || die "neither byobu nor tmux is installed"
command -v tmux >/dev/null || die "tmux is not installed"

# Apostrophe-free on purpose: the prompt is typed into the shell inside single quotes.
OPEN="Your task brief is the runbook at $PROMPT. Read it in full first, then carry it out end to end under the repo CLAUDE.md and ~/agents-config/INDEX_RULES.md: keep its results ledger live, run the QA tier it names before pushing, and report with the mandatory TLDR/Snapshot protocol."
CMD="$WRAPPER"
[ "$RC" -eq 1 ] && CMD="$CMD --remote-control $NAME"
CMD="$CMD --model '$MODEL' --effort $EFFORT '$OPEN'"

if [ "$DRY" -eq 1 ]; then
  echo "$LAUNCHER new-session -d -s $NAME -c $CWD /bin/zsh -il"
  echo "tmux send-keys -t =$NAME: '<cmd>' Enter"
  echo "then poll $REG_DIR/*.json for a live pid whose tmux field starts with '$NAME:' (up to ${WAIT}s)"
  echo "cmd: $CMD"
  exit 0
fi
if tmux has-session -t "=$NAME" 2>/dev/null; then
  echo "deploy_cc.sh: tmux session '$NAME' already exists -- pick another --name, or attach: byobu attach -t $NAME" >&2
  exit 1
fi
# an explicit interactive login zsh: the wrappers are defined in ~/.zshrc, whatever the server default is
"$LAUNCHER" new-session -d -s "$NAME" -c "$CWD" /bin/zsh -il
python3 -c 'import time; time.sleep(2)'    # let the shell finish its rc files before the keys arrive
tmux send-keys -t "=$NAME:" "$CMD" Enter
echo "typed into tmux session '$NAME' ($CWD): $CMD"
echo "waiting up to ${WAIT}s for Claude Code to register in that session ..."

# Claude Code writes <config>/sessions/<pid>.json with "tmux":"<session>:@w.%p" while it runs; that
# file plus a live pid is the same evidence the agent board uses, so "deployed" means exactly that.
registered() {
  python3 - "$REG_DIR" "$NAME" <<'PY'
import glob, json, os, sys
reg, name = sys.argv[1], sys.argv[2]
for f in glob.glob(os.path.join(reg, "*.json")):
    try:
        d = json.load(open(f))
        pid = int(d.get("pid") or 0)
        if str(d.get("tmux", "")).split(":", 1)[0] == name and pid > 0:
            os.kill(pid, 0)
            print(d.get("sessionId", "")[:8]); sys.exit(0)
    except Exception:
        continue
sys.exit(1)
PY
}
deadline=$((SECONDS + WAIT))
while [ "$SECONDS" -lt "$deadline" ]; do
  if SID=$(registered); then
    echo "deployed: Claude Code session $SID is live in tmux session '$NAME'"
    echo "  attach:  byobu attach -t $NAME        (tmux attach -t '=$NAME' also works; detach with the prefix + d)"
    [ "$RC" -eq 1 ] && echo "  phone:   Remote Control requested under the name '$NAME' -- open it from claude.ai/code"
    echo "  board:   python3 ~/agents-config/scripts/agent_board.py --hours 1   (row: tmux $NAME)"
    exit 0
  fi
  python3 -c 'import time; time.sleep(2)'
done
echo "deploy_cc.sh: NOT verified -- no live Claude Code process registered tmux session '$NAME' within ${WAIT}s." >&2
echo "  last lines of the pane:" >&2
tmux capture-pane -p -t "=$NAME:" 2>/dev/null | grep -v '^$' | tail -6 | sed 's/^/    /' >&2
echo "  inspect: byobu attach -t $NAME      discard: tmux kill-session -t '=$NAME'" >&2
exit 1
