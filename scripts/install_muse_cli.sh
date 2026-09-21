#!/usr/bin/env bash
# Install Meta Muse Code per host; checks never call a model or enable billing.
set -euo pipefail
mode="${1:---install}"
case "$mode" in --install|--check) ;; *) echo 'Usage: install_muse_cli.sh [--install|--check]' >&2; exit 2;; esac
muse_bin="${MUSE_INSTALL_DIR:-$HOME/.local/bin}/muse"
if [ "$mode" = --install ]; then
  muse_installer=$(mktemp "${TMPDIR:-/tmp}/muse-install.XXXXXX")
  trap 'rm -f "$muse_installer"' EXIT
  curl --fail --silent --show-error --location --max-time 60 \
    --proto '=https' --proto-redir '=https' https://dev.meta.ai/install.sh -o "$muse_installer"
  bash -n "$muse_installer"
  MUSE_LOGIN=0 MUSE_NO_MODIFY_PATH=1 bash "$muse_installer"
fi
python3 - "$muse_bin" <<'PY'
import os, pathlib, subprocess, sys, tempfile
binary = str(pathlib.Path(sys.argv[1]).resolve(strict=True))
subprocess.run([binary, '--version'], check=True, timeout=60)
with tempfile.TemporaryDirectory(prefix='.muse-offline-', dir=pathlib.Path.home()) as directory, \
        tempfile.TemporaryDirectory(prefix='muse-runtime-', dir='/var/tmp') as runtime:
    result = subprocess.run([
        binary, 'exec', '--provider', 'echo', '--max-model-steps', '1',
        '--disable-shell', '--disable-write', '--disable-web-tools',
        '--approval-judge', 'off', '--no-foreign-personal-context',
        '--no-session-log', '--workspace', directory, 'MUSE_OFFLINE_CHECK',
    ], cwd=directory, env={**os.environ, 'TMPDIR': runtime}, text=True,
        capture_output=True, timeout=60, check=True)
    if 'echo: MUSE_OFFLINE_CHECK' not in result.stdout:
        raise SystemExit('Offline echo output did not match')
    print('PASS: offline echo; no model inference or billing verification')
PY
