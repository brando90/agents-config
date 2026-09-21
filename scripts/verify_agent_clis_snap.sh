#!/usr/bin/env bash
# TLDR: Make one bounded real model call through Cursor Agent, Grok Build, and Antigravity on every canonical SNAP node and fail unless all 15 calls return their node-specific token.
set -euo pipefail
DEFAULT_HOSTS=(skampere1 skampere2 skampere3 mercury1 mercury2)
HOSTS=("$@")
[ ${#HOSTS[@]} -gt 0 ] || HOSTS=("${DEFAULT_HOSTS[@]}")
failed=0
for host in "${HOSTS[@]}"; do
  printf '[smoke] %s\n' "$host"
  for client in cursor grok agy; do
    case "$client" in
      cursor) upper=CURSOR ;;
      grok) upper=GROK ;;
      agy) upper=AGY ;;
    esac
    token="$upper-$host-OK"
    case "$client" in
      cursor) cmd=(agent -p --trust --mode ask --output-format text "Reply with exactly: $token") ;;
      grok) cmd=(grok -p "Reply with exactly: $token" --max-turns 1 --disable-web-search) ;;
      agy) cmd=(agy -p "Reply with exactly: $token" --model gemini-3.8-flash-low --print-timeout 270s) ;;
    esac
    printf -v remote_cmd '%q ' "${cmd[@]}"
    output="$(ssh -o BatchMode=yes -o ConnectTimeout=15 "$host.stanford.edu" \
      "bash -lc 'timeout 300 $remote_cmd'" 2>&1)" || { printf 'FAIL %s/%s rc\n' "$host" "$client"; failed=1; continue; }
    if grep -Fq "$token" <<<"$output"; then
      printf 'PASS %s/%s %s\n' "$host" "$client" "$token"
    else
      printf 'FAIL %s/%s missing-token\n' "$host" "$client"
      failed=1
    fi
  done
done
exit "$failed"
