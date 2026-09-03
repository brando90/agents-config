#!/bin/bash
# TLDR: Idempotently installs the Vals platform tooling (Valkyrie CLI `valkyrie`/`valk`, the
# public agent registry, and the benchmark-service framework) on a Stanford SNAP node — everything
# shared on DFS so all nodes get it, with a per-node ~/.config/valkyrie symlink for the credentials.
#
# Usage (run ON a SNAP node; steps 1-2 are shared, so only step 3 really repeats per node):
#   bash ~/agents-config/scripts/setup_valkyrie_snap.sh [--force]
#
# What it does NOT do: put a Vals API key on disk. Finish with ONE of
#   export VALKYRIE_API_KEY=...   &&  valkyrie config init      # hosted mode, non-interactive key
#   valkyrie config init                                        # prompts for the key
# The resulting ~/.config/valkyrie/valkyrie.yaml lands on DFS and is then shared by every node.
set -euo pipefail

DFS_ROOT="${DFS_ROOT:-/dfs/scratch0/brando9}"
DFS_BIN="$DFS_ROOT/bin"
AFS_BIN="${AFS:-/afs/cs.stanford.edu/u/brando9}/bin"
VALK_CFG="$DFS_ROOT/.config/valkyrie"
FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1

log() { printf '[valkyrie] %s\n' "$*"; }
[ -d "$DFS_ROOT" ] || { echo "[valkyrie] FATAL: $DFS_ROOT not mounted on $(hostname)" >&2; exit 1; }

# uv writes tool venvs + managed pythons to DFS so every node runs the same install.
# (mercury nodes only have system python3.8; the uv-managed 3.12 on DFS is what makes valk work there.)
export UV_TOOL_DIR="$DFS_ROOT/uv/tools"
# uv's own shims go to a staging dir, NOT $DFS_BIN: the PATH copies are hand-written wrappers below
# (a `uv tool install` would otherwise clobber them with bare symlinks).
export UV_TOOL_BIN_DIR="$DFS_ROOT/uv/bin"
export UV_PYTHON_INSTALL_DIR="$DFS_ROOT/uv/python"
# only-managed matters: the system python3.12 exists on skampere but NOT on mercury (3.8 there), and
# a tool venv pinned to /usr/bin/python3.12 would be broken on any node lacking it. A uv-managed
# interpreter under $UV_PYTHON_INSTALL_DIR (DFS) is visible and identical on every node.
export UV_PYTHON_PREFERENCE=only-managed
mkdir -p "$UV_TOOL_DIR" "$UV_PYTHON_INSTALL_DIR" "$DFS_BIN"

# --- 1. repos on DFS ---------------------------------------------------------------------------
# The repos live on DFS and are therefore shared: pulling them again on every node is pure DFS
# round-trips. Clone when missing; only pull with --force (or VALKYRIE_PULL=1).
clone_or_pull() {  # $1=url $2=dest
  local url="$1" dest="$2"
  if [ -d "$dest/.git" ]; then
    if [ "$FORCE" -eq 1 ] || [ "${VALKYRIE_PULL:-0}" = "1" ]; then
      git -C "$dest" pull --quiet --recurse-submodules 2>/dev/null && log "pulled  $dest" || log "WARN    pull failed: $dest"
    else
      log "keep    $dest (already cloned; --force or VALKYRIE_PULL=1 to pull)"
    fi
  else
    git clone --quiet --recurse-submodules "$url" "$dest" && log "cloned  $dest" || log "WARN    clone failed: $url"
  fi
}
clone_or_pull https://github.com/vals-ai/Valkyrie.git                  "$DFS_ROOT/Valkyrie"
clone_or_pull https://github.com/vals-ai/public-agent-registry.git     "$DFS_ROOT/vals-public-agent-registry"
clone_or_pull https://github.com/vals-ai/create-benchmark-service.git  "$DFS_ROOT/vals-create-benchmark-service"

# --- 2. the CLI itself (shared via $DFS_BIN, which is already on PATH in .bashrc) ---------------
# "on PATH" is NOT proof of a working install: a stale shim, or a venv pinned to a system python
# that exists on skampere but not on mercury, both leave `valkyrie` present and broken. Health is a
# property of the VENV, so a missing wrapper never triggers a needless 5-minute reinstall.
VENV_BIN="$UV_TOOL_DIR/valkyrie/bin"
valk_venv_healthy() {
  local py="$VENV_BIN/python" real
  [ -x "$VENV_BIN/valkyrie" ] && [ -e "$py" ] || return 1
  real="$(readlink -f "$py" 2>/dev/null)" || return 1
  [ -x "$real" ] || return 1                              # interpreter must exist ON THIS NODE
  case "$real" in "$DFS_ROOT"/*) ;; *) return 1 ;; esac    # ... and be the DFS-managed one
  return 0
}
# NB: health is deliberately a FILE check, not a `valkyrie --version` run. The CLI imports boto3 +
# logfire + opentelemetry off DFS, so a cold first start takes minutes on this cluster; running it
# here would make the installer look hung, and a timeout would trigger a needless 5-minute reinstall.
# The PYTHONPATH breakage that a runtime check would have caught is handled structurally by the
# wrappers below, which are rewritten on every run.
if [ "$FORCE" -eq 0 ] && valk_venv_healthy; then
  log "keep    $VENV_BIN/valkyrie — venv healthy (DFS-managed python $(readlink -f "$VENV_BIN/python" | sed 's|.*/uv/python/||')); --force to reinstall"
else
  [ "$FORCE" -eq 1 ] || log "repair  valkyrie venv missing/stale on $(hostname) — reinstalling"
  log "installing valkyrie CLI (uv tool install, python 3.12 managed by uv on DFS)…"
  uv python install 3.12 2>&1 | tail -2
  uv tool install --force --python 3.12 --python-preference only-managed \
    git+https://github.com/vals-ai/Valkyrie@prod 2>&1 | tail -5
fi

# PATH copies are wrappers, not symlinks, for one load-bearing reason: .bashrc exports
# PYTHONPATH=/dfs/scratch0/<user>/lib/python3.12/site-packages (mistral-vibe's install). That path
# shadows the venv's opentelemetry and makes every valkyrie import die with
# "ImportError: cannot import name '_ON_EMIT_RECURSION_COUNT_KEY' from 'opentelemetry.context'".
for bin_dir in "$DFS_BIN" "$AFS_BIN"; do
  if mkdir -p "$bin_dir" 2>/dev/null && [ -w "$bin_dir" ]; then
    for name in valkyrie valk; do
      dest="$bin_dir/$name"
      rm -f "$dest"          # it may be a symlink INTO the venv — writing through it would corrupt the venv
      cat > "$dest" <<EOF
#!/bin/bash
# TLDR: \`$name\` (Valkyrie CLI) from the DFS-shared uv tool venv, with the interpreter environment
# scrubbed so the node's global PYTHONPATH cannot shadow the venv's packages.
# Installed by ~/agents-config/scripts/setup_valkyrie_snap.sh — edit there, not here.
unset PYTHONPATH PYTHONHOME VIRTUAL_ENV
exec $VENV_BIN/$name "\$@"
EOF
      chmod 755 "$dest"
      log "wrapper $dest"
    done
  else
    log "SKIP    $bin_dir (not writable — AFS token expired? run 'aklog' and re-run)"
  fi
done

# --- 3. per-node config symlink (credentials live once, on DFS) --------------------------------
mkdir -p "$VALK_CFG" && chmod 700 "$VALK_CFG"
mkdir -p "$HOME/.config"
LINK="$HOME/.config/valkyrie"
if [ -L "$LINK" ]; then
  [ "$(readlink "$LINK")" = "$VALK_CFG" ] || ln -sfn "$VALK_CFG" "$LINK"
  log "symlink $LINK -> $(readlink "$LINK")"
elif [ -d "$LINK" ]; then
  if [ -z "$(ls -A "$LINK")" ]; then rmdir "$LINK" && ln -sfn "$VALK_CFG" "$LINK" && log "symlink $LINK -> $VALK_CFG (replaced empty dir)"
  else log "WARN    $LINK is a non-empty real dir; merge into $VALK_CFG by hand"; fi
else
  ln -sfn "$VALK_CFG" "$LINK" && log "symlink $LINK -> $VALK_CFG"
fi

# --- 4. report ---------------------------------------------------------------------------------
echo
log "=== state on $(hostname) ==="
VER="$(timeout 90 "$DFS_BIN/valkyrie" --version 2>&1 | tail -1)"
[ -n "$VER" ] || VER="(no answer within 90s — cold DFS import; run 'valkyrie --version' again once warm)"
log "  valkyrie: $(command -v valkyrie || echo 'NOT on PATH (open a new shell)')  $VER"
if [ -f "$VALK_CFG/valkyrie.yaml" ]; then
  log "  config:   $VALK_CFG/valkyrie.yaml present"
else
  log "  config:   MISSING — run: export VALKYRIE_API_KEY=<vals key> && valkyrie config init"
fi
log "  repos:    $(ls -d "$DFS_ROOT"/Valkyrie "$DFS_ROOT"/vals-* 2>/dev/null | tr '\n' ' ')"
