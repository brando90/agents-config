#!/usr/bin/env bash
# TLDR: Launch a long-running job on a SNAP cluster node inside a detached tmux session so it
# survives SSH disconnects and the laptop sleeping/shutting down; also list/attach/tail/kill jobs.
#
# WHY: Brando's laptops sleep or power off mid-run even with keep-awake apps, killing any job
# hosted locally or attached to a live SSH channel. The fix is to make the laptop a thin client:
# the job lives in tmux on a cluster node, logs to node-local /lfs, and keeps running when the
# laptop disappears.
#
# USAGE
#   scripts/snap_dispatch.sh run   <job-name> <command...>   # start a detached job
#   scripts/snap_dispatch.sh list                            # all jobs on all nodes
#   scripts/snap_dispatch.sh tail  <job-name>                # follow a job's log
#   scripts/snap_dispatch.sh log   <job-name>                # print full log path + tail
#   scripts/snap_dispatch.sh attach <job-name>               # attach to the live tmux session
#   scripts/snap_dispatch.sh kill  <job-name>                # stop a job
#   scripts/snap_dispatch.sh nodes                           # node health (load/disk/gpu/auth)
#
# ENV
#   SNAP_HOST   target node (default: skampere1). Any of skampere1|skampere2|skampere3|mercury1.
#   SNAP_SSH_USER   remote account (default: brando9, also used for node-local logs).
#
# EXAMPLES
#   SNAP_HOST=skampere3 scripts/snap_dispatch.sh run vb_oracle \
#       'cd /lfs/skampere3/0/brando9/harbor_jobs && harbor run -d veribench@1.3 -a oracle -m none'
#   scripts/snap_dispatch.sh tail vb_oracle

set -euo pipefail

SNAP_HOST="${SNAP_HOST:-skampere1}"
SNAP_SSH_USER="${SNAP_SSH_USER:-brando9}"
SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=60)
ALL_NODES=(skampere1 skampere2 skampere3 mercury1)

die() { echo "ERROR: $*" >&2; exit 1; }

# Remote log dir lives on node-local /lfs, never DFS/NFS: writes keep working after the
# laptop's Kerberos ticket expires, and Harbor requires /lfs anyway (NFS root-squash).
remote_logdir() { echo "/lfs/${1}/0/${SNAP_SSH_USER}/snap_jobs"; }

case "$SNAP_HOST" in skampere1|skampere2|skampere3|mercury1) ;; *) die "unsupported SNAP_HOST: $SNAP_HOST" ;; esac
[[ "$SNAP_SSH_USER" =~ ^[A-Za-z_][A-Za-z0-9_-]*$ ]] || die "invalid SNAP_SSH_USER"
valid_name() {
  # tmux rewrites dots in session names, and target prefixes may select another job.
  [[ "${1:-}" =~ ^[A-Za-z0-9_][A-Za-z0-9_-]*$ ]] || die "job name must use letters, digits, _ or - and must not start with -"
}

preflight() {
  local host="$1"
  ssh "${SSH_OPTS[@]}" "${SNAP_SSH_USER}@${host}.stanford.edu" true 2>/dev/null \
    || die "cannot SSH to ${host}. Is the Stanford VPN up and 'klist' showing a valid ticket?"
}

cmd_run() {
  local name="${1:-}"; shift || true
  local job_cmd
  if [ "$#" -eq 1 ]; then job_cmd="$1"  # One argument is a shell program, as in the examples.
  else printf -v job_cmd '%q ' "$@"; fi  # Multiple arguments retain their individual boundaries.
  [[ -n "$name"    ]] || die "usage: run <job-name> <command...>"
  [[ "$#" -gt 0 && -n "$job_cmd" ]] || die "no command given"
  valid_name "$name"

  preflight "$SNAP_HOST"
  local logdir; logdir="$(remote_logdir "$SNAP_HOST")"
  local stamp;  stamp="$(date +%Y-%m-%d_%H-%M-%S)"
  local log="${logdir}/${name}_${stamp}.log"

  # Guard: refuse to start if a session with this name already exists, so we never end up with
  # two harbor runs on one host (that corrupts verifier output -> empty results).
  if ssh "${SSH_OPTS[@]}" "${SNAP_SSH_USER}@${SNAP_HOST}.stanford.edu" "tmux has-session -t '=$name' 2>/dev/null"; then
    die "job '$name' already running on $SNAP_HOST. Use 'kill' first, or pick another name."
  fi

  # The job command travels base64-encoded and is written to a runner script on the node. This
  # avoids every layer of nested shell quoting (local shell -> ssh -> tmux -> bash), which
  # otherwise silently mangles $VARS and $(substitutions) inside the user's command.
  local payload; payload="$(printf '%s' "$job_cmd" | base64 | tr -d '\n')"

  ssh "${SSH_OPTS[@]}" "${SNAP_SSH_USER}@${SNAP_HOST}.stanford.edu" bash -s -- \
      "$name" "$logdir" "$log" "$payload" <<'REMOTE'
set -euo pipefail
name="$1"; logdir="$2"; log="$3"; payload="$4"
mkdir -p "$logdir"
# Serialize the duplicate check and file writes on the node. A losing launch cannot
# overwrite the active job's runner or latest-log link, even if both preflights passed.
lock="$logdir/.${name}.launch-lock"
mkdir "$lock" 2>/dev/null || { echo "launch already in progress for '$name' (lock: $lock)" >&2; exit 1; }
trap 'rmdir "$lock"' EXIT
if tmux has-session -t "=$name" 2>/dev/null; then
  echo "job '$name' already running" >&2
  exit 1
fi
runner=$(mktemp "$logdir/${name}_runner.XXXXXX")
{
  echo '#!/usr/bin/env bash'
  echo "exec > >(tee -a '$log') 2>&1"
  echo "echo \"[snap_dispatch] host=\$(hostname -s) start=\$(date -Is)\""
  echo '('
  printf '%s\n' "$payload" | base64 -d
  echo ''
  echo ')'
  echo "rc=\$?; echo \"[snap_dispatch] exit=\$rc end=\$(date -Is)\""
  # Propagate the job's status: without this the runner exits with the status of the echo above,
  # so a failed job looks like a clean one to tmux's remain-on-exit pane and to anything polling it.
  echo 'exit "$rc"'
} > "$runner"
chmod +x "$runner"
# tmux detaches the process from this SSH channel, so it survives disconnect / laptop sleep.
# bash -l gives the login PATH (nvm/node for claude+codex, ~/.local/bin for harbor).
# Configure remain-on-exit in the same server command queue, before it processes a
# fast child's exit; otherwise even `true` may destroy the session before set-option.
tmux new-session -d -s "$name" "bash -l '$runner'" \; \
  set-option -t "=$name:" remain-on-exit on >/dev/null
ln -sfn "$log" "$logdir/${name}_latest.log"
echo "started tmux session '$name' on $(hostname -s)"
REMOTE

  cat <<EOF

  job     : $name
  node    : $SNAP_HOST
  log     : $log
  latest  : ${logdir}/${name}_latest.log

  follow  : SNAP_HOST=$SNAP_HOST SNAP_SSH_USER=$SNAP_SSH_USER $0 tail $name
  attach  : SNAP_HOST=$SNAP_HOST SNAP_SSH_USER=$SNAP_SSH_USER $0 attach $name
  stop    : SNAP_HOST=$SNAP_HOST SNAP_SSH_USER=$SNAP_SSH_USER $0 kill $name

  Safe to close the laptop now — the job runs on $SNAP_HOST, not here.
EOF
}

cmd_list() {
  for h in "${ALL_NODES[@]}"; do
    printf '=== %s ===\n' "$h"
    ssh "${SSH_OPTS[@]}" "${SNAP_SSH_USER}@${h}.stanford.edu" \
      "tmux ls 2>/dev/null || echo '  (no tmux sessions)'" 2>/dev/null \
      || echo '  (unreachable)'
  done
}

cmd_tail() {
  local name="${1:-}"; valid_name "$name"
  preflight "$SNAP_HOST"
  local logdir; logdir="$(remote_logdir "$SNAP_HOST")"
  ssh -t "${SSH_OPTS[@]}" "${SNAP_SSH_USER}@${SNAP_HOST}.stanford.edu" \
    "tail -f '${logdir}/${name}_latest.log'"
}

cmd_log() {
  local name="${1:-}"; valid_name "$name"
  local logdir; logdir="$(remote_logdir "$SNAP_HOST")"
  ssh "${SSH_OPTS[@]}" "${SNAP_SSH_USER}@${SNAP_HOST}.stanford.edu" \
    "ls -la '${logdir}/${name}'*.log 2>/dev/null; echo '--- tail ---'; tail -40 '${logdir}/${name}_latest.log' 2>/dev/null || echo '(no log yet)'"
}

cmd_attach() {
  local name="${1:-}"; valid_name "$name"
  echo "Attaching to '$name' on $SNAP_HOST. Detach with Ctrl-b then d (do NOT Ctrl-c)."
  ssh -t "${SSH_OPTS[@]}" "${SNAP_SSH_USER}@${SNAP_HOST}.stanford.edu" "tmux attach -t '=$name'"
}

cmd_kill() {
  local name="${1:-}"; valid_name "$name"
  ssh "${SSH_OPTS[@]}" "${SNAP_SSH_USER}@${SNAP_HOST}.stanford.edu" \
    "tmux kill-session -t '=$name' && echo 'killed $name'"
}

cmd_nodes() {
  printf '%-11s %-9s %-7s %-16s %-9s %s\n' NODE LOAD1 CORES FREE_LFS DOCKER CLAUDE_CREDS
  for h in "${ALL_NODES[@]}"; do
    ssh "${SSH_OPTS[@]}" "${SNAP_SSH_USER}@${h}.stanford.edu" bash -s <<'REMOTE' 2>/dev/null || printf '%-11s (unreachable)\n' "$h"
load=$(awk '{print $1}' /proc/loadavg)
cores=$(nproc)
free=$(df -h "/lfs/$(hostname -s)/0" 2>/dev/null | tail -1 | awk '{print $4" ("$5")"}')
if command -v docker >/dev/null && docker ps >/dev/null 2>&1; then d=ok; else d=NO; fi
if [ -f "$HOME/.claude/.credentials.json" ]; then c=present; else c=NONE; fi
printf '%-11s %-9s %-7s %-16s %-9s %s\n' "$(hostname -s)" "$load" "$cores" "$free" "$d" "$c"
REMOTE
  done
  echo
  echo "NOTE: CLAUDE_CREDS='present' only means a credentials file exists, not that the token is valid."
  echo "      Verify liveness with:  ssh <node>.stanford.edu 'bash -lc \"claude -p PONG\"'"
}

case "${1:-}" in
  run)    shift; cmd_run    "$@" ;;
  list)   shift; cmd_list   "$@" ;;
  tail)   shift; cmd_tail   "$@" ;;
  log)    shift; cmd_log    "$@" ;;
  attach) shift; cmd_attach "$@" ;;
  kill)   shift; cmd_kill   "$@" ;;
  nodes)  shift; cmd_nodes  "$@" ;;
  *) sed -n '2,30p' "$0"; exit 1 ;;
esac
