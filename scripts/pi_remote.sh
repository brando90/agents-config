#!/usr/bin/env bash
# Shared Pi entry point. No credentials are loaded and no model is downloaded.
set -e
pi_cli="$HOME/.local/lib/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js"
if [ ! -r "$pi_cli" ]; then
  printf '%s\n' 'Pi coding agent is missing. Run the documented user-level Pi installer; do not apt-install pi.' >&2
  exit 127
fi
if ! command -v node >/dev/null 2>&1 || ! node -e 'process.exit(((v)=>v[0]>22||(v[0]===22&&v[1]>=19))(process.versions.node.split(".").map(Number)) ? 0 : 1)' 2>/dev/null; then
  if [ -s /dfs/scratch0/brando9/.nvm/nvm.sh ]; then
    export NVM_DIR=/dfs/scratch0/brando9/.nvm
  else
    export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
  fi
  [ ! -s "$NVM_DIR/nvm.sh" ] || . "$NVM_DIR/nvm.sh" --no-use
  if command -v nvm >/dev/null 2>&1; then nvm use default --silent; fi
fi
node -e 'process.exit(((v)=>v[0]>22||(v[0]===22&&v[1]>=19))(process.versions.node.split(".").map(Number)) ? 0 : 1)' || {
  printf '%s\n' 'Pi requires Node >=22.19.0; install a supported Node version with the existing version manager.' >&2
  exit 1
}

# Version/help/catalog checks do not need inference connectivity.
pi_metadata_only=false
for pi_arg in "$@"; do
  case "$pi_arg" in --version|-v|--help|-h|--list-models) pi_metadata_only=true ;; esac
done
if [ "$pi_metadata_only" = false ]; then
  python3 - "$@" <<'PY'
import fcntl
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import urllib.request

home = Path.home()
profile = Path(os.environ.get('PI_CODING_AGENT_DIR', str(home / '.pi/agent')))
settings_path = profile / 'settings.json'
models_path = profile / 'models.json'
if not settings_path.exists() or not models_path.exists():
    sys.exit(0)
settings = json.loads(settings_path.read_text())
project_settings = Path.cwd() / '.pi/settings.json'
if project_settings.exists():
    settings.update(json.loads(project_settings.read_text()))
provider = settings.get('defaultProvider')
args = sys.argv[1:]
for i, arg in enumerate(args):
    if arg == '--provider' and i + 1 < len(args):
        provider = args[i + 1]
    elif arg.startswith('--provider='):
        provider = arg.split('=', 1)[1]
if provider != 'snap-coder':
    sys.exit(0)
spec = json.loads(models_path.read_text()).get('providers', {}).get(provider, {})
local_port = 18201 if socket.gethostname().split('.')[0] == 'skampere1' else 18127
base_url = 'http://127.0.0.1:' + str(local_port)
if spec.get('baseUrl', '').rstrip('/') != base_url + '/v1':
    sys.exit(0)  # Preserve customized routes; never rewrite model settings.

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
def healthy():
    try:
        with opener.open(base_url + '/v1/models', timeout=3) as response:
            return response.status == 200 and any(m.get('id') == 'qwen3-coder-30b' for m in json.load(response).get('data', []))
    except Exception:
        return False

if healthy():
    sys.exit(0)
if socket.gethostname().split('.')[0] == 'skampere1':
    sys.exit('Pi model server on skampere1:18201 is unavailable; inspect its existing service. No new GPU job was started.')
cache = home / '.cache/pi-snap' / socket.gethostname().split('.')[0]
cache.mkdir(parents=True, exist_ok=True, mode=0o700)
with (cache / 'tunnel.lock').open('a') as lock:
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit('Another Pi tunnel setup is active on this host; no duplicate connection was attempted.')
    if healthy():
        sys.exit(0)
    # One bounded authenticated attempt. Keep host-key verification enabled.
    command = ['ssh', '-fNT', '-S', str(cache / 'model.sock'),
               '-o', 'ControlMaster=auto', '-o', 'ControlPersist=600',
               '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
               '-o', 'ConnectTimeout=10', '-o', 'ConnectionAttempts=1',
               '-o', 'ExitOnForwardFailure=yes', '-o', 'ServerAliveInterval=60',
               '-o', 'ServerAliveCountMax=3',
               '-L', '127.0.0.1:18127:127.0.0.1:18201',
               'brando9@skampere1.stanford.edu']
    # A detached SSH master must not retain the caller's output pipes.
    with tempfile.TemporaryFile() as diagnostic:
        try:
            result = subprocess.run(command, timeout=20, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.DEVNULL, stderr=diagnostic)
        except subprocess.TimeoutExpired:
            sys.exit('Pi SSH model tunnel timed out; no retry. Complete host authentication separately.')
        if result.returncode:
            diagnostic.seek(0)
            sys.stderr.write(diagnostic.read().decode(errors='replace'))
    if result.returncode or not healthy():
        sys.exit('Pi SSH model tunnel is unavailable; no retry. Check host authentication and the existing skampere1 model service.')
PY
fi
if [ "${1:-}" = --check-local ]; then
  printf '%s\n' 'Pi command and configured local-route preflight completed (no inference).'
  exit 0
fi
exec node "$pi_cli" "$@"
