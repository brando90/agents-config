#!/usr/bin/env bash
# TLDR: deploy a Claude Code worker on THIS machine in its own detached byobu/tmux session -- attach with
# `byobu attach -t <name>` or drive it from the phone via Remote Control -- running `clauded` / `clauded-vals`
# at a chosen model + effort on a runbook file. The local counterpart of ssh-submit.sh (SNAP nodes).
#
# Usage:
#   deploy_cc.sh --name <tmux-session> --cwd <dir> --prompt-file <runbook.md>
#                [--profile cc|ccv] [--model claude-fable-5-1] [--effort max] [--no-rc] [--dry-run]
# Example:
#   ~/agents-config/scripts/deploy_cc.sh --name vb-fix-thms --cwd ~/veribench \
#     --prompt-file experiments/74_hard_subset_and_versioned_releases/scripts/fix_false_reference_theorems_cc_prompt.md
#
# What it does: `tmux new-session -d -s <name> -c <cwd>` on the byobu/tmux server (byobu is tmux with a
# profile, same server), waits for the shell's rc files, then types
#   <wrapper> --remote-control <name> --model <model> --effort <effort> '<opening prompt>'
# into it. The opening prompt tells the agent to read the runbook and carry it out end to end; nothing
# else is sent, so the whole brief lives in the file (Trigger Rule 36: TL;DR at both ends). The agent
# board (agent_board.py) lists the session under its tmux name within 20 s.
set -euo pipefail

NAME=""; CWD=""; PROMPT=""; PROFILE=cc; MODEL=claude-fable-5-1; EFFORT=max; RC=1; DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME=${2:-}; shift 2 ;;
    --cwd) CWD=${2:-}; shift 2 ;;
    --prompt-file) PROMPT=${2:-}; shift 2 ;;
    --profile) PROFILE=${2:-}; shift 2 ;;
    --model) MODEL=${2:-}; shift 2 ;;
    --effort) EFFORT=${2:-}; shift 2 ;;
    --no-rc) RC=0; shift ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
    *) echo "deploy_cc.sh: unknown argument: $1" >&2; exit 2 ;;
  esac
done
[ -n "$NAME" ] && [ -n "$CWD" ] && [ -n "$PROMPT" ] || { echo "deploy_cc.sh: need --name, --cwd and --prompt-file" >&2; exit 2; }
case "$NAME" in *[!A-Za-z0-9_-]*|"") echo "deploy_cc.sh: --name may use letters, digits, _ and - only (it is a tmux target)" >&2; exit 2 ;; esac
case "$MODEL$EFFORT" in *[!A-Za-z0-9._-]*) echo "deploy_cc.sh: --model/--effort: letters, digits, . _ - only" >&2; exit 2 ;; esac
CWD=$(cd "$CWD" 2>/dev/null && pwd -P) || { echo "deploy_cc.sh: --cwd is not a directory: $CWD" >&2; exit 2; }
case "$PROMPT" in /*) ;; *) PROMPT="$CWD/$PROMPT" ;; esac
[ -f "$PROMPT" ] || { echo "deploy_cc.sh: --prompt-file not found: $PROMPT" >&2; exit 2; }
case "$PROMPT" in *\'*) echo "deploy_cc.sh: the runbook path may not contain a single quote" >&2; exit 2 ;; esac
case "$PROFILE" in
  cc) WRAPPER=clauded ;;                 # personal config, ~/.claude   (zsh alias)
  ccv) WRAPPER=clauded-vals ;;           # Vals config, ~/.claude-vals  (zsh function)
  *) echo "deploy_cc.sh: --profile must be cc or ccv" >&2; exit 2 ;;
esac

# Apostrophe-free on purpose: the prompt is typed into the shell inside single quotes.
OPEN="Your task brief is the runbook at $PROMPT. Read it in full first, then carry it out end to end under the repo CLAUDE.md and ~/agents-config/INDEX_RULES.md: keep its results ledger live, run the QA tier it names before pushing, and report with the mandatory TLDR/Snapshot protocol."
CMD="$WRAPPER"
[ "$RC" -eq 1 ] && CMD="$CMD --remote-control $NAME"
CMD="$CMD --model $MODEL --effort $EFFORT '$OPEN'"

if [ "$DRY" -eq 1 ]; then
  echo "tmux new-session -d -s $NAME -c $CWD"
  echo "tmux send-keys -t =$NAME: '<cmd>' Enter"
  echo "cmd: $CMD"
  exit 0
fi
if tmux has-session -t "=$NAME" 2>/dev/null; then
  echo "deploy_cc.sh: tmux session '$NAME' already exists -- pick another --name, or attach: byobu attach -t $NAME" >&2
  exit 1
fi
tmux new-session -d -s "$NAME" -c "$CWD"
# let the interactive shell finish ~/.zshrc (that is where clauded / clauded-vals are defined)
python3 -c 'import time; time.sleep(2)'
tmux send-keys -t "=$NAME:" "$CMD" Enter
echo "deployed: tmux session '$NAME' in $CWD"
echo "  attach:  byobu attach -t $NAME        (tmux attach -t $NAME also works; detach with the prefix + d)"
[ "$RC" -eq 1 ] && echo "  phone:   Remote Control is on under the name '$NAME' -- open it from claude.ai/code"
echo "  board:   python3 ~/agents-config/scripts/agent_board.py --hours 1   (row: tmux $NAME)"
echo "  typed:   $CMD"
