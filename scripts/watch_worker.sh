#!/usr/bin/env bash
# TLDR: watch one dispatched agent worker (Claude Code or Codex in a tmux session) until a TERMINAL state and
# say which: DONE (deliverables written, agent no longer busy), DEAD (session gone), BLOCKED (usage/credit/
# rate-limit/auth message at its idle prompt), IDLE (finished its turn without the deliverables) or TIMEOUT.
# A live process is not progress: an interactive Claude Code session that runs out of credits stays alive at
# its prompt, so success-file waits and process checks both miss it (Trigger Rule 69, Brando 10-09-2026).
#
# Usage:
#   watch_worker.sh --session <tmux-name> --deliverable <path> [--deliverable <path> ...]
#                   [--interval <seconds, default 30>] [--idle-checks <n, default 3>] [--timeout <seconds, 0 = none>]
# Exit codes: 0 DONE, 1 DEAD, 2 BLOCKED, 3 IDLE, 4 TIMEOUT, 64 usage error. One line "STATE: detail" on stdout.
# Busy signal: both Claude Code and Codex show "esc to interrupt" only while a turn is running.
# Use it as a Bash run_in_background / Monitor command, or in a cron watchdog; on any non-zero exit,
# recover under Trigger Rule 58 (next eligible account or model; deploy_cc.sh's preflight probe first).
set -u
SESSION="" INTERVAL=30 IDLE_CHECKS=3 TIMEOUT=0
DELIVERABLES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --session) SESSION="$2"; shift 2 ;;
    --deliverable) DELIVERABLES+=("$2"); shift 2 ;;
    --interval) INTERVAL="$2"; shift 2 ;;
    --idle-checks) IDLE_CHECKS="$2"; shift 2 ;;
    --timeout) TIMEOUT="$2"; shift 2 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "watch_worker.sh: unknown argument $1" >&2; exit 64 ;;
  esac
done
if [ -z "$SESSION" ] || [ ${#DELIVERABLES[@]} -eq 0 ]; then
  echo "watch_worker.sh: --session and at least one --deliverable are required" >&2; exit 64
fi
LIMIT_RE='out of usage|usage credits|usage limit|spend limit|rate limit|rate-limited|hit your|quota exceeded|insufficient_quota|unauthorized|authentication (failed|error)|please (run )?/?login|log in again|credit balance'
start=$(date +%s)
idle=0
all_written() {
  local f
  for f in "${DELIVERABLES[@]}"; do [ -s "$f" ] || return 1; done
  return 0
}
while :; do
  if ! tmux has-session -t "=$SESSION" 2>/dev/null; then
    if all_written; then echo "DONE: deliverables present; session $SESSION already closed"; exit 0; fi
    echo "DEAD: tmux session $SESSION is gone and deliverables are missing"; exit 1
  fi
  tail_lines=$(tmux capture-pane -p -t "=$SESSION:" -S -60 2>/dev/null | grep -v '^[[:space:]]*$' | tail -15)
  if [ -z "$tail_lines" ]; then sleep "$INTERVAL"; continue; fi  # capture failed or blank pane: unknown, not idle
  busy=0
  printf '%s' "$tail_lines" | grep -q "esc to interrupt" && busy=1
  if [ $busy -eq 0 ]; then
    if all_written; then echo "DONE: deliverables present and $SESSION is idle"; exit 0; fi
    hit=$(printf '%s' "$tail_lines" | grep -iE "$LIMIT_RE" | tail -1 | cut -c1-200)
    if [ -n "$hit" ]; then echo "BLOCKED: $SESSION idle with a limit/auth message: $hit"; exit 2; fi
    idle=$((idle + 1))
    if [ "$idle" -ge "$IDLE_CHECKS" ]; then
      echo "IDLE: $SESSION finished its turn without the deliverables (${IDLE_CHECKS} consecutive idle checks)"; exit 3
    fi
  else
    idle=0
  fi
  if [ "$TIMEOUT" -gt 0 ] && [ $(( $(date +%s) - start )) -ge "$TIMEOUT" ]; then
    echo "TIMEOUT: $SESSION still $([ $busy -eq 1 ] && echo busy || echo idle) after ${TIMEOUT}s"; exit 4
  fi
  sleep "$INTERVAL"
done
