#!/bin/bash
# Stanford SNAP cluster setup for VeriBench.
# This script handles SNAP-specific filesystem setup (AFS/DFS/LFS), then runs the
# universal setup.sh (at repo root) for everything else (uv, Python deps, Lean, Mathlib, PyPantograph).
#
# For agent documentation architecture, see: ~/agent-config/INDEX_RULES.md
# For per-node setup (when DFS is already configured), see: agents-config/machine/snap.md
#
# --> IMPORTANT: Please always do an ls -lah or echo $NEW_ENV etc to check that doing the right things!
# you need to read this:
# https://ilwiki.stanford.edu/doku.php?id=hints:storefiles
# https://ilwiki.stanford.edu/doku.php?id=hints:long-jobs
# https://ilwiki.stanford.edu/doku.php?id=koyejo-servers:koyejo

# ---- SNAP filesystem setup (AFS/DFS/LFS) ----

# If you've never set up before you will be in afs and $HOME will point to afs
export USER_NAME=$(whoami)
export AFS=/afs/cs.stanford.edu/u/$USER_NAME
export DFS=/dfs/scratch0/$USER_NAME
export LOCAL_MACHINE_PWD="/lfs/$(hostname | cut -d. -f1)/0/$USER_NAME"
mkdir -p "$LOCAL_MACHINE_PWD"
# Point HOME to LFS so python scripts store outputs locally (fast)
export HOME=$LOCAL_MACHINE_PWD
# Create DFS directory if it doesn't exist
mkdir -p "$DFS"
cd "$DFS"
# Clone the veribench repo to DFS (shared across nodes)
if [ ! -d "$DFS/veribench/.git" ]; then
    git clone git@github.com:brando90/veribench.git "$DFS/veribench"
fi
# Symlink veribench from LFS home → DFS
ln -sfn "$DFS/veribench" "$HOME/veribench"
# Copy .bashrc from veribench to DFS (canonical location), then symlink from AFS and LFS
cp "$HOME/veribench/experiments/.bashrc" "$DFS/.bashrc"
ln -sf "$DFS/.bashrc" "$AFS/.bashrc"
ln -sf "$DFS/.bashrc" "$HOME/.bashrc"
# Source it (sets HOME to LFS, adds DFS/bin to PATH, loads nvm)
source "$HOME/.bashrc"
echo "HOME=$HOME  (should be /lfs/<hostname>/0/$USER_NAME)"

# ---- Agent config (agents-config) ----
# Clone agent-config repo to DFS, symlink entry points from home
if [ ! -d "$DFS/agents-config/.git" ]; then
    git clone https://github.com/brando90/agents-config.git "$DFS/agents-config"
fi
ln -sfn "$DFS/agents-config" "$HOME/agents-config"
ln -sf "$HOME/agents-config/CLAUDE.md" "$HOME/CLAUDE.md"
ln -sf "$HOME/agents-config/agents.md" "$HOME/agents.md"

# ---- Symlink keys directory (DFS → LFS home) ----
ln -sfn "$DFS/keys" "$HOME/keys"

# ---- Symlink all DFS projects into LFS home (short paths) ----
for proj in "$DFS"/*/; do
  [ -d "$proj" ] || continue
  name=$(basename "$proj")
  [ ! -e "$HOME/$name" ] && ln -s "$DFS/$name" "$HOME/$name"
done

# ---- Git config (change to your name/email) ----
# git config --global user.name "YOUR NAME"
# git config --global user.email "YOUR_EMAIL@gmail.com"

# ---- Run universal setup (uv, Python deps, Lean, Mathlib, PyPantograph) ----
# veribench_setup.sh handles installation; it calls veribench_test.sh at the end to verify.
bash ~/veribench/veribench_setup.sh

# ---- mistral-vibe (installed once to DFS, shared across all servers) ----
# Binary: /dfs/scratch0/brando9/bin/vibe (already on PATH via DFS/bin)
# Packages: /dfs/scratch0/brando9/lib/python3.12/site-packages
# PYTHONPATH entry added to ~/.bashrc — no per-server install needed.
# If vibe is missing (e.g. fresh DFS), re-run:
#   python3.12 -m pip install mistral-vibe --prefix /dfs/scratch0/brando9
#   sed -i '1s|.*|#!/usr/bin/env python3.12|' /dfs/scratch0/brando9/bin/vibe
# API key: export MISTRAL_API_KEY=$(cat ~/keys/mistral_api_key.txt)
# Verify:  PYTHONPATH="/dfs/scratch0/brando9/lib/python3.12/site-packages:$PYTHONPATH" vibe --version
