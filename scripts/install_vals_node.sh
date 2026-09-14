#!/usr/bin/env bash
# Install a node-local Vals Claude runtime using a separately authorized setup-token grant.
# Run on a SNAP node after health checks. Never pass credentials as arguments.
set -euo pipefail
umask 077
shared=/dfs/scratch0/brando9
node_home="/lfs/$(hostname -s)/0/brando9"
grant="$shared/.claude-vals-remote/oauth-token"
[ -d "$node_home" ] || { echo 'Node-local home unavailable' >&2; exit 1; }
[ ! -L "$grant" ] && [ -s "$grant" ] || { echo 'Vals remote grant missing' >&2; exit 1; }
[ "$(stat -c %u "$grant")" = "$(id -u)" ] && [ "$(stat -c %a "$grant")" = 600 ] || {
  echo 'Vals grant must be owned by this user with mode 600' >&2; exit 1;
}
source_bin=$(readlink -f "$(command -v claude)")
case "$source_bin" in "$shared"/.nvm/*/claude.exe) ;; *) echo 'Unexpected Claude source binary' >&2; exit 1;; esac
file "$source_bin" | grep -q 'ELF 64-bit' || exit 1
sha=$(sha256sum "$source_bin" | cut -d' ' -f1)
runtime="$node_home/.local/share/claude-vals-runtime/$sha"
for dir in "$node_home/.local" "$node_home/.local/share" "$node_home/.local/bin" "$node_home/.local/share/claude-vals-runtime" "$runtime" "$node_home/.claude-vals-node"; do
  [ ! -L "$dir" ] || { echo "Refusing symlink directory: $dir" >&2; exit 1; }
  mkdir -p "$dir"
  [ "$(stat -c %u "$dir")" = "$(id -u)" ] || exit 1
  mode=$(stat -c %a "$dir")
  (( (8#$mode & 0022) == 0 )) || { echo "Writable by others: $dir" >&2; exit 1; }
done
chmod 700 "$node_home/.claude-vals-node" "$node_home/.local/share/claude-vals-runtime" "$runtime"
for cfg in settings.json .claude.json .credentials.json; do
  [ ! -L "$node_home/.claude-vals-node/$cfg" ] || { echo 'Refusing symlink profile file' >&2; exit 1; }
done
[ ! -L "$runtime/claude" ] || { echo 'Refusing symlink executable' >&2; exit 1; }
# Never overwrite a mapped executable. Each content revision has its own directory.
if [ ! -f "$runtime/claude" ]; then
  tmp=$(mktemp "$runtime/.claude.XXXXXX")
  cp "$source_bin" "$tmp"
  chmod 700 "$tmp"
  [ "$(sha256sum "$tmp" | cut -d' ' -f1)" = "$sha" ] || { rm -f "$tmp"; exit 1; }
  mv "$tmp" "$runtime/claude"
fi
[ "$(sha256sum "$runtime/claude" | cut -d' ' -f1)" = "$sha" ] || exit 1
"$runtime/claude" --version
profile="$node_home/.claude-vals-node"
if [ ! -e "$profile/settings.json" ]; then
  printf '%s\n' '{"model":"opus","modelSettings":{"claude-opus-5":{"effortLevel":"xhigh"}},"skipDangerousModePermissionPrompt":true}' > "$profile/settings.json"
fi
if [ ! -e "$profile/.claude.json" ]; then
  printf '%s\n' '{"hasCompletedOnboarding":true,"theme":"dark"}' > "$profile/.claude.json"
fi
for command_name in claude-vals clauded-vals; do
  tmp=$(mktemp "$node_home/.local/bin/.vals.XXXXXX")
  cat > "$tmp" <<WRAPPER
#!/usr/bin/env bash
set -euo pipefail
# Dedicated Vals subscription grant; never inherit personal or API billing credentials.
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN CLAUDE_CODE_OAUTH_TOKEN \\
 CLAUDE_CODE_OAUTH_REFRESH_TOKEN ANTHROPIC_BASE_URL CLAUDE_CODE_USE_BEDROCK \\
 CLAUDE_CODE_USE_VERTEX CLAUDE_CODE_USE_FOUNDRY CLAUDE_CONFIG_DIR \\
 CLAUDE_CODE_EFFORT_LEVEL CLAUDE_EFFORT
export CLAUDE_CONFIG_DIR='$profile'
export DISABLE_AUTOUPDATER=1
if [ -L '$grant' ] || [ ! -s '$grant' ] || [ "\$(stat -c %u '$grant')" != "\$(id -u)" ] || [ "\$(stat -c %a '$grant')" != 600 ]; then
 echo 'Protected Vals remote grant unavailable' >&2; exit 1
fi
CLAUDE_CODE_OAUTH_TOKEN="\$(cat '$grant')" || { echo 'Cannot read Vals grant' >&2; exit 1; }
[[ "\$CLAUDE_CODE_OAUTH_TOKEN" =~ ^sk-ant-oat01-[A-Za-z0-9_-]{32,}$ ]] || { echo 'Invalid Vals grant format' >&2; exit 1; }
export CLAUDE_CODE_OAUTH_TOKEN
if [ "\$(basename "\$0")" = clauded-vals ]; then
  set -- --dangerously-skip-permissions "\$@"
fi
exec '$runtime/claude' "\$@"
WRAPPER
  chmod 700 "$tmp"
  mv "$tmp" "$node_home/.local/bin/$command_name"
done
printf 'VALS_NODE_READY host=%s runtime=%s profile=%s\n' "$(hostname -s)" "$runtime/claude" "$profile"
