#!/usr/bin/env bash
# TLDR: Audit Sherlock cluster connection, identity, quotas, partitions, and test Slurm batch execution.

set -euo pipefail

SHERLOCK_HOST="${SHERLOCK_HOST:-sherlock}"

log() {
  printf '[sherlock_preflight] %s\n' "$*"
}

warn() {
  printf '[sherlock_preflight] [WARN] %s\n' "$*" >&2
}

err() {
  printf '[sherlock_preflight] [ERROR] %s\n' "$*" >&2
}

check_socket() {
  log "Checking SSH ControlMaster socket for host '$SHERLOCK_HOST'..."
  if ssh -O check "$SHERLOCK_HOST" 2>/dev/null; then
    log "ControlMaster socket is active."
    return 0
  else
    warn "No active ControlMaster socket found."
    warn "Please authenticate once from your terminal (password + Duo push):"
    warn "    ssh $SHERLOCK_HOST"
    warn "Once logged in, ControlPersist keeps the connection active for 12 hours."
    return 1
  fi
}

check_identity() {
  log "Testing identity and cluster paths..."
  ssh "$SHERLOCK_HOST" 'hostname; whoami; id; echo "HOME: $HOME | SCRATCH: $SCRATCH | GROUP_HOME: $GROUP_HOME"'
}

check_partitions_and_quota() {
  log "Querying partitions (sh_part) and storage quotas (sh_quota)..."
  ssh "$SHERLOCK_HOST" 'sh_part; sh_quota'
}

test_python_module() {
  log "Testing module environment (Lmod) and Python..."
  ssh "$SHERLOCK_HOST" 'ml spider python 2>&1 | head -n 20'
}

run_cpu_job() {
  log "Submitting test CPU sbatch job to partition normal..."
  local job_output
  job_output=$(ssh "$SHERLOCK_HOST" 'sbatch --partition=normal --time=00:05:00 --job-name=preflight_cpu --output=preflight_cpu_%j.out --wrap="hostname; date"')
  log "$job_output"
  local job_id
  job_id=$(echo "$job_output" | grep -oE '[0-9]+' | tail -n 1)
  if [ -n "$job_id" ]; then
    log "Monitoring job ID $job_id with sacct..."
    for _ in {1..5}; do
      sleep 60   # >=60 s between sacct polls (Sherlock anti-spam rule)
      local state
      state=$(ssh "$SHERLOCK_HOST" "sacct -j $job_id --format=State --noheader | head -n 1 | tr -d ' '")
      log "Job $job_id state: $state"
      if [ "$state" = "COMPLETED" ]; then
        log "CPU Job completed successfully. Output:"
        ssh "$SHERLOCK_HOST" "cat preflight_cpu_${job_id}.out; rm -f preflight_cpu_${job_id}.out"
        return 0
      elif [ "$state" = "FAILED" ] || [ "$state" = "CANCELLED" ] || [ "$state" = "TIMEOUT" ]; then
        err "Job $job_id ended with state: $state"
        return 1
      fi
    done
    warn "Job $job_id is still queued/running. Check status with: ssh $SHERLOCK_HOST 'squeue -j $job_id'"
  fi
}

run_gpu_job() {
  log "Submitting test GPU sbatch job to partition gpu..."
  local job_output
  job_output=$(ssh "$SHERLOCK_HOST" 'sbatch --partition=gpu --gpus=1 --time=00:10:00 --job-name=preflight_gpu --output=preflight_gpu_%j.out --wrap="nvidia-smi"')
  log "$job_output"
  local job_id
  job_id=$(echo "$job_output" | grep -oE '[0-9]+' | tail -n 1)
  if [ -n "$job_id" ]; then
    log "Monitoring GPU job ID $job_id..."
    for _ in {1..10}; do
      sleep 60   # >=60 s between sacct polls (Sherlock anti-spam rule)
      local state
      state=$(ssh "$SHERLOCK_HOST" "sacct -j $job_id --format=State --noheader | head -n 1 | tr -d ' '")
      log "Job $job_id state: $state"
      if [ "$state" = "COMPLETED" ]; then
        log "GPU Job completed successfully. Output:"
        ssh "$SHERLOCK_HOST" "cat preflight_gpu_${job_id}.out; rm -f preflight_gpu_${job_id}.out"
        return 0
      elif [ "$state" = "FAILED" ] || [ "$state" = "CANCELLED" ] || [ "$state" = "TIMEOUT" ]; then
        err "Job $job_id ended with state: $state"
        return 1
      fi
    done
    warn "GPU job $job_id is currently queued/pending. Check with: ssh $SHERLOCK_HOST 'squeue -j $job_id'"
  fi
}

main() {
  if ! check_socket; then
    exit 1
  fi

  check_identity
  echo ""
  check_partitions_and_quota
  echo ""
  test_python_module

  if [ "${1:-}" = "--jobs" ]; then
    echo ""
    run_cpu_job
    echo ""
    run_gpu_job
  fi
}

main "$@"
