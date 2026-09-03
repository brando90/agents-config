#!/usr/bin/env bash
# TLDR: Audit SNAP nodes for agent-tool, storage, authentication, symlink, and repository hazards, with conservative opt-in repairs.

set -u

DFS_ROOT="${SNAP_DFS_ROOT:-/dfs/scratch0/brando9}"
NVM_DIR="$DFS_ROOT/.nvm"
DFS_BIN="$DFS_ROOT/bin"
OPEN_NODES="skampere1 skampere2 skampere3 mercury1 mercury2"
GATED_NODES="hyperturing1 hyperturing2 ampere1 ampere2 ampere3 ampere4 ampere5 ampere6 ampere7 ampere8 ampere9 turing1 turing2 turing3 blackwell1"
ALL_NODES="$OPEN_NODES $GATED_NODES"
DISK_WARN_FREE_PCT="${SNAP_HEALTH_DISK_WARN_FREE_PCT:-10}"
DISK_FAIL_FREE_PCT="${SNAP_HEALTH_DISK_FAIL_FREE_PCT:-5}"
CONNECT_TIMEOUT="${SNAP_HEALTH_CONNECT_TIMEOUT:-7}"
DO_FIX=0
DO_JSON=0
DO_SMOKE=0
ONLY_NODE=""
WORKER=0
FAILURES=0

usage() {
  cat <<'EOF'
Usage: snap_health.sh [--fix] [--node HOST] [--json] [--smoke]

With no arguments, audit every normally reachable SNAP node and probe every
Slurm-gated node. --fix applies only conservative user-owned repairs. --smoke
spends Codex and Claude subscription tokens and is therefore opt-in.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --fix) DO_FIX=1 ;;
    --json) DO_JSON=1 ;;
    --smoke) DO_SMOKE=1 ;;
    --node)
      [ "$#" -ge 2 ] || { echo "--node requires a host" >&2; exit 2; }
      ONLY_NODE="${2%%.*}"
      shift
      ;;
    --_worker) WORKER=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if [ -n "$ONLY_NODE" ]; then
  case " $ALL_NODES " in
    *" $ONLY_NODE "*) ;;
    *) echo "Unknown SNAP node: $ONLY_NODE" >&2; exit 2 ;;
  esac
fi

clean_field() {
  printf '%s' "$1" | tr '\t\r\n' '   ' | sed 's/[[:space:]][[:space:]]*/ /g; s/^ //; s/ $//'
}

emit() {
  # Internal tab-separated protocol: severity, host, check, detail, repair.
  _sev="$1" _host="$2" _check="$3" _detail="$4" _repair="${5:--}"
  printf '%s\t%s\t%s\t%s\t%s\n' \
    "$_sev" "$_host" "$_check" "$(clean_field "$_detail")" "$(clean_field "$_repair")"
}

canonical_nvm_bin() {
  # nvm.sh selects its default dynamically; never embed a Node version in PATH.
  export NVM_DIR
  if [ -s "$NVM_DIR/nvm.sh" ]; then
    # shellcheck disable=SC1090
    . "$NVM_DIR/nvm.sh" >/dev/null 2>&1 || true
    nvm use default --silent >/dev/null 2>&1 || true
  fi
  if [ -n "${NVM_BIN:-}" ] && [ -x "$NVM_BIN/node" ]; then
    case "$NVM_BIN" in
      "$NVM_DIR"/versions/node/*/bin) printf '%s\n' "$NVM_BIN"; return ;;
    esac
  fi
  _node_path="$(command -v node 2>/dev/null || true)"
  case "$_node_path" in
    "$NVM_DIR"/versions/node/*/bin/node) dirname "$_node_path" ;;
    *)
      find "$NVM_DIR/versions/node" -mindepth 3 -maxdepth 3 -type f -name node -perm -u+x \
        -printf '%T@ %h\n' 2>/dev/null | sort -nr | awk 'NR == 1 { print $2 }'
      ;;
  esac
}

version_of() {
  _tool="$1" _path="$2"
  case "$_tool" in
    valkyrie)
      _meta="$(find "$DFS_ROOT/uv/tools" "$DFS_ROOT/uv/tools-glibc2.31" \
        -path '*/valkyrie-*.dist-info/METADATA' -type f -print 2>/dev/null | head -1)"
      if [ -n "$_meta" ]; then
        sed -n 's/^Version: /valkyrie /p' "$_meta" | head -1
      else
        printf 'version unavailable'
      fi
      ;;
    harbor)
      _version_output="$(timeout 20 "$_path" --version 2>&1)"
      _version_rc=$?
      printf '%s\n' "$_version_output" | tail -1
      return "$_version_rc"
      ;;
    *)
      _version_output="$(timeout 12 "$_path" --version 2>&1)"
      _version_rc=$?
      printf '%s\n' "$_version_output" | head -1
      return "$_version_rc"
      ;;
  esac
}

numeric_version() {
  printf '%s\n' "$1" | grep -oE '[0-9]+(\.[0-9]+)+' | head -1
}

version_is_older() {
  _left="$1" _right="$2"
  [ -n "$_left" ] && [ -n "$_right" ] || return 1
  [ "$_left" = "$_right" ] && return 1
  [ "$(printf '%s\n%s\n' "$_left" "$_right" | sort -V | head -1)" = "$_left" ]
}

expected_path() {
  _tool="$1" _nvm_bin="$2"
  case "$_tool" in
    claude|codex|node) printf '%s/%s' "$_nvm_bin" "$_tool" ;;
    clauded|claude-vals|clauded-vals|valkyrie) printf '%s/%s' "$DFS_BIN" "$_tool" ;;
    uv) printf '%s/.local/bin/%s' "$HOME" "$_tool" ;;
    harbor) printf '%s/%s' "$DFS_BIN" "$_tool" ;;
    elan|lake) printf '%s/.elan/bin/%s' "$HOME" "$_tool" ;;
    docker) printf '/usr/bin/docker|user shim' ;;
    python3) printf '/usr/bin/python3' ;;
    *) printf 'unknown' ;;
  esac
}

path_is_canonical() {
  _tool="$1" _actual="$2" _expected="$3"
  case "$_tool" in
    docker) [ "$_actual" = /usr/bin/docker ] || [ "$_actual" = /bin/docker ] || [ "$_actual" = "$HOME/.local/bin/docker" ] ;;
    *) [ "$_actual" = "$_expected" ] ;;
  esac
}

safe_fix_local_duplicate() {
  _host="$1" _tool="$2" _canonical="$3"
  _duplicate="$HOME/.local/bin/$_tool"
  [ -e "$_duplicate" ] || [ -L "$_duplicate" ] || return 0
  [ "$_duplicate" != "$_canonical" ] || return 0
  [ -O "$_duplicate" ] || { emit WARN "$_host" "fix.$_tool" "kept $_duplicate; it is not owned by the current user" "ask its owner or an administrator to remove it"; return 0; }
  [ -x "$_canonical" ] || { emit WARN "$_host" "fix.$_tool" "kept $_duplicate; canonical copy does not execute" "verify $_canonical, then rm $_duplicate"; return 0; }
  _canonical_text="$(version_of "$_tool" "$_canonical")"
  _canonical_rc=$?
  _duplicate_text="$(version_of "$_tool" "$_duplicate")"
  _duplicate_rc=$?
  if [ "$_canonical_rc" -ne 0 ] || [ "$_duplicate_rc" -ne 0 ]; then
    emit WARN "$_host" "fix.$_tool" "kept $_duplicate; one of the version checks failed" "verify both binaries execute successfully, then remove the older local copy"
    return 0
  fi
  _canonical_version="$(numeric_version "$_canonical_text")"
  _duplicate_version="$(numeric_version "$_duplicate_text")"
  if [ -z "$_canonical_version" ] || [ -z "$_duplicate_version" ]; then
    emit WARN "$_host" "fix.$_tool" "kept $_duplicate; could not compare versions" "compare '$_canonical --version' and '$_duplicate --version', then remove the older local copy"
    return 0
  fi
  if version_is_older "$_canonical_version" "$_duplicate_version"; then
    emit WARN "$_host" "fix.$_tool" "kept newer local $_tool $_duplicate_version; canonical is $_canonical_version" "bash $DFS_ROOT/agents-config/scripts/auto-update-tools.sh --force"
    return 0
  fi
  _duplicate_target="$(readlink "$_duplicate" 2>/dev/null || true)"
  _delete_failed=0
  rm -f -- "$_duplicate" || _delete_failed=1
  case "$_tool" in
    codex)
      if [ -d "$HOME/.local/lib/node_modules/@openai/codex" ]; then
        if [ -O "$HOME/.local/lib/node_modules/@openai/codex" ]; then
          rm -rf -- "$HOME/.local/lib/node_modules/@openai/codex" || _delete_failed=1
        else
          _delete_failed=1
        fi
      fi
      ;;
    claude)
      if [ -d "$HOME/.local/lib/node_modules/@anthropic-ai/claude-code" ]; then
        if [ -O "$HOME/.local/lib/node_modules/@anthropic-ai/claude-code" ]; then
          rm -rf -- "$HOME/.local/lib/node_modules/@anthropic-ai/claude-code" || _delete_failed=1
        else
          _delete_failed=1
        fi
      fi
      case "$_duplicate_target" in
        "$HOME/.local/share/claude/"*|../share/claude/*)
          if [ -d "$HOME/.local/share/claude" ]; then
            if [ -O "$HOME/.local/share/claude" ]; then
              rm -rf -- "$HOME/.local/share/claude" || _delete_failed=1
            else
              _delete_failed=1
            fi
          fi
          ;;
      esac
      ;;
  esac
  if [ "$_delete_failed" -eq 0 ]; then
    emit PASS "$_host" "fix.$_tool" "removed redundant $_duplicate ($_duplicate_version; canonical $_canonical_version)" "-"
  else
    emit WARN "$_host" "fix.$_tool" "could not completely remove the redundant local $_tool install" "inspect and remove only the remaining user-owned duplicate below $HOME/.local"
  fi
}

safe_link() {
  _host="$1" _rel="$2" _target="$3"
  _link="$HOME/$_rel"
  if [ -L "$_link" ]; then
    if [ "$(readlink "$_link")" = "$_target" ]; then return 0; fi
    emit WARN "$_host" "fix.symlink.$_rel" "left existing symlink $_link -> $(readlink "$_link") untouched" "review its target, then ln -sfn $_target $_link"
  elif [ ! -e "$_link" ] && [ -e "$_target" ]; then
    mkdir -p "$(dirname "$_link")"
    if ln -s "$_target" "$_link" && [ -L "$_link" ] && [ "$(readlink "$_link")" = "$_target" ]; then
      emit PASS "$_host" "fix.symlink.$_rel" "created $_link -> $_target" "-"
    else
      emit WARN "$_host" "fix.symlink.$_rel" "could not create and verify $_link" "ln -s $_target $_link"
    fi
  elif [ -e "$_link" ]; then
    emit WARN "$_host" "fix.symlink.$_rel" "left real path $_link untouched" "move it aside after review, then ln -sfn $_target $_link"
  fi
}

apply_worker_fixes() {
  _host="$1" _nvm_bin="$2"
  safe_link "$_host" .bash_profile "$DFS_ROOT/.bash_profile"
  safe_link "$_host" .claude "$DFS_ROOT/.claude"
  safe_link "$_host" .claude-vals "$DFS_ROOT/.claude-vals"
  safe_link "$_host" keys "$DFS_ROOT/keys"
  safe_link "$_host" agents-config "$DFS_ROOT/agents-config"
  safe_link "$_host" veribench "$DFS_ROOT/veribench"
  safe_link "$_host" dfs "$DFS_ROOT"
  safe_link "$_host" .config/valkyrie "$DFS_ROOT/.config/valkyrie"
  if [ -f "$HOME/.claude-vals/.credentials.json" ]; then
    chmod 600 "$HOME/.claude-vals/.credentials.json"
  fi
  if ! klist -s 2>/dev/null || ! tokens 2>/dev/null | grep -q 'tokens for cs.stanford.edu'; then
    if [ -x "$DFS_ROOT/bin/krenew.sh" ] || [ -f "$DFS_ROOT/bin/krenew.sh" ]; then
      bash "$DFS_ROOT/bin/krenew.sh" >/dev/null 2>&1 || true
    fi
  fi
  safe_fix_local_duplicate "$_host" claude "$_nvm_bin/claude"
  safe_fix_local_duplicate "$_host" codex "$_nvm_bin/codex"
}

audit_tool() {
  _host="$1" _tool="$2" _nvm_bin="$3"
  _expected="$(expected_path "$_tool" "$_nvm_bin")"
  _hits="$(which -a "$_tool" 2>/dev/null | awk '!seen[$0]++')"
  _first="$(printf '%s\n' "$_hits" | sed -n '1p')"
  if [ -z "$_first" ]; then
    case "$_tool" in
      docker)
        emit WARN "$_host" "tool.$_tool" "missing; expected $_expected" "ask an administrator to install Docker, or use a node where 'docker --version' works"
        ;;
      *)
        emit FAIL "$_host" "tool.$_tool" "missing; expected $_expected" "$(tool_repair "$_tool" "$_host")"
        ;;
    esac
    return
  fi
  _first_version="$(version_of "$_tool" "$_first")"
  _first_rc=$?
  [ -n "$_first_version" ] || _first_version="no output"
  _hit_details=""
  _stale=""
  _first_num="$(numeric_version "$_first_version")"
  while IFS= read -r _hit; do
    [ -n "$_hit" ] || continue
    _hit_version="$(version_of "$_tool" "$_hit")"
    _hit_rc=$?
    [ -n "$_hit_version" ] || _hit_version="no output"
    if [ "$_hit_rc" -ne 0 ]; then
      _hit_details="${_hit_details}${_hit_details:+,}$_hit@ERROR:$_hit_version"
    else
      _hit_details="${_hit_details}${_hit_details:+,}$_hit@$_hit_version"
    fi
    _hit_num="$(numeric_version "$_hit_version")"
    case "$_tool" in
      claude|codex|clauded|claude-vals|clauded-vals|valkyrie)
        if [ "$_hit" != "$_first" ] && { [ "$_hit_rc" -ne 0 ] || version_is_older "$_hit_num" "$_first_num"; }; then
          _stale="${_stale}${_stale:+,}$_hit"
        fi
        ;;
    esac
  done <<EOF
$_hits
EOF
  if [ "$_tool" = valkyrie ]; then
    _valk_output="$(timeout 150 "$_first" --help 2>&1)"
    _valk_rc=$?
    if [ "$_valk_rc" -ne 0 ] || ! printf '%s\n' "$_valk_output" | grep -q '^Usage: valkyrie'; then
      _first_rc="${_valk_rc:-1}"
      [ "$_first_rc" -ne 0 ] || _first_rc=1
      _hit_details="$_hit_details,runtime@ERROR:$(printf '%s\n' "$_valk_output" | tail -1)"
    fi
  fi
  if ! path_is_canonical "$_tool" "$_first" "$_expected"; then
    emit FAIL "$_host" "tool.$_tool" "resolved=$_first; expected=$_expected; hits=$_hit_details" "source $DFS_ROOT/.bashrc; hash -r; which -a $_tool"
  elif [ "$_first_rc" -ne 0 ]; then
    emit FAIL "$_host" "tool.$_tool" "resolved=$_first but version check failed; hits=$_hit_details" "$(tool_repair "$_tool" "$_host")"
  elif [ -n "$_stale" ]; then
    emit WARN "$_host" "tool.$_tool" "resolved=$_first; stale alternates=$_stale; hits=$_hit_details" "remove user-owned stale copies; ask root to remove root-owned copies"
  else
    emit PASS "$_host" "tool.$_tool" "resolved=$_first; hits=$_hit_details" "-"
  fi
}

tool_repair() {
  _tool="$1" _host="$2"
  case "$_tool" in
    claude|codex) printf 'bash %s/agents-config/scripts/auto-update-tools.sh --force' "$DFS_ROOT" ;;
    clauded|claude-vals|clauded-vals) printf 'bash %s/agents-config/scripts/setup_claude_vals_snap.sh' "$DFS_ROOT" ;;
    valkyrie)
      if [ "$_host" = mercury1 ]; then
        printf 'after the valkfix job finishes: ssh mercury1 bash %s/agents-config/scripts/setup_valkyrie_snap.sh' "$DFS_ROOT"
      else
        printf 'bash %s/agents-config/scripts/setup_valkyrie_snap.sh' "$DFS_ROOT"
      fi
      ;;
    uv) printf 'curl -LsSf https://astral.sh/uv/install.sh | sh' ;;
    harbor) printf 'install -m 755 %s/agents-config/scripts/harbor_snap.sh %s/harbor && uv tool install harbor' "$DFS_ROOT" "$DFS_BIN" ;;
    elan|lake) printf 'curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh' ;;
    node) printf '. %s/nvm/nvm.sh && nvm install --lts && nvm alias default lts/*' "$DFS_ROOT" ;;
    python3) printf 'ask an administrator to install python3' ;;
    *) printf 'install %s, then rerun snap_health.sh --node %s' "$_tool" "$_host" ;;
  esac
}

audit_disk() {
  _host="$1" _label="$2" _path="$3"
  _df="$(df -Pk "$_path" 2>/dev/null | awk 'NR == 2 { print $2, $3, $4, $5, $6 }')"
  if [ -z "$_df" ]; then
    emit FAIL "$_host" "disk.$_label" "cannot stat $_path" "ls -ld $_path; df -h $_path"
    return
  fi
  set -- $_df
  _total_k="$1" _used_k="$2" _free_k="$3" _used_pct="${4%%%}" _mount="$5"
  _free_pct=$((100 - _used_pct))
  _detail="path=$_path mount=$_mount used=${_used_pct}% free=$((_free_k / 1024 / 1024))GiB total=$((_total_k / 1024 / 1024))GiB thresholds=warn<${DISK_WARN_FREE_PCT}%,fail<${DISK_FAIL_FREE_PCT}% free"
  if [ "$_free_pct" -lt "$DISK_FAIL_FREE_PCT" ]; then
    emit FAIL "$_host" "disk.$_label" "$_detail" "du -x -h --max-depth=1 $_path 2>/dev/null | sort -h | tail -20; delete only reviewed, finished, regenerable user artifacts"
  elif [ "$_free_pct" -lt "$DISK_WARN_FREE_PCT" ]; then
    emit WARN "$_host" "disk.$_label" "$_detail" "du -x -h --max-depth=1 $_path 2>/dev/null | sort -h | tail -20"
  else
    emit PASS "$_host" "disk.$_label" "$_detail" "-"
  fi
}

audit_symlink() {
  _host="$1" _rel="$2" _target="$3" _link="$HOME/$_rel"
  if [ -L "$_link" ] && [ "$(readlink "$_link")" = "$_target" ] && [ -e "$_link" ]; then
    emit PASS "$_host" "symlink.$_rel" "$_link -> $_target" "-"
  elif [ -L "$_link" ]; then
    emit FAIL "$_host" "symlink.$_rel" "$_link -> $(readlink "$_link") (expected live target $_target)" "ln -sfn $_target $_link"
  elif [ -e "$_link" ]; then
    emit FAIL "$_host" "symlink.$_rel" "$_link is a real path, expected symlink -> $_target" "review and move $_link aside, then ln -sfn $_target $_link"
  else
    emit FAIL "$_host" "symlink.$_rel" "missing; expected $_link -> $_target" "mkdir -p $(dirname "$_link") && ln -sfn $_target $_link"
  fi
}

audit_auth() {
  _host="$1"
  if klist -s 2>/dev/null; then
    emit PASS "$_host" auth.kerberos "valid Kerberos ticket" "-"
  else
    emit FAIL "$_host" auth.kerberos "missing or expired Kerberos ticket" "bash $DFS_ROOT/bin/krenew.sh"
  fi
  if tokens 2>/dev/null | grep -q 'tokens for cs.stanford.edu'; then
    emit PASS "$_host" auth.afs "valid Andrew File System token" "-"
  else
    emit FAIL "$_host" auth.afs "missing Andrew File System token" "aklog"
  fi
  _pidfile="/tmp/krenew_brando9.pid"
  _pid="$(cat "$_pidfile" 2>/dev/null || true)"
  if [ -n "$_pid" ] && kill -0 "$_pid" 2>/dev/null; then
    emit PASS "$_host" auth.krenew_loop "alive pid=$_pid" "-"
  else
    emit FAIL "$_host" auth.krenew_loop "not alive" "bash $DFS_ROOT/bin/krenew.sh; source $DFS_ROOT/.bashrc"
  fi
  _creds="$HOME/.claude-vals/.credentials.json"
  if [ ! -e "$_creds" ]; then
    emit FAIL "$_host" auth.vals_credentials "missing $_creds" "from the authorized source machine: bash ~/agents-config/scripts/push_claude_vals_creds.sh"
  else
    _mode="$(stat -c '%a' "$_creds" 2>/dev/null || true)"
    if [ "$_mode" = 600 ]; then
      emit PASS "$_host" auth.vals_credentials "present mode=600" "-"
    else
      emit FAIL "$_host" auth.vals_credentials "present mode=$_mode, expected 600" "chmod 600 $_creds"
    fi
  fi
}

smoke_test() {
  _host="$1" _tool="$2"
  if [ "$DO_SMOKE" -ne 1 ]; then
    emit PASS "$_host" "smoke.$_tool" "SKIP (pass --smoke; this spends subscription tokens)" "-"
    return
  fi
  _smoke_err="$(mktemp "${TMPDIR:-/tmp}/snap-smoke.XXXXXX")"
  case "$_tool" in
    codex)
      _last_message="$(mktemp "${TMPDIR:-/tmp}/snap-smoke-last.XXXXXX")"
      timeout 120 codex exec --skip-git-repo-check -s read-only -m gpt-5.6-sol \
        --output-last-message "$_last_message" -c 'model_reasoning_effort="xhigh"' \
        'Reply exactly SNAP_CODEX_OK' >"$_smoke_err" 2>&1
      _smoke_rc=$?
      _out="$(tr -d '\r' <"$_last_message")"
      rm -f -- "$_last_message"
      _marker=SNAP_CODEX_OK
      ;;
    claude)
      _out="$(timeout 120 claude -p --model 'claude-fable-5[1m]' 'Reply exactly SNAP_CLAUDE_OK' 2>"$_smoke_err")"
      _smoke_rc=$?
      _out="$(printf '%s' "$_out" | tr -d '\r')"
      _marker=SNAP_CLAUDE_OK
      ;;
  esac
  _smoke_diag="$(tail -1 "$_smoke_err" 2>/dev/null || true)"
  rm -f -- "$_smoke_err"
  if [ "$_smoke_rc" -eq 0 ] && [ "$_out" = "$_marker" ]; then
    emit PASS "$_host" "smoke.$_tool" "model gate accepted ($_marker)" "-"
  else
    _last="$(printf '%s\n%s\n' "$_out" "$_smoke_diag" | sed '/^$/d' | tail -1)"
    emit FAIL "$_host" "smoke.$_tool" "model gate failed: $_last" "$(tool_repair "$_tool" "$_host")"
  fi
}

worker_main() {
  _host="$(hostname -s)"
  if [ -r "$DFS_ROOT/.bash_env" ]; then
    # Audit the durable shell policy, not a caller process that may predate the latest .bashrc edit.
    # shellcheck disable=SC1090
    . "$DFS_ROOT/.bash_env"
  fi
  _nvm_bin="$(canonical_nvm_bin)"
  if [ "$DO_FIX" -eq 1 ]; then
    apply_worker_fixes "$_host" "$_nvm_bin"
    hash -r 2>/dev/null || true
  fi
  emit PASS "$_host" reachability "reachable via $(hostname -f 2>/dev/null || hostname)" "-"
  _os="$(. /etc/os-release 2>/dev/null && printf '%s %s' "${NAME:-unknown}" "${VERSION_ID:-unknown}")"
  _glibc="$(ldd --version 2>&1 | head -1)"
  emit PASS "$_host" platform "os=$_os; glibc=$_glibc" "-"
  _shell_probe="$(bash -lc 'printf "%s|%s|%s\n" "$BASH_ENV" "$(command -v codex)" "$(bash -c "command -v codex")"' 2>/dev/null | tail -1)"
  _shell_expected="$DFS_ROOT/.bash_env|$_nvm_bin/codex|$_nvm_bin/codex"
  if [ -r "$DFS_ROOT/.bash_env" ] && [ "$_shell_probe" = "$_shell_expected" ] &&
     grep -q 'SNAP canonical agent CLI path' "$DFS_ROOT/.bashrc" 2>/dev/null &&
     case "$PATH" in "$_nvm_bin:$DFS_BIN:"*) true ;; *) false ;; esac; then
    emit PASS "$_host" shell.canonical_path "login and child non-login shells resolve canonical Codex; BASH_ENV=$DFS_ROOT/.bash_env" "-"
  else
    emit FAIL "$_host" shell.canonical_path "canonical shell policy failed; observed=${_shell_probe:-no probe output}; expected=$_shell_expected" "restore the marked SNAP canonical agent CLI path block in $DFS_ROOT/.bashrc and $DFS_ROOT/.bash_env"
  fi
  for _tool in claude codex clauded claude-vals clauded-vals valkyrie uv harbor docker elan lake python3 node; do
    audit_tool "$_host" "$_tool" "$_nvm_bin"
  done
  audit_disk "$_host" lfs "/lfs/$_host/0/brando9"
  audit_disk "$_host" dfs "$DFS_ROOT"
  audit_symlink "$_host" .bash_profile "$DFS_ROOT/.bash_profile"
  audit_symlink "$_host" .claude "$DFS_ROOT/.claude"
  audit_symlink "$_host" .claude-vals "$DFS_ROOT/.claude-vals"
  audit_symlink "$_host" keys "$DFS_ROOT/keys"
  audit_symlink "$_host" agents-config "$DFS_ROOT/agents-config"
  audit_symlink "$_host" veribench "$DFS_ROOT/veribench"
  audit_symlink "$_host" dfs "$DFS_ROOT"
  audit_symlink "$_host" .config/valkyrie "$DFS_ROOT/.config/valkyrie"
  audit_auth "$_host"
  smoke_test "$_host" codex
  smoke_test "$_host" claude
}

audit_one_repo() {
  _repo="$1" _name="$(basename "$_repo")"
  _branch="$(git -C "$_repo" symbolic-ref --quiet --short HEAD 2>/dev/null || printf DETACHED)"
  _upstream="$(git -C "$_repo" rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || true)"
  _ahead=0 _behind=0
  if [ -n "$_upstream" ]; then
    _counts="$(git -C "$_repo" rev-list --left-right --count HEAD..."$_upstream" 2>/dev/null || printf '0 0')"
    _ahead="$(printf '%s' "$_counts" | awk '{print $1}')"
    _behind="$(printf '%s' "$_counts" | awk '{print $2}')"
  fi
  _status_file="$REPO_TMP/status"
  if timeout 45 git -C "$_repo" status --porcelain --untracked-files=all >"$_status_file" 2>/dev/null; then
    _dirty="$(wc -l <"$_status_file" | tr -d ' ')"
    if [ "$_dirty" -gt 0 ] || [ "$_ahead" -gt 0 ] || [ "$_behind" -gt 0 ]; then
      emit WARN shared-dfs "git.$_name" "branch=$_branch upstream=${_upstream:-none} ahead=$_ahead behind=$_behind dirty_files=$_dirty" "use one dedicated clone per agent; inspect with git -C $_repo status; do not reset or stash shared work"
    else
      emit PASS shared-dfs "git.$_name" "branch=$_branch upstream=${_upstream:-none} ahead=0 behind=0 dirty_files=0" "-"
    fi
  else
    emit WARN shared-dfs "git.$_name" "branch=$_branch upstream=${_upstream:-none} ahead=$_ahead behind=$_behind dirty_files=unknown (status timed out)" "inspect manually: git -C $_repo status --short --branch"
  fi
}

audit_repositories() {
  _repo_list="$RUN_TMP/repos"
  find "$DFS_ROOT" -mindepth 2 -maxdepth 2 -name .git \( -type d -o -type f \) -printf '%h\n' 2>/dev/null | sort >"$_repo_list"
  if [ ! -s "$_repo_list" ]; then
    emit WARN shared-dfs git.clones "no top-level DFS clones discovered" "find $DFS_ROOT -mindepth 2 -maxdepth 2 -type d -name .git"
    return
  fi
  while IFS= read -r _repo; do
    REPO_TMP="$(mktemp -d "$RUN_TMP/repo.XXXXXX")"
    audit_one_repo "$_repo"
    rm -rf -- "$REPO_TMP"
  done <"$_repo_list"
}

audit_slurm_controller() {
  _slurm_targets="${ONLY_NODE:-$GATED_NODES}"
  _account_out="$(timeout 15 ssh -o BatchMode=yes -o ConnectTimeout="$CONNECT_TIMEOUT" ilc.stanford.edu \
    'command -v srun >/dev/null && showaccount' 2>&1)"
  _account_rc=$?
  if [ "$_account_rc" -ne 0 ]; then
    emit FAIL slurm-controller slurm.access "cannot query ilc.stanford.edu: $_account_out" "bash $DFS_ROOT/bin/krenew.sh; ssh ilc.stanford.edu showaccount"
    return
  fi
  if printf '%s\n' "$_account_out" | grep -qw infolab; then
    emit PASS slurm-controller slurm.account "infolab account association is present" "-"
  else
    emit FAIL slurm-controller slurm.account "showaccount returned no infolab association; gated nodes cannot be allocated" "email il-action@cs.stanford.edu and request the infolab Slurm association for brando9"
  fi
  _states="$(timeout 15 ssh -o BatchMode=yes -o ConnectTimeout="$CONNECT_TIMEOUT" ilc.stanford.edu \
    "sinfo -h -N -n $(printf '%s' "$_slurm_targets" | tr ' ' ',') -o '%N=%T' | sort -u | paste -sd, -" 2>/dev/null || true)"
  _missing_nodes=""
  for _target in $_slurm_targets; do
    if ! printf '%s\n' "$_states" | tr ',' '\n' | grep -q "^$_target="; then
      _missing_nodes="${_missing_nodes}${_missing_nodes:+,}$_target"
    fi
  done
  _unhealthy_states="$(printf '%s\n' "$_states" | tr ',' '\n' | awk -F= 'tolower($2) ~ /^(down|drain|fail|unknown|unk|invalid)/ {print}' | paste -sd, -)"
  if [ -n "$_missing_nodes" ]; then
    emit FAIL slurm-controller slurm.inventory "missing from Slurm inventory: $_missing_nodes; observed: ${_states:-none}" "ssh ilc.stanford.edu sinfo -N; ask il-action@cs.stanford.edu whether the missing nodes were retired"
  elif [ -n "$_unhealthy_states" ]; then
    emit FAIL slurm-controller slurm.inventory "target nodes are unavailable: $_unhealthy_states; observed: $_states" "ssh ilc.stanford.edu sinfo -N -l; choose an idle/mixed node or ask il-action@cs.stanford.edu"
  elif [ -n "$_states" ]; then
    emit PASS slurm-controller slurm.inventory "targets present: $_states" "-"
  else
    emit WARN slurm-controller slurm.inventory "could not confirm gated nodes in Slurm inventory" "ssh ilc.stanford.edu sinfo -N"
  fi
}

json_escape() {
  # JSON forbids every unescaped byte below 0x20, not only newline/tab/carriage-return.
  _json=$1
  _json_i=0
  while [ "$_json_i" -lt "${#_json}" ]; do
    _json_c=${_json:$_json_i:1}
    case "$_json_c" in
      '"') printf '\\"' ;;
      \\) printf '\\\\' ;;
      $'\b') printf '\\b' ;;
      $'\f') printf '\\f' ;;
      $'\n') printf '\\n' ;;
      $'\r') printf '\\r' ;;
      $'\t') printf '\\t' ;;
      *)
        LC_ALL=C printf -v _json_code '%d' "'$_json_c"
        if [ "$_json_code" -lt 32 ]; then
          printf '\\u%04x' "$_json_code"
        else
          printf '%s' "$_json_c"
        fi
        ;;
    esac
    _json_i=$((_json_i + 1))
  done
}

render_record() {
  _sev="$1" _host="$2" _check="$3" _detail="$4" _repair="$5"
  [ "$_sev" != FAIL ] || FAILURES=$((FAILURES + 1))
  if [ "$DO_JSON" -eq 1 ]; then
    [ "$JSON_FIRST" -eq 1 ] || printf ',\n'
    JSON_FIRST=0
    printf '  {"status":"%s","node":"%s","check":"%s","detail":"%s","repair":' \
      "$(json_escape "$_sev")" "$(json_escape "$_host")" "$(json_escape "$_check")" "$(json_escape "$_detail")"
    if [ "$_repair" = - ]; then
      printf 'null}'
    else
      printf '"%s"}' "$(json_escape "$_repair")"
    fi
  else
    printf '%-4s %-12s %-28s %s\n' "$_sev" "$_host" "$_check" "$_detail"
    [ "$_repair" = - ] || printf '     REPAIR: %s\n' "$_repair"
  fi
}

if [ "$WORKER" -eq 1 ]; then
  worker_main
  exit 0
fi

if [ -n "$ONLY_NODE" ]; then
  TARGET_NODES="$ONLY_NODE"
else
  TARGET_NODES="$ALL_NODES"
fi

RUN_TMP="$(mktemp -d "${TMPDIR:-/tmp}/snap-health.XXXXXX")"
WORKER_PIDS=""
cleanup() {
  for _cleanup_pid in $WORKER_PIDS; do
    kill "$_cleanup_pid" 2>/dev/null || true
  done
  [ -z "$WORKER_PIDS" ] || wait $WORKER_PIDS 2>/dev/null || true
  rm -rf -- "$RUN_TMP"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
SCRIPT_PATH="$(cd "$(dirname "$0")" 2>/dev/null && pwd)/$(basename "$0")"
FIX_RESULTS="$RUN_TMP/controller-fixes"
: >"$FIX_RESULTS"

if [ "$DO_FIX" -eq 1 ]; then
  _updater="$(dirname "$SCRIPT_PATH")/auto-update-tools.sh"
  if [ -x "$_updater" ] || [ -r "$_updater" ]; then
    if bash "$_updater" --force; then
      emit PASS controller fix.agent_cli_update "canonical NVM updater completed; see $DFS_ROOT/.cache/agent-cli-update.log" "-" >>"$FIX_RESULTS"
    else
      emit FAIL controller fix.agent_cli_update "canonical NVM updater failed; see $DFS_ROOT/.cache/agent-cli-update.log" "bash $_updater --force" >>"$FIX_RESULTS"
    fi
  fi
  if [ ! -x "$DFS_BIN/claude-vals" ] || [ ! -x "$DFS_BIN/clauded-vals" ]; then
    _vals_installer="$(dirname "$SCRIPT_PATH")/setup_claude_vals_snap.sh"
    if bash "$_vals_installer" >/dev/null 2>&1; then
      emit PASS controller fix.vals_wrappers "installed the shared Vals wrappers once" "-" >>"$FIX_RESULTS"
    else
      emit FAIL controller fix.vals_wrappers "shared Vals wrapper installer failed" "bash $_vals_installer" >>"$FIX_RESULTS"
    fi
  fi
  if [ ! -x "$DFS_BIN/harbor" ]; then
    _harbor_source="$(dirname "$SCRIPT_PATH")/harbor_snap.sh"
    if [ -r "$_harbor_source" ] && install -m 755 "$_harbor_source" "$DFS_BIN/harbor"; then
      emit PASS controller fix.harbor_wrapper "installed $DFS_BIN/harbor once" "-" >>"$FIX_RESULTS"
    else
      emit FAIL controller fix.harbor_wrapper "could not install the shared Harbor wrapper" "install -m 755 $_harbor_source $DFS_BIN/harbor" >>"$FIX_RESULTS"
    fi
  fi
fi

for _node in $TARGET_NODES; do
  (
    # The parent owns RUN_TMP; background subshells must not inherit its cleanup trap.
    trap - EXIT HUP INT TERM
    _out="$RUN_TMP/$_node.out" _err="$RUN_TMP/$_node.err" _rc="$RUN_TMP/$_node.rc"
    if [ "$_node" = "$(hostname -s)" ]; then
      bash "$SCRIPT_PATH" --_worker $([ "$DO_FIX" -eq 1 ] && printf '%s' --fix) $([ "$DO_SMOKE" -eq 1 ] && printf '%s' --smoke) >"$_out" 2>"$_err"
    else
      timeout 420 ssh -o BatchMode=yes -o ConnectTimeout="$CONNECT_TIMEOUT" "$_node" \
        bash -s -- --_worker $([ "$DO_FIX" -eq 1 ] && printf '%s' --fix) $([ "$DO_SMOKE" -eq 1 ] && printf '%s' --smoke) \
        <"$SCRIPT_PATH" >"$_out" 2>"$_err"
    fi
    printf '%s\n' "$?" >"$_rc"
  ) &
  WORKER_PIDS="$WORKER_PIDS $!"
done
wait
WORKER_PIDS=""

RESULTS="$RUN_TMP/results"
: >"$RESULTS"
cat "$FIX_RESULTS" >>"$RESULTS"
for _node in $TARGET_NODES; do
  _rc="$(cat "$RUN_TMP/$_node.rc" 2>/dev/null || printf 255)"
  if [ "$_rc" -eq 0 ]; then
    cat "$RUN_TMP/$_node.out" >>"$RESULTS"
  else
    _reason="$(tail -3 "$RUN_TMP/$_node.err" 2>/dev/null | tr '\n' ' ')"
    if grep -qi 'pam_slurm_adopt\|no active jobs' "$RUN_TMP/$_node.err" 2>/dev/null; then
      emit WARN "$_node" reachability "Slurm-gated (ssh refused without an allocation): $_reason" \
        "ssh -t ilc.stanford.edu \"srun --partition=il-cpu --account=infolab --nodelist=$_node --nodes=1 --ntasks=1 --cpus-per-task=1 --time=00:10:00 --pty bash -l\"; then run $DFS_ROOT/agents-config/scripts/snap_health.sh --node $_node inside the allocation" >>"$RESULTS"
    else
      emit FAIL "$_node" reachability "unreachable: $_reason" \
        "ssh -vv $_node; if the host is retired or its mount is broken, file a SNAP administrator ticket" >>"$RESULTS"
    fi
  fi
done

# Repository state is shared through DFS, so audit every top-level clone once rather than once per node.
if [ -z "$ONLY_NODE" ]; then
  audit_slurm_controller >>"$RESULTS"
else
  case " $GATED_NODES " in *" $ONLY_NODE "*) audit_slurm_controller >>"$RESULTS" ;; esac
fi
audit_repositories >>"$RESULTS"

JSON_FIRST=1
[ "$DO_JSON" -eq 0 ] || printf '[\n'
while IFS=$'\t' read -r _sev _host _check _detail _repair; do
  [ -n "$_sev" ] || continue
  render_record "$_sev" "$_host" "$_check" "$_detail" "${_repair:--}"
done <"$RESULTS"
[ "$DO_JSON" -eq 0 ] || printf '\n]\n'

[ "$FAILURES" -eq 0 ]
