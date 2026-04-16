#!/usr/bin/env bash
# git-inbox-poller.sh — bridge from a git-tracked phone-submission inbox into
# the DFS job watcher queue.
#
# Purpose: enable job dispatch from contexts that cannot SSH into the cluster
# (e.g. claude.ai on a phone, Anthropic cloud sandbox without Kerberos). The
# submitting agent commits a job file to the agents-config repo under
# `jobs-inbox/pending/*.sh`; this poller pulls the repo every N seconds on a
# cluster node and hands any new job files to the local DFS watcher queue
# (~/dfs/job_queue/pending/), where smart-mode agent wrapping takes over.
#
# Usage:
#   bash ~/agents-config/scripts/git-inbox-poller.sh                # defaults
#   bash ~/agents-config/scripts/git-inbox-poller.sh --interval 15  # poll 15s
#
# Recommended: run in a tmux session named git_inbox_poller:
#   tmux new -d -s git_inbox_poller "bash ~/agents-config/scripts/git-inbox-poller.sh"
#   tmux attach -t git_inbox_poller
#
# The poller emits heartbeats into
#   /dfs/scratch0/$USER/job_queue/git_inbox_heartbeat.json
# so you can check from any node that the bridge is alive.
#
# SECURITY NOTE: this runs any *.sh that appears in jobs-inbox/pending/ of the
# tracked git repo. Anyone with push access to that repo can execute arbitrary
# code on the cluster as your user. The agents-config repo is assumed to be
# private and write-restricted to Brando. If you fork or share the repo, move
# the inbox to a dedicated private repo.

set -euo pipefail

# ── defaults ─────────────────────────────────────────────────────────────
INTERVAL=30
INBOX_DIR="$HOME/agents-config/jobs-inbox"
PENDING_DIR="$INBOX_DIR/pending"
DISPATCHED_DIR="$INBOX_DIR/dispatched"
DFS_QUEUE_PENDING="$HOME/dfs/job_queue/pending"
HEARTBEAT="$HOME/dfs/job_queue/git_inbox_heartbeat.json"
LOG="$HOME/dfs/job_queue/logs/git_inbox_poller.log"

# ── arg parse ────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --interval) INTERVAL="$2"; shift 2 ;;
        --inbox)    INBOX_DIR="$2"; PENDING_DIR="$2/pending"; DISPATCHED_DIR="$2/dispatched"; shift 2 ;;
        -h|--help)  sed -n '2,30p' "$0"; exit 0 ;;
        *)          echo "git-inbox-poller: unknown arg: $1" >&2; exit 2 ;;
    esac
done

# ── sanity ───────────────────────────────────────────────────────────────
if [[ ! -d "$HOME/agents-config/.git" ]]; then
    echo "git-inbox-poller: $HOME/agents-config is not a git repo — aborting" >&2
    exit 3
fi
if [[ ! -d "$HOME/dfs" ]]; then
    echo "git-inbox-poller: ~/dfs symlink missing — aborting" >&2
    echo "  fix: ln -sfn /dfs/scratch0/\$USER ~/dfs" >&2
    exit 3
fi

mkdir -p "$PENDING_DIR" "$DISPATCHED_DIR" "$DFS_QUEUE_PENDING" "$(dirname "$LOG")" "$(dirname "$HEARTBEAT")"

# .keep files so the empty dirs are checked in
: > "$PENDING_DIR/.keep" || true
: > "$DISPATCHED_DIR/.keep" || true

log() { echo "[$(date -Is)] $*" | tee -a "$LOG"; }

heartbeat() {
    cat > "$HEARTBEAT" <<EOF
{
  "hostname": "$(hostname)",
  "pid": $$,
  "state": "$1",
  "interval_s": $INTERVAL,
  "inbox": "$INBOX_DIR",
  "dfs_queue": "$DFS_QUEUE_PENDING",
  "last_heartbeat": "$(date -Is)",
  "dispatched_this_run": $DISPATCHED_COUNT
}
EOF
}

DISPATCHED_COUNT=0
trap 'heartbeat "STOPPED"; log "poller stopping (received signal)"; exit 0' INT TERM
heartbeat "STARTING"
log "git-inbox-poller starting on $(hostname), interval=${INTERVAL}s"
log "  inbox:     $INBOX_DIR"
log "  dfs queue: $DFS_QUEUE_PENDING"

# ── main loop ────────────────────────────────────────────────────────────
while true; do
    # Pull latest commits. --rebase to avoid merge commits from our own pushes.
    # --autostash to survive any unexpected local changes.
    pull_out=$(cd "$HOME/agents-config" && git pull --rebase --autostash 2>&1) || {
        log "git pull failed: $pull_out"
        heartbeat "PULL_FAILED"
        sleep "$INTERVAL"
        continue
    }

    # Find new .sh files in pending/ (ignore .keep, .md, dotfiles).
    shopt -s nullglob
    new_jobs=("$PENDING_DIR"/*.sh)
    shopt -u nullglob

    if [[ ${#new_jobs[@]} -gt 0 ]]; then
        for job in "${new_jobs[@]}"; do
            base="$(basename "$job")"
            stamp="$(date +%Y-%m-%d__%H-%M-%S)"
            queued_name="${stamp}__${base}"
            dispatched_name="${stamp}__${base}"

            log "dispatching $base → $DFS_QUEUE_PENDING/$queued_name"
            # Copy (not mv) to DFS queue — DFS is a different FS, cross-FS mv is rename+unlink anyway.
            cp "$job" "$DFS_QUEUE_PENDING/$queued_name"
            chmod +x "$DFS_QUEUE_PENDING/$queued_name" || true

            # Move the source file into dispatched/ in the git repo, commit, push.
            mv "$job" "$DISPATCHED_DIR/$dispatched_name"
            (
                cd "$HOME/agents-config"
                git add "jobs-inbox/pending/$base" "jobs-inbox/dispatched/$dispatched_name" 2>/dev/null || true
                git -c user.name="git-inbox-poller" \
                    -c user.email="brando9@stanford.edu" \
                    commit -m "inbox: dispatch $base on $(hostname)" \
                    --author="git-inbox-poller <brando9@stanford.edu>" \
                    -- "jobs-inbox/pending/$base" "jobs-inbox/dispatched/$dispatched_name" \
                    >/dev/null 2>&1 || log "commit skipped (nothing to commit?)"
                git push origin HEAD >/dev/null 2>&1 || log "push failed (will retry next tick)"
            )
            DISPATCHED_COUNT=$((DISPATCHED_COUNT + 1))
            log "dispatched $base (total this run: $DISPATCHED_COUNT)"
        done
    fi

    heartbeat "RUNNING"
    sleep "$INTERVAL"
done
