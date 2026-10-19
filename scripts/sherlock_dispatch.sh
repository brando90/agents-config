#!/usr/bin/env bash
# TLDR: Launch, monitor, log, and cancel Slurm jobs on Stanford Sherlock HPC with the same simple UX as snap_dispatch.sh.
#
# USAGE
#   scripts/sherlock_dispatch.sh run <job-name> '<command...>' [--gpu <N>] [--partition <part>] [--time <limit>] [--mem <size>] [--cpus <N>]
#   scripts/sherlock_dispatch.sh list                         # list all active/pending jobs for the user
#   scripts/sherlock_dispatch.sh status <job-name>            # check status of a specific job
#   scripts/sherlock_dispatch.sh tail <job-name>              # follow/stream output log
#   scripts/sherlock_dispatch.sh log <job-name>               # print latest output log lines
#   scripts/sherlock_dispatch.sh kill <job-name>              # cancel a job by name or job ID
#   scripts/sherlock_dispatch.sh nodes                        # show partition & GPU availability
#
# EXAMPLES
#   scripts/sherlock_dispatch.sh run my-train 'python train.py --epochs 10' --gpu 1
#   scripts/sherlock_dispatch.sh run quick-test 'python test.py' --gpu 1 --dev
#   scripts/sherlock_dispatch.sh list
#   scripts/sherlock_dispatch.sh tail my-train
#   scripts/sherlock_dispatch.sh kill my-train

set -euo pipefail

SHERLOCK_HOST="${SHERLOCK_HOST:-sherlock}"
SHERLOCK_USER="${SHERLOCK_USER:-brando9}"
SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=60)

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

check_connection() {
  if ! ssh -O check "$SHERLOCK_HOST" 2>/dev/null; then
    die "SSH master connection to '$SHERLOCK_HOST' is not active. Authenticate once via: ssh $SHERLOCK_HOST (SMS passcode will be auto-read from Google Messages)."
  fi
}

valid_name() {
  [[ "${1:-}" =~ ^[A-Za-z0-9_][A-Za-z0-9_-]*$ ]] || die "Job name must use letters, digits, _ or - and cannot start with -"
}

remote_dir() {
  local name="$1"
  echo "/scratch/users/${SHERLOCK_USER}/sherlock_jobs/${name}"
}

cmd_run() {
  local name="${1:-}"
  [[ -n "$name" ]] || die "usage: run <job-name> '<command>' [--gpu <N>] [--partition <part>] [--time <HH:MM:SS>] [--mem <size>] [--cpus <N>] [--dev]"
  valid_name "$name"
  shift

  local job_cmd="${1:-}"
  [[ -n "$job_cmd" ]] || die "No command given to run"
  shift

  local gpu=""
  local partition=""
  local time_limit=""
  local mem="16G"
  local cpus="4"
  local is_dev=0

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --gpu)
        gpu="${2:-1}"
        shift 2
        ;;
      --dev)
        is_dev=1
        shift
        ;;
      --partition)
        partition="$2"
        shift 2
        ;;
      --time)
        time_limit="$2"
        shift 2
        ;;
      --mem)
        mem="$2"
        shift 2
        ;;
      --cpus)
        cpus="$2"
        shift 2
        ;;
      *)
        die "Unknown argument: $1"
        ;;
    esac
  done

  # Default partition and time limits
  if [[ -z "$partition" ]]; then
    if [[ "$is_dev" -eq 1 ]]; then
      partition="dev"
      time_limit="${time_limit:-01:00:00}"
    elif [[ -n "$gpu" && "$gpu" -gt 0 ]]; then
      partition="gpu"
      time_limit="${time_limit:-04:00:00}"
    else
      partition="normal"
      time_limit="${time_limit:-02:00:00}"
    fi
  else
    time_limit="${time_limit:-02:00:00}"
  fi

  check_connection

  local rdir
  rdir=$(remote_dir "$name")

  printf 'Submitting job "%s" to Sherlock [%s partition]...\n' "$name" "$partition"

  # Create remote job script and directory
  ssh "${SSH_OPTS[@]}" "$SHERLOCK_HOST" bash -s << EOF
set -euo pipefail
mkdir -p "$rdir"

cat << 'SBATCH_EOF' > "$rdir/job.sbatch"
#!/bin/bash
#SBATCH --job-name=$name
#SBATCH --partition=$partition
#SBATCH --time=$time_limit
#SBATCH --mem=$mem
#SBATCH --cpus-per-task=$cpus
$([ -n "$gpu" ] && echo "#SBATCH --gres=gpu:$gpu")
#SBATCH --output=$rdir/output.log
#SBATCH --error=$rdir/output.log
#SBATCH --open-mode=append

set -euo pipefail

printf '=== Job Started: %s on %s ===\n' "$name" "\$(hostname)"
printf 'Date: %s\n' "\$(date)"
printf 'Slurm Job ID: %s\n\n' "\${SLURM_JOB_ID:-n/a}"

# Load modules if available
module purge
module load gcc/12.4.0 python/3.14.2 2>/dev/null || true
$([ -n "$gpu" ] && echo "module load cuda/12.4.0 py-pytorch/2.4.1_py312 2>/dev/null || true")

cd "\$HOME"

$job_cmd

printf '\n=== Job Finished with exit code %s at %s ===\n' "\$?" "\$(date)"
SBATCH_EOF

# If partition is dev, interactive srun is required by Sherlock policy.
# Otherwise, standard batch submission.
if [[ "$partition" == "dev" ]]; then
  echo "LAUNCH_TYPE=DEV"
  # Dev partition uses sbatch or background srun
  # Note: dev partition permits interactive srun
  sbatch "$rdir/job.sbatch" 2>&1 || {
    echo "Batch on dev disallowed by cluster policy, executing via srun..."
    nohup srun -p dev $([ -n "$gpu" ] && echo "-G $gpu") -t "$time_limit" --mem="$mem" -c "$cpus" bash "$rdir/job.sbatch" > "$rdir/output.log" 2>&1 &
    echo "Started dev job in background PID: \$!"
  }
else
  sbatch "$rdir/job.sbatch"
fi
EOF

  printf 'Job "%s" submitted.\n' "$name"
  printf 'Log: %s/output.log\n' "$rdir"
  printf 'To follow log: scripts/sherlock_dispatch.sh tail %s\n' "$name"
}

cmd_list() {
  check_connection
  ssh "${SSH_OPTS[@]}" "$SHERLOCK_HOST" squeue -u "$SHERLOCK_USER" -o "'%.10i %.10P %.24j %.8T %.10M %.10l %.6D %R'"
}

cmd_status() {
  local name="${1:-}"
  [[ -n "$name" ]] || die "usage: status <job-name>"
  check_connection
  ssh "${SSH_OPTS[@]}" "$SHERLOCK_HOST" squeue -u "$SHERLOCK_USER" --name="$name" -o "'%.10i %.10P %.24j %.8T %.10M %.10l %.6D %R'"
}

cmd_log() {
  local name="${1:-}"
  [[ -n "$name" ]] || die "usage: log <job-name>"
  check_connection
  local rdir
  rdir=$(remote_dir "$name")
  ssh "${SSH_OPTS[@]}" "$SHERLOCK_HOST" "
    if [[ -f '$rdir/output.log' ]]; then
      echo '=== Log: $rdir/output.log (last 40 lines) ==='
      tail -n 40 '$rdir/output.log'
    else
      echo 'No log file found at $rdir/output.log yet.'
    fi
  "
}

cmd_tail() {
  local name="${1:-}"
  [[ -n "$name" ]] || die "usage: tail <job-name>"
  check_connection
  local rdir
  rdir=$(remote_dir "$name")
  ssh "${SSH_OPTS[@]}" "$SHERLOCK_HOST" "
    if [[ -f '$rdir/output.log' ]]; then
      tail -n 50 -f '$rdir/output.log'
    else
      echo 'Waiting for $rdir/output.log to appear (checking every 5s, timeout 60s)...'
      for i in {1..12}; do
        if [[ -f '$rdir/output.log' ]]; then break; fi
        sleep 5
      done
      if [[ -f '$rdir/output.log' ]]; then
        tail -n 50 -f '$rdir/output.log'
      else
        echo 'Log file not created yet. The job may still be queued. Check status via: scripts/sherlock_dispatch.sh status $name'
      fi
    fi
  "
}

cmd_kill() {
  local name="${1:-}"
  [[ -n "$name" ]] || die "usage: kill <job-name|job-id>"
  check_connection
  if [[ "$name" =~ ^[0-9]+$ ]]; then
    ssh "${SSH_OPTS[@]}" "$SHERLOCK_HOST" scancel "$name"
    printf 'Cancelled Slurm job ID %s.\n' "$name"
  else
    ssh "${SSH_OPTS[@]}" "$SHERLOCK_HOST" scancel --name="$name"
    printf 'Cancelled Slurm jobs matching name "%s".\n' "$name"
  fi
}

cmd_nodes() {
  check_connection
  ssh "${SSH_OPTS[@]}" "$SHERLOCK_HOST" sh_part
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    run)    cmd_run "$@" ;;
    list)   cmd_list ;;
    status) cmd_status "$@" ;;
    log)    cmd_log "$@" ;;
    tail)   cmd_tail "$@" ;;
    kill)   cmd_kill "$@" ;;
    nodes)  cmd_nodes ;;
    *)
      cat << 'HELP_EOF'
Usage: scripts/sherlock_dispatch.sh <command> [args]

Commands:
  run <job-name> '<command>' [--gpu <N>] [--dev] [--partition <name>] [--time <limit>] [--mem <size>]
  list                        List all active and pending Slurm jobs
  status <job-name>           Show Slurm queue status for a named job
  log <job-name>              Print recent log output
  tail <job-name>             Stream live log output
  kill <job-name|job-id>      Cancel running job
  nodes                       Display partition, node, and GPU status (sh_part)
HELP_EOF
      exit 1
      ;;
  esac
}

main "$@"
