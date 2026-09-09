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
#                [--wait <seconds, default 120>] [--no-preflight] [--dry-run]
#   --profile codex types `codex --dangerously-bypass-approvals-and-sandbox -m <model> -c 'model_reasoning_effort="<effort>"' '<prompt>'` (model and
#   effort default to gpt-6-astra and ultra; efforts low|medium|high|xhigh|ultra) and
#   counts the worker as started once a `codex` process carrying the runbook path is running under
#   the pane's shell and is still alive three seconds later.
# Example (a temporary brief, previewed without starting a worker):
#   brief=$(mktemp "${TMPDIR:-/tmp}/deploy-brief.XXXXXX")
#   printf '# Inspect this repository\n**TLDR:** Summarize tracked files without changing them.\n\nTL;DR: Read the repository and report its structure.\n' > "$brief"
#   ~/agents-config/scripts/deploy_cc.sh --name config-inspect --cwd ~/agents-config \
#     --prompt-file "$brief" --dry-run
#   rm "$brief"
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

usage() { sed -n '2,/^set -/p' "$0" | sed '$d'; }
die() { echo "deploy_cc.sh: $*" >&2; exit 2; }
# a flag that takes a value: the value must exist, be non-empty and not look like another flag
val() { [ $# -ge 2 ] && [ -n "$2" ] && [ "${2#-}" = "$2" ] || die "$1 needs a value (got '${2:-}')"; printf '%s' "$2"; }
# single-quote a value for a shell command line (bash 3.2 has no ${var@Q})
shq() { printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"; }

NAME=""; CWD=""; PROMPT=""; PROFILE=cc; MODEL=""; EFFORT=""; RC=1; DRY=0; WAIT=120; PREFLIGHT=1
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
    --no-preflight) PREFLIGHT=0; shift ;;
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
  codex)  MODEL=${MODEL:-gpt-6-astra}; EFFORT=${EFFORT:-ultra}
          case "$EFFORT" in low|medium|high|xhigh|ultra) ;; *) die "--effort for codex must be one of low medium high xhigh ultra (got '$EFFORT')" ;; esac ;;
  *) die "--profile must be cc, ccv or codex" ;;
esac
# model ids are like claude-fable-5-1, claude-fable-5-1[1m] (Hard Rule 8) or gpt-6-astra; typed inside single quotes
case "$MODEL" in *[!A-Za-z0-9._\[\]-]*) die "--model may use letters, digits, . _ - [ ] only (got '$MODEL')" ;; esac
case "$WAIT" in *[!0-9]*|"") die "--wait must be a whole number of seconds" ;; esac
# Force decimal arithmetic: a valid value such as 08 must not be interpreted as octal.
WAIT=$((10#$WAIT))
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
OPEN="Your task brief is the runbook at $PROMPT. Read it in full first, then carry it out end to end under the repo CLAUDE.md and ~/agents-config/INDEX_RULES.md: keep its results ledger live, keep a resumable CKPT_$NAME.md in the work dir with real Created/Last-updated stamps from date (Trigger Rule 44), run the QA tier it names before pushing, and report with the mandatory TLDR/Snapshot protocol. TL;DR: Complete the runbook, maintain the results and checkpoint, verify the work, and report the outcome."
CMD="$WRAPPER"
if [ "$PROFILE" = codex ]; then
  CMD="$CMD --dangerously-bypass-approvals-and-sandbox -m '$MODEL' -c 'model_reasoning_effort=\"$EFFORT\"'"
  CMD="$CMD '$OPEN'"
else
  [ "$RC" -eq 1 ] && CMD="$CMD --remote-control $NAME"
  CMD="$CMD --model '$MODEL' --effort $EFFORT '$OPEN'"
fi

# Print shell-replayable arguments, including spaces and the literal command sent to zsh.
print_cmd() { printf '%q ' "$@"; printf '\n'; }
if [ "$DRY" -eq 1 ]; then
  print_cmd "$LAUNCHER" new-session -d -s "$NAME" -c "$CWD" /bin/zsh -il
  print_cmd tmux send-keys -l -t "=$NAME:" "$CMD"
  print_cmd tmux send-keys -t "=$NAME:" Enter
  echo "# Wait for the shell, then verify a non-zombie worker below the pane with stable process identity (up to ${WAIT}s)."
  if [ -n "$REG_DIR" ]; then
    printf '# Require a matching Claude registry entry in %s and process start time.\n' "$REG_DIR"
  else
    printf '# Require a Codex process carrying runbook %s on both checks, three seconds apart.\n' "$PROMPT"
  fi
  exit 0
fi
if tmux has-session -t "=$NAME" 2>/dev/null; then
  echo "deploy_cc.sh: tmux session '$NAME' already exists -- pick another --name, or attach: byobu attach -t $NAME" >&2
  exit 1
fi
# Pre-flight: a model with no usage left accepts the session, registers, and then dies on its first
# turn -- which is how four workers were lost overnight on 2026-09-08 while their dispatcher believed
# they were running. One cheap probe here turns that silent loss into a refusal to deploy.
# FAIL CLOSED: only an actual PONG proceeds. Claude Code words exhaustion several ways ("out of usage
# credits", "monthly spend limit", "usage limit reached"), so matching known phrases lets tomorrow's
# wording through; anything that is not PONG is treated as unusable and --no-preflight is the escape.
if [ "$PREFLIGHT" -eq 1 ] && [ "$PROFILE" != codex ]; then
  # bounded: a hung shell, hook or request must not wedge the dispatch (no deadline = no guard)
  if command -v timeout >/dev/null; then RUNNER="timeout 90"
  elif command -v gtimeout >/dev/null; then RUNNER="gtimeout 90"
  else RUNNER=""; fi
  # same shell the worker gets (interactive login zsh, in the worker's cwd), so the wrapper resolves
  # the same way and a cwd-specific hook or rc file cannot make the probe and the session disagree
  probe=$($RUNNER zsh -ilc "cd $(shq "$CWD") && $WRAPPER --model $(shq "$MODEL") -p 'reply with exactly: PONG'" \
            < /dev/null 2>&1 | tail -3 || true)
  case "$probe" in
    *PONG*) ;;
    *)
      echo "deploy_cc.sh: $MODEL did not answer a probe -- not deploying '$NAME'." >&2
      echo "  probe said: $(printf '%s' "$probe" | tr '\n' ' ' | cut -c1-160)" >&2
      echo "  if that is a usage/credit limit, try another Claude model (--model claude-opus-5) or" >&2
      echo "  --profile codex, per Hard Rule 8; never fall back to API keys. If the probe itself is" >&2
      echo "  broken (empty answer, hung shell), re-run with --no-preflight." >&2
      exit 3 ;;
  esac
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
tmux send-keys -l -t "=$NAME:" "$CMD"
tmux send-keys -t "=$NAME:" Enter
echo "typed into tmux session '$NAME' ($CWD): $CMD"
echo "waiting up to ${WAIT}s for the $WRAPPER worker to start in that session ..."

# Both profiles must identify an actual, non-zombie agent under this pane twice. A live
# unrelated process, a recycled registry pid, or a shell mentioning the runbook is insufficient.
worker_identity() {
  local pane_pid; pane_pid=$(tmux display-message -p -t "=$NAME:" '#{pane_pid}' 2>/dev/null) || return 1
  python3 - "$pane_pid" "$(basename "$WRAPPER")" "$PROMPT" "$REG_DIR" "$NAME" <<'PYTHON'
import calendar, glob, json, os, shlex, subprocess, sys, time
root, wrapper, marker, reg, name = sys.argv[1:]
try:
    result = subprocess.run(
        ["ps", "-ax", "-o", "pid=,ppid=,stat=,lstart=,command="],
        env=dict(os.environ, LC_ALL="C"), capture_output=True, text=True, timeout=5,
        check=True,
    )
except (OSError, subprocess.SubprocessError):
    sys.exit(1)
processes, children = {}, {}
for line in result.stdout.splitlines():
    fields = line.split(None, 8)
    if len(fields) != 9:
        continue
    pid, parent, state = fields[:3]
    if state.startswith(("Z", "X")):
        continue
    stamp = " ".join(fields[3:8])
    try:
        started = time.mktime(time.strptime(stamp, "%a %b %d %H:%M:%S %Y"))
    except ValueError:
        continue
    processes[pid] = (started, fields[8])
    children.setdefault(parent, []).append(pid)

def is_agent(command):
    try:
        words = shlex.split(command)
    except ValueError:
        return False
    if not words:
        return False
    family = "claude" if reg else "codex"
    expected = {wrapper, family, family + ".exe"}
    # Native binaries, and the Node/Python/shell launchers used by packaged commands.
    executable = os.path.basename(words[0])
    if executable in expected:
        return True
    if len(words) < 2:
        return False
    if executable in {"node", "nodejs"}:
        entrypoint = words[1].replace("\\", "/")
        package_script = ("/@anthropic-ai/claude-code/cli.js" if reg
                          else "/@openai/codex/bin/codex.js")
        if entrypoint.endswith(package_script):
            return True
    return (executable in {"node", "nodejs", "python3", "python", "bash", "sh"}
            and os.path.basename(words[1]) in expected)

candidates, todo, seen = {}, [root], set()
while todo:
    pid = todo.pop()
    if pid in seen:
        continue
    seen.add(pid)
    info = processes.get(pid)
    if info and is_agent(info[1]) and (reg or marker in info[1]):
        candidates[pid] = info
    todo.extend(children.get(pid, []))
if not reg:
    for pid, (started, _) in candidates.items():
        print(f"pid {pid} start {started:.0f}")
        sys.exit(0)
else:
    for filename in glob.glob(os.path.join(reg, "*.json")):
        try:
            with open(filename) as stream:
                entry = json.load(stream)
            if not isinstance(entry, dict):
                continue
            pid = str(entry.get("pid") or "")
            sid = entry.get("sessionId")
            if pid not in candidates or not isinstance(sid, str) or not sid:
                continue
            if str(entry.get("tmux", "")).split(":", 1)[0] != name:
                continue
            if entry.get("startedAt"):
                started = float(entry["startedAt"]) / 1000
            else:
                started = calendar.timegm(time.strptime(entry["procStart"], "%a %b %d %H:%M:%S %Y"))
            actual_started = candidates[pid][0]
            if abs(actual_started - started) > 120:
                continue
            print(f"{sid[:8]} pid {pid} start {actual_started:.0f}")
            sys.exit(0)
        except (OSError, KeyError, TypeError, ValueError):
            continue
sys.exit(1)
PYTHON
}
registered() {
  local before after
  before=$(worker_identity) || return 1
  python3 -c 'import time; time.sleep(3)'
  after=$(worker_identity) || return 1
  [ "$before" = "$after" ] || return 1
  printf '%s\n' "$after"
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
tmux capture-pane -p -t "=$NAME:" 2>/dev/null | grep -v '^$' | tail -6 | sed 's/^/    /' >&2 || true
echo "  inspect: byobu attach -t $NAME      discard: tmux kill-session -t '=$NAME'" >&2
exit 1
