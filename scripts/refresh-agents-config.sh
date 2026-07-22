#!/usr/bin/env bash
# Refresh ~/agents-config via a throttled git pull.
# Wired as a Claude Code UserPromptSubmit hook (see claude-code-settings.json):
# stdout is injected into the model's context, so when a pull brings new
# commits the session is told to re-read INDEX_RULES.md (Hard Rule 5, made
# deterministic). Throttled to one attempt per 15 minutes per machine via a
# marker file; safe offline (pull failure is silent and still stamps the
# marker so we don't retry on every prompt). If the repo has local commits
# that block the fast-forward pull, a bounded warning is emitted instead of
# wedging silently.
set -uo pipefail

AC_DIR="${HOME}/agents-config"
MARKER="${HOME}/.claude/.ac_last_pull"
THROTTLE_SECS=900

[ -d "${AC_DIR}/.git" ] || exit 0

now=$(date +%s)
last=$(cat "$MARKER" 2>/dev/null || echo 0)
# Sanitize: non-numeric or empty -> 0; force base-10 (leading zeros would be
# parsed as octal and abort bash 3.2); future-dated (e.g. ms epoch) -> 0.
case "$last" in (*[!0-9]*|'') last=0;; esac
last=$((10#$last))
[ "$last" -gt "$now" ] && last=0
[ $((now - last)) -lt "$THROTTLE_SECS" ] && exit 0
mkdir -p "$(dirname "$MARKER")" 2>/dev/null || true
echo "$now" > "$MARKER" 2>/dev/null || true

before=$(git -C "$AC_DIR" rev-parse HEAD 2>/dev/null) || exit 0
if ! GIT_TERMINAL_PROMPT=0 git -C "$AC_DIR" -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=5 pull --quiet --ff-only >/dev/null 2>&1; then
  ahead=$(git -C "$AC_DIR" rev-list --count '@{u}..HEAD' 2>/dev/null) || ahead=0
  case "$ahead" in (*[!0-9]*|'') ahead=0;; esac
  if [ "$ahead" -gt 0 ]; then
    echo "WARNING: ~/agents-config has ${ahead} local commit(s) not on origin — auto-refresh is wedged until they are pushed or rebased (Trigger Rule 6)."
  fi
  exit 0
fi
after=$(git -C "$AC_DIR" rev-parse HEAD 2>/dev/null) || exit 0

if [ "$before" != "$after" ]; then
  echo "agents-config updated ($(git -C "$AC_DIR" log --oneline "${before}..${after}" | head -3 | tr '\n' ';' | cut -c1-300)) — re-read ~/agents-config/INDEX_RULES.md before continuing."
fi
