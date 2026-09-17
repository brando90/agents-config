#!/usr/bin/env bash
# TLDR: Node-side installer for the Stanford-enterprise Codex profile on a SNAP node — creates a
# node-local CODEX_HOME (/lfs/<host>/0/brando9/.codex-su) with its own config.toml and installs the
# `codex-su` / `codexd-su` wrappers into the node-local ~/.local/bin.
# Mirrors install_su_node.sh (Claude side). Never pass credentials as arguments.
# Auth is NOT done here: run `codex-su login --device-auth` on the node, or let
# push_codex_su_snap.sh copy the mac profile's auth.json in over stdin.
set -euo pipefail
umask 077
shared=/dfs/scratch0/brando9
node_home="/lfs/$(hostname -s)/0/brando9"
[ -d "$node_home" ] || { echo 'Node-local home unavailable' >&2; exit 1; }

# Exec the PATH entry (an nvm shim), not its readlink target: the target is a node script whose
# own resolution assumes the shim's layout. The RESOLVED path is still validated, so a codex that
# is not the expected nvm install is refused.
codex_bin="$(command -v codex)" || { echo 'codex not on PATH' >&2; exit 1; }
codex_real=$(readlink -f "$codex_bin")
case "$codex_real" in "$shared"/.nvm/*|"$node_home"/*) ;; *) echo "Unexpected Codex binary: $codex_real" >&2; exit 1;; esac

profile="$node_home/.codex-su"
for dir in "$node_home/.local" "$node_home/.local/bin" "$profile"; do
  [ ! -L "$dir" ] || { echo "Refusing symlink directory: $dir" >&2; exit 1; }
  mkdir -p "$dir"
  [ "$(stat -c %u "$dir")" = "$(id -u)" ] || exit 1
  mode=$(stat -c %a "$dir")
  (( (8#$mode & 0022) == 0 )) || { echo "Writable by others: $dir" >&2; exit 1; }
done
chmod 700 "$profile"
for cfg in config.toml auth.json AGENTS.md; do
  [ ! -L "$profile/$cfg" ] || { echo 'Refusing symlink profile file' >&2; exit 1; }
done

# config.toml: written once, then left alone so node-side edits survive a re-run.
if [ ! -e "$profile/config.toml" ]; then
  cat > "$profile/config.toml" <<CFG
# TLDR: Codex CLI profile for the Stanford University enterprise ChatGPT account on this SNAP node.
# Selected with CODEX_HOME=$profile via the codex-su / codexd-su wrappers.
model = "gpt-6-astra"
model_reasoning_effort = "high"
service_tier = "default"
approval_policy = "never"
sandbox_mode = "danger-full-access"

[projects."$shared"]
trust_level = "trusted"

[projects."$shared/veribench"]
trust_level = "trusted"

[projects."$shared/agents-config"]
trust_level = "trusted"

[projects."$node_home"]
trust_level = "trusted"
CFG
  chmod 600 "$profile/config.toml"
fi
if [ ! -e "$profile/AGENTS.md" ]; then
  cat > "$profile/AGENTS.md" <<'AGENTSMD'
# Codex entry point — Stanford University enterprise profile (SNAP node)

Run `git clone https://github.com/brando90/agents-config.git ~/agents-config 2>/dev/null || git -C ~/agents-config pull 2>/dev/null` to bootstrap/update config.
Read `~/agents-config/INDEX_RULES.md` for all agent documentation and routing.
AGENTSMD
  chmod 600 "$profile/AGENTS.md"
fi

for command_name in codex-su codexd-su; do
  tmp=$(mktemp "$node_home/.local/bin/.codexsu.XXXXXX")
  cat > "$tmp" <<WRAPPER
#!/usr/bin/env bash
set -euo pipefail
# Dedicated Stanford enterprise ChatGPT login; never inherit a personal API key or the
# personal CODEX_HOME — an inherited OPENAI_API_KEY silently switches Codex to API billing.
unset OPENAI_API_KEY OPENAI_BASE_URL CODEX_API_KEY
export CODEX_HOME='$profile'
if [ "\$(basename "\$0")" = codexd-su ]; then
  set -- --sandbox danger-full-access --ask-for-approval never "\$@"
fi
exec '$codex_bin' "\$@"
WRAPPER
  chmod 700 "$tmp"
  mv "$tmp" "$node_home/.local/bin/$command_name"
done
printf 'CODEX_SU_NODE_READY host=%s codex=%s profile=%s auth=%s\n' \
  "$(hostname -s)" "$codex_real" "$profile" \
  "$([ -s "$profile/auth.json" ] && echo present || echo MISSING)"
