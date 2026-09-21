#!/usr/bin/env bash
# TLDR: Install isolated Vals ChatGPT Codex wrappers and profile on one SNAP node.
set -euo pipefail
umask 077
shared=/dfs/scratch0/brando9
node_home="/lfs/$(hostname -s)/0/brando9"
profile="$node_home/.codex-vals"
codex_bin="$(command -v codex)"
codex_real="$(readlink -f "$codex_bin")"
case "$codex_real" in "$shared"/.nvm/*|"$node_home"/*) ;; *) echo "Unexpected Codex binary: $codex_real" >&2; exit 1;; esac
for dir in "$node_home/.local" "$node_home/.local/bin" "$profile"; do
  [ ! -L "$dir" ] || { echo "Refusing symlink: $dir" >&2; exit 1; }
  mkdir -p "$dir"
  [ "$(stat -c %u "$dir")" = "$(id -u)" ] || exit 1
done
chmod 700 "$profile"
if [ ! -e "$profile/config.toml" ]; then
  cat > "$profile/config.toml" <<CFG
model = "gpt-6-astra"
model_reasoning_effort = "high"
service_tier = "default"
approval_policy = "never"
sandbox_mode = "danger-full-access"
[projects."$shared"]
trust_level = "trusted"
[projects."$node_home"]
trust_level = "trusted"
CFG
  chmod 600 "$profile/config.toml"
fi
for command_name in codex-vals codexd-vals; do
  tmp=$(mktemp "$node_home/.local/bin/.codexvals.XXXXXX")
  cat > "$tmp" <<WRAPPER
#!/usr/bin/env bash
set -euo pipefail
unset OPENAI_API_KEY OPENAI_BASE_URL CODEX_API_KEY
export CODEX_HOME='$profile'
if [ "\$(basename "\$0")" = codexd-vals ]; then
  set -- --sandbox danger-full-access --ask-for-approval never "\$@"
fi
exec '$codex_bin' "\$@"
WRAPPER
  chmod 700 "$tmp"
  mv "$tmp" "$node_home/.local/bin/$command_name"
done
printf 'CODEX_VALS_NODE_READY host=%s profile=%s auth=%s\n' "$(hostname -s)" "$profile" "$([ -s "$profile/auth.json" ] && echo present || echo MISSING)"
