#!/bin/sh
# Make the endpoint's bearer token outside the repo (mode 600). Never print or commit it.
set -eu
f="${1:-$HOME/.config/pi-claude-endpoint/token}"
mkdir -p "$(dirname "$f")"; chmod 700 "$(dirname "$f")"
[ -e "$f" ] && { echo "exists: $f"; exit 0; }
umask 177; python3 -c 'import secrets;print(secrets.token_urlsafe(48))' > "$f"
echo "wrote $f"
