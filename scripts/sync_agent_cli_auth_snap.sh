#!/usr/bin/env bash
# TLDR: Copy existing node-local Cursor, Grok, and Antigravity subscription credentials from one authenticated SNAP node to the other canonical nodes without printing or storing secrets in Git.
set -euo pipefail
umask 077

SOURCE_HOST="${SOURCE_HOST:-mercury1}"
DOMAIN="${SNAP_DOMAIN:-stanford.edu}"
DEFAULT_HOSTS=(skampere1 skampere2 skampere3 mercury1 mercury2)
HOSTS=("$@")
[ ${#HOSTS[@]} -gt 0 ] || HOSTS=("${DEFAULT_HOSTS[@]}")
SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=15)

copy_private_file() {
  local source_path="$1" target_host="$2" target_path="$3"
  local target_dir="${target_path%/*}"
  ssh "${SSH_OPTS[@]}" "$SOURCE_HOST.$DOMAIN" "test -s '$source_path' && cat '$source_path'" |
    ssh "${SSH_OPTS[@]}" "$target_host.$DOMAIN" \
      "umask 077; mkdir -p '$target_dir'; cat > '$target_path'; chmod 600 '$target_path'"
}

source_root="/lfs/$SOURCE_HOST/0/brando9"
for host in "${HOSTS[@]}"; do
  target_root="/lfs/$host/0/brando9"
  printf '[auth-sync] %s\n' "$host"
  if [ "$host" != "$SOURCE_HOST" ]; then
    copy_private_file "$source_root/.config/cursor/auth.json" "$host" "$target_root/.config/cursor/auth.json"
    copy_private_file "$source_root/.grok/auth.json" "$host" "$target_root/.grok/auth.json"
    copy_private_file "$source_root/.gemini/antigravity-cli/antigravity-oauth-token" "$host" "$target_root/.gemini/antigravity-cli/antigravity-oauth-token"
    copy_private_file "$source_root/.gemini/antigravity-cli/cache/onboarding.json" "$host" "$target_root/.gemini/antigravity-cli/cache/onboarding.json"
  fi
  ssh "${SSH_OPTS[@]}" "$host.$DOMAIN" "bash -lc '
    agent status 2>&1 | head -1
    timeout 20 agy models 2>&1 | head -2 | tail -1
    stat -c \"mode=%a %n\" $target_root/.config/cursor/auth.json
    stat -c \"mode=%a %n\" $target_root/.grok/auth.json
    stat -c \"mode=%a %n\" $target_root/.gemini/antigravity-cli/antigravity-oauth-token
  '"
done
