#!/usr/bin/env bash
# TLDR: deploy a Claude Code (or Codex) worker on THIS machine in its own detached byobu/tmux session --
# attach with `byobu attach -t <name>` or drive Claude Code from the phone via Remote Control -- running
# `clauded` / `clauded-vals` / `codex` at a chosen model + effort on a runbook file, and only report success
# once the agent has actually started in that session. The local counterpart of ssh-submit.sh (SNAP nodes).
# Trigger Rule 42: every dispatched worker gets a session like this, named after project and task; the
# opening prompt also asks for the Rule 44 checkpoint file CKPT_<name>.md in the work dir.
#
# Usage:
#   deploy_cc.sh --name <tmux-session> --cwd <dir> --prompt-file <runbook.md>
#                [--profile cc|ccv|codex] [--model claude-fable-5-1] [--effort max] [--no-rc]
#                [--wait <seconds, default 120>] [--dry-run]
#   --profile codex types `codex -m <model> -c model_reasoning_effort="<effort>" '<prompt>'` (model and
#   effort default to ~/.codex/config.toml when not given; efforts low|medium|high|xhigh|ultra) and
#   counts the worker as started once a `codex` process carrying the runbook path is running under
#   the pane's shell and is still alive three seconds later.
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

NAME=""; CWD=""; PROMPT=""; PROFILE=cc; MODEL=""; EFFORT=""; RC=1; DRY=0; WAIT=120
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
case "$PROFILE" in
  cc|ccv) MODEL=${MODEL:-claude-fable-5-1}; EFFORT=${EFFORT:-max}
          case "$EFFORT" in low|medium|high|xhigh|max) ;; *) die "--effort must be one of low medium high xhigh max (got '$EFFORT')" ;; esac ;;
  codex)  case "${EFFORT:-low}" in low|medium|high|xhigh|ultra) ;; *) die "--effort for codex must be one of low medium high xhigh ultra (got '$EFFORT')" ;; esac ;;
  *) die "--profile must be cc, ccv or codex" ;;
esac
# model ids are like claude-fable-5-1, claude-fable-5[1m] (Hard Rule 8) or gpt-6-astra; typed inside single quotes
case "$MODEL" in *[!A-Za-z0-9._\[\]-]*) die "--model may use letters, digits, . _ - [ ] only (got '$MODEL')" ;; esac
case "$WAIT" in *[!0-9]*|"") die "--wait must be a whole number of seconds" ;; esac
CWD=$(cd "$CWD" 2>/dev/null && pwd -P) || die "--cwd is not a directory: $CWD"
case "$PROMPT" in /*) ;; *) PROMPT="$CWD/$PROMPT" ;; esac
[ -f "$PROMPT" ] || die "--prompt-file not found: $PROMPT"
case "$PROMPT" in *\'*) die "the runbook path may not contain a single quote" ;; esac
case "$PROFILE" in
  cc) WRAPPER=clauded; REG_DIR="$HOME/.claude/sessions" ;;              # personal config (zsh alias)
  ccv) WRAPPER=clauded-vals; REG_DIR="$HOME/.claude-vals/sessions" ;;   # Vals config (zsh function)
  codex) WRAPPER=codex; REG_DIR=""; RC=0 ;;                            # no registry, no Remote Control
esac
WRAPPER=${DEPLOY_WRAPPER:-$WRAPPER}     # test hook: point at a missing command to exercise the failure path
LAUNCHER=$(command -v byobu || command -v tmux) || die "neither byobu nor tmux is installed"
command -v tmux >/dev/null || die "tmux is not installed"

# Apostrophe-free on purpose: the prompt is typed into the shell inside single quotes.
OPEN="Your task brief is the runbook at $PROMPT. Read it in full first, then carry it out end to end under the repo CLAUDE.md and ~/agents-config/INDEX_RULES.md: keep its results ledger live, keep a resumable CKPT_$NAME.md in the work dir with real Created/Last-updated stamps from date (Trigger Rule 44), run the QA tier it names before pushing, and report with the mandatory TLDR/Snapshot protocol."
CMD="$WRAPPER"
if [ "$PROFILE" = codex ]; then
  [ -n "$MODEL" ] && CMD="$CMD -m '$MODEL'"
  [ -n "$EFFORT" ] && CMD="$CMD -c model_reasoning_effort=\"$EFFORT\""
  CMD="$CMD '$OPEN'"
else
  [ "$RC" -eq 1 ] && CMD="$CMD --remote-control $NAME"
  CMD="$CMD --model '$MODEL' --effort $EFFORT '$OPEN'"
fi

if [ "$DRY" -eq 1 ]; then
  echo "$LAUNCHER new-session -d -s $NAME -c $CWD /bin/zsh -il"
  echo "tmux send-keys -t =$NAME: '<cmd>' Enter"
  if [ -n "$REG_DIR" ]; then echo "then poll $REG_DIR/*.json for a live pid whose tmux field starts with '$NAME:' (up to ${WAIT}s)"
  else echo "then wait until the pane's foreground command is no longer the shell (up to ${WAIT}s)"; fi
  echo "cmd: $CMD"
  exit 0
fi
if tmux has-session -t "=$NAME" 2>/dev/null; then
  echo "deploy_cc.sh: tmux session '$NAME' already exists -- pick another --name, or attach: byobu attach -t $NAME" >&2
  exit 1
fi
# an explicit interactive login zsh: the wrappers are defined in ~/.zshrc, whatever the server default is
"$LAUNCHER" new-session -d -s "$NAME" -c "$CWD" /bin/zsh -il
# wait for the interactive shell to be the pane's foreground command again: ~/.zshrc may run kinit
# and friends first, and keys typed before it finishes can be eaten or misparsed
shell_ready() {
  case "$(tmux display-message -p -t "=$NAME:" '#{pane_current_command}' 2>/dev/null)" in
    zsh|-zsh|bash|-bash|sh|fish) return 0 ;; *) return 1 ;;
  esac
}
t0=$SECONDS
until shell_ready || [ $((SECONDS - t0)) -ge 30 ]; do python3 -c 'import time; time.sleep(1)'; done
shell_ready || echo "deploy_cc.sh: warning: the shell in '$NAME' was still busy after 30s; typing anyway" >&2
python3 -c 'import time; time.sleep(1)'
tmux send-keys -t "=$NAME:" "$CMD" Enter
echo "typed into tmux session '$NAME' ($CWD): $CMD"
echo "waiting up to ${WAIT}s for the $WRAPPER worker to start in that session ..."

# Claude Code writes <config>/sessions/<pid>.json with "tmux":"<session>:@w.%p" while it runs; that
# file plus a live pid is the same evidence the agent board uses, so "deployed" means exactly that.
# codex has no registry: the evidence is a process under the pane's shell whose command line carries
# this runbook's path (so a kinit, sleep or git from ~/.zshrc can never pass), and that is still
# alive three seconds later (so a codex that rejects a flag and exits does not pass).
worker_pid() {
  local pane_pid; pane_pid=$(tmux display-message -p -t "=$NAME:" '#{pane_pid}' 2>/dev/null) || return 1
  python3 - "$pane_pid" "$(basename "$WRAPPER")" "$PROMPT" <<'PY'
import subprocess, sys
root, wrapper, marker = sys.argv[1], sys.argv[2], sys.argv[3]
kids, cmd = {}, {}
for ln in subprocess.run(["ps", "-ax", "-o", "pid=,ppid=,command="], capture_output=True, text=True).stdout.splitlines():
    f = ln.split(None, 2)
    if len(f) == 3:
        kids.setdefault(f[1], []).append(f[0]); cmd[f[0]] = f[2]
todo = [root]
while todo:
    pid = todo.pop()
    for k in kids.get(pid, []):
        c = cmd.get(k, "")
        if marker in c:               # the runbook path is unique to this launch; the wrapper
            print(k); sys.exit(0)     # name may vanish when a launcher execs into a binary
        todo.append(k)
sys.exit(1)
PY
}
registered() {
  if [ -z "$REG_DIR" ]; then
    local pid; pid=$(worker_pid) || return 1
    python3 -c 'import time; time.sleep(3)'
    kill -0 "$pid" 2>/dev/null && { echo "pid $pid"; return 0; }
    return 1
  fi
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
    if [ "$PROFILE" = codex ]; then echo "deployed: codex ($SID) is running in tmux session '$NAME'"
    else echo "deployed: Claude Code session $SID is live in tmux session '$NAME'"; fi
    echo "  attach:  byobu attach -t $NAME        (tmux attach -t '=$NAME' also works; detach with the prefix + d)"
    [ "$RC" -eq 1 ] && echo "  phone:   Remote Control requested under the name '$NAME' -- open it from claude.ai/code"
    echo "  board:   python3 ~/agents-config/scripts/agent_board.py --hours 1   (row: tmux $NAME)"
    exit 0
  fi
  python3 -c 'import time; time.sleep(2)'
done
echo "deploy_cc.sh: NOT verified -- the agent did not start in tmux session '$NAME' within ${WAIT}s." >&2
echo "  last lines of the pane:" >&2
tmux capture-pane -p -t "=$NAME:" 2>/dev/null | grep -v '^$' | tail -6 | sed 's/^/    /' >&2
echo "  inspect: byobu attach -t $NAME      discard: tmux kill-session -t '=$NAME'" >&2
exit 1
