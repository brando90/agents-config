#!/usr/bin/env bash
# Thin wrapper around the shared helper. Defaults to this video and this folder.
# See scripts/fetch_youtube_transcript.sh for the implementation.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$DIR/../.." && pwd)"
URL="${1:-https://youtu.be/u-2F63eD9tE}"
exec bash "$REPO_ROOT/scripts/fetch_youtube_transcript.sh" "$URL" "$DIR"
