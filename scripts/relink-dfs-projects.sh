#!/usr/bin/env bash
# relink-dfs-projects.sh — idempotently create `~/<proj>` → `/dfs/scratch0/<user>/<proj>` symlinks
# for every project directory in DFS that doesn't already have a home-dir link.
#
# Why: the project-symlink loop in `machine/snap.md` New Node Setup runs once at
# setup time. When a new repo is later added to `/dfs/scratch0/<user>/`, its
# `~/<proj>` shortcut is never created, so tooling that expects `~/<proj>`
# paths silently breaks. Re-run this script after adding a new DFS repo.
#
# Safe to re-run: only creates links that don't already exist; never touches
# existing files, dirs, or links.
#
# Usage:
#   bash ~/agents-config/scripts/relink-dfs-projects.sh          # use $USER
#   bash ~/agents-config/scripts/relink-dfs-projects.sh brando9  # override

set -euo pipefail

user="${1:-${USER:?set USER or pass as arg}}"
dfs_root="/dfs/scratch0/$user"
home_dir="${HOME:-/lfs/$(hostname -s)/0/$user}"

if [ ! -d "$dfs_root" ]; then
  echo "error: $dfs_root does not exist" >&2
  exit 1
fi

created=0
skipped=0
for proj in "$dfs_root"/*/; do
  [ -d "$proj" ] || continue
  name=$(basename "$proj")
  target="$home_dir/$name"
  if [ -e "$target" ] || [ -L "$target" ]; then
    skipped=$((skipped + 1))
    continue
  fi
  ln -s "$dfs_root/$name" "$target"
  echo "linked $target -> $dfs_root/$name"
  created=$((created + 1))
done

echo "---"
echo "created: $created, already-present: $skipped"
