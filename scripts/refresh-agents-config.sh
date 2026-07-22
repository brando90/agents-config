#!/usr/bin/env bash
# Refresh ~/agents-config via a throttled git pull.
# Wired as a Claude Code UserPromptSubmit hook (see claude-code-settings.json):
# stdout is injected into the model's context, so when a pull brings new
# commits the session is told to re-read INDEX_RULES.md (Hard Rule 5, made
# deterministic). Throttled to one attempt per 15 minutes per machine via a
# marker file; safe offline (pull failure is silent and still stamps the
# marker so we don't retry on every prompt).
set -uo pipefail

AC_DIR="${HOME}/agents-config"
MARKER="${HOME}/.claude/.ac_last_pull"
THROTTLE_SECS=900

[ -d "${AC_DIR}/.git" ] || exit 0

now=$(date +%s)
last=$(cat "$MARKER" 2>/dev/null || echo 0)
case "$last" in (*[!0-9]*|'') last=0;; esac
[ $((now - last)) -lt "$THROTTLE_SECS" ] && exit 0
echo "$now" > "$MARKER"

before=$(git -C "$AC_DIR" rev-parse HEAD 2>/dev/null) || exit 0
git -C "$AC_DIR" pull --quiet --ff-only >/dev/null 2>&1 || exit 0
after=$(git -C "$AC_DIR" rev-parse HEAD 2>/dev/null) || exit 0

if [ "$before" != "$after" ]; then
  echo "agents-config updated ($(git -C "$AC_DIR" log --oneline "${before}..${after}" | head -3 | tr '\n' '; ')) — re-read ~/agents-config/INDEX_RULES.md before continuing."
fi
