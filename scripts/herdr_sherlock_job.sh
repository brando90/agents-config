#!/usr/bin/env bash
# Run Herdr in one explicitly requested allocation; never resubmit this job.
# Submit from a Sherlock login: sbatch this-file
#SBATCH --job-name=herdr-interactive
#SBATCH --partition=service
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=08:00:00
#SBATCH --no-requeue
#SBATCH --output=.local/state/herdr-stanford/job-%j.log
set -euo pipefail
umask 077
test -n "${SLURM_JOB_ID:-}" || { echo 'A Slurm allocation is required.' >&2; exit 2; }
case "$(hostname -s)" in *-ln*) echo 'Refusing a login-node server.' >&2; exit 2;; esac
state="$HOME/.local/state/herdr-stanford"
mkdir -p "$state"
# Shared home makes this lock exclusive even if two allocations use different nodes.
exec 9>"$state/allocation.lock"
flock -n 9 || { echo 'Another Herdr allocation is already running.' >&2; exit 3; }
test -x "$HOME/.local/bin/herdr"
python3 - "$state/runtime.json" <<'PY'
import json, os, pathlib, socket, tempfile, time
path = pathlib.Path(__import__('sys').argv[1])
data = {'job_id': os.environ['SLURM_JOB_ID'], 'host': socket.gethostname(),
        'user': os.environ['USER'], 'started_at': int(time.time()),
        'session': 'default', 'automatic_restart': False}
fd, temporary = tempfile.mkstemp(prefix='.runtime-', dir=path.parent)
with os.fdopen(fd, 'w') as stream:
    json.dump(data, stream); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
os.replace(temporary, path)
PY
cd "$HOME"
exec "$HOME/.local/bin/herdr" server
