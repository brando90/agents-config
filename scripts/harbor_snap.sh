#!/usr/bin/env bash
# TLDR: Run a node-local SNAP Harbor installation without letting the shared Mistral PYTHONPATH contaminate its isolated environment.

set -u
HARBOR_BIN="$HOME/.local/bin/harbor"
if [ ! -x "$HARBOR_BIN" ]; then
  echo "harbor: missing per-node executable $HARBOR_BIN; run: uv tool install harbor" >&2
  exit 127
fi
exec env -u PYTHONPATH "$HARBOR_BIN" "$@"
