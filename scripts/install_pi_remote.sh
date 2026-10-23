#!/usr/bin/env bash
# User-level Pi 1.4.0 installer; does not copy credentials or start GPU workloads.
set -e
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v node >/dev/null 2>&1 || ! node -e 'process.exit(((v)=>v[0]>22||(v[0]===22&&v[1]>=19))(process.versions.node.split(".").map(Number)) ? 0 : 1)' 2>/dev/null; then
  export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
  [ ! -s "$NVM_DIR/nvm.sh" ] || . "$NVM_DIR/nvm.sh"
fi
node -e 'process.exit(((v)=>v[0]>22||(v[0]===22&&v[1]>=19))(process.versions.node.split(".").map(Number)) ? 0 : 1)' || {
  printf '%s\n' 'Load Node >=22.19.0 using this host’s supported version manager, then rerun.' >&2; exit 1;
}
pi_package="$HOME/.local/lib/node_modules/@earendil-works/pi-coding-agent/package.json"
pi_installed=$(node -e 'try { console.log(require(process.argv[1]).version) } catch {}' "$pi_package")
if [ "$pi_installed" != 1.4.0 ]; then
  npm install --global --prefix "$HOME/.local" --ignore-scripts @earendil-works/pi-coding-agent@1.4.0
fi
mkdir -p "$HOME/.local/share/pi-remote" "$HOME/.local/bin"
install -m 755 "$script_dir/pi_remote.sh" "$HOME/.local/share/pi-remote/pi"
if { [ -e "$HOME/.local/bin/pi" ] || [ -L "$HOME/.local/bin/pi" ]; } && [ "$(readlink "$HOME/.local/bin/pi" 2>/dev/null || true)" != "$HOME/.local/share/pi-remote/pi" ]; then
  cp -P "$HOME/.local/bin/pi" "$HOME/.local/share/pi-remote/pi.before-$(date +%m-%d-%Y-%H%M%S)"
fi
ln -sfn "$HOME/.local/share/pi-remote/pi" "$HOME/.local/bin/pi"
python3 - <<'PY'
import datetime
from pathlib import Path
home = Path.home()
block = '\n# Pi user-level command path\ncase ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) export PATH="$HOME/.local/bin:$PATH" ;; esac\n'
# Preserve Bash's existing login-file precedence; do not create .bash_profile
# over an existing .profile or .bash_login.
login = next((n for n in ['.bash_profile', '.bash_login', '.profile'] if (home / n).exists()), '.profile')
for name in ['.bashrc', login]:
    path = home / name
    original = path.read_text() if path.exists() else ''
    if '# Pi user-level command path' not in original:
        if path.exists():
            backup = home / '.local/share/pi-remote' / (name + '.before-' + datetime.datetime.now().strftime('%m-%d-%Y-%H%M%S'))
            backup.write_text(original)
            backup.chmod(0o600)
        path.write_text(original + block)
PY
"$HOME/.local/bin/pi" --version
printf '%s\n' 'Pi installed. Existing shells: export PATH="$HOME/.local/bin:$PATH"; hash -r'
