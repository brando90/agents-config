# Machine: SNAP — Stanford SNAP / Infolab Cluster

Multi-node GPU cluster. Shared DFS/AFS filesystems, per-node LFS local scratch. No job scheduler — direct SSH to nodes.

Full storage docs: https://ilwiki.stanford.edu/doku.php?id=hints:storefiles

---

## Connection

```bash
ssh <username>@<hostname>.stanford.edu
```

- **Access:** Direct SSH from Stanford network or VPN. No jump host.
- **Port:** 22
- **Persistent sessions:** Use `byobu` (tmux-based). Config is shared across nodes via DFS (`BYOBU_CONFIG_DIR` set in `.bashrc`).

---

## Filesystem

| Mount | Type | Scope | Speed | Notes |
|-------|------|-------|-------|-------|
| `/afs/cs.stanford.edu/u/<user>` | AFS | All servers | Slow | Backed up daily, quota enforced. Config files and important docs. |
| `/lfs/<hostname>/0/<user>` | LFS | Local to server | Fastest | Not backed up. Set as `$HOME` in `.bashrc`. Active work, datasets, checkpoints. |
| `/dfs/scratch0/<user>` | DFS (AutoFS) | All servers | Medium | Shared network FS. Repos, shared scripts, binaries. Trigger mount: `cd /dfs/scratch0`. |
| `/dfs/user/<user>` | DFS personal | All servers | Medium | Personal quota'd network storage. Trigger: `cd /dfs/user/<user>`. |

**Key rules:**
- `$HOME` is set to `/lfs/<hostname>/0/<user>` (LFS) in `.bashrc` — fast local scratch.
- `~/.bashrc` is a symlink to `/dfs/scratch0/<user>/.bashrc` — shared across all nodes.
- **Clone repos to DFS** (`/dfs/scratch0/<user>/`), then symlink from LFS home. Never clone directly to LFS — it's node-local and not backed up.
- **Run Docker/Harbor from LFS**, not AFS/DFS. NFS/AFS has root-squash that blocks Docker writes.
- If a `/dfs/` mount is missing, `cd /dfs/scratch0` triggers AutoFS. If still missing, check https://ilwiki.stanford.edu/doku.php?id=hints:storefiles.

---

## Compute — Known Server Profiles

Hardware varies per node. **Always verify at runtime:**

```bash
hostname
nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv,noheader
nproc && free -h
```

| Server | GPUs | RAM |
|--------|------|-----|
| `ampere1` | 8x A100-SXM4-80GB | ~2 TiB |
| `ampere8` | 8x A100-SXM4-80GB | ~2 TiB |
| `skampere2` | 8x H200 140 GiB | ~3 TiB |
| `skampere3` | 8x B200 179 GiB | ~3 TiB |
| `mercury1` | 10x RTX A4000 16 GB | ~487 GB |
| `mercury2` | 10x RTX A4000 16 GB | ~503 GB |

- **CUDA:** 12.4 (check with `nvcc --version`)
- **OS:** Ubuntu 22.04
- **System Python:** `/usr/bin/python3` (version varies per node — check `python3 --version`)

---

## Environment Setup

Read `~/.bashrc` directly — it is the source of truth for paths, env vars, and tool setup. Do not duplicate secrets here.

Key paths and vars set in `.bashrc`:
- `$HOME` = `/lfs/<hostname>/0/<user>` (LFS, set dynamically per server)
- `$AFS` = `/afs/cs.stanford.edu/u/<user>`
- `$DFS` = `/dfs/scratch0/<user>`
- `~/keys/` — API keys and tokens (loaded by `.bashrc`, never committed)
- `/dfs/scratch0/<user>/bin/` — shared binaries on PATH (claude, clauded, vibe, etc.)
- `~/.nvm/` — Node.js via nvm (on DFS, shared)
- `~/.virtualenvs/` — Python virtual environments
- `BYOBU_CONFIG_DIR` = `/dfs/scratch0/<user>/.byobu_shared` (shared tmux config)

### Claude Code

- `claude` binary: `/dfs/scratch0/<user>/bin/claude` (DFS — shared, no per-node install)
- `clauded` script: `/dfs/scratch0/<user>/bin/clauded` (runs `claude --dangerously-skip-permissions "$@"`)
- Auth: `CLAUDE_CODE_OAUTH_TOKEN` set in `.bashrc`

### Docker

```bash
cat ~/keys/<ghcr_token_file> | docker login ghcr.io -u <github_username> --password-stdin
```

---

## New Node Setup

When SSH-ing into a new SNAP node for the first time:

```bash
# 1. Create LFS home
mkdir -p /lfs/$(hostname -s)/0/<user>

# 2. Symlink .bashrc from AFS → DFS (before HOME is moved)
ln -sf /dfs/scratch0/<user>/.bashrc /afs/cs.stanford.edu/u/<user>/.bashrc

# 3. Source it (sets HOME to LFS, adds DFS/bin to PATH, loads nvm)
source ~/.bashrc

# 4. Also symlink in LFS home (for after HOME is set)
ln -sf /dfs/scratch0/<user>/.bashrc ~/.bashrc

# 5. Symlink agent-config entry points
ln -sf /dfs/scratch0/<user>/agent-config/CLAUDE.md ~/CLAUDE.md
ln -sf /dfs/scratch0/<user>/agent-config/agents.md ~/agents.md

# 6. Create DFS project symlinks in LFS home
# (symlink each DFS project into LFS home so paths are short)
for proj in /dfs/scratch0/<user>/*/; do
  [ -d "$proj" ] || continue
  name=$(basename "$proj")
  [ ! -e ~/"$name" ] && ln -s "/dfs/scratch0/<user>/$name" ~/"$name"
done

# 7. Verify
which claude && which clauded
```

---

## Common Issues

### AFS token expiration
**Symptom:** Home directory unresponsive. `ls /afs/cs/...` hangs.
**Fix:** `kinit <user>@CS.STANFORD.EDU` then `aklog`.

### DFS mount missing
**Symptom:** `/dfs/scratch0` doesn't exist or is empty.
**Fix:** `cd /dfs/scratch0` triggers AutoFS. If still missing, check https://ilwiki.stanford.edu/doku.php?id=hints:storefiles.

### Local scratch (LFS) full
**Symptom:** Write failures on `/lfs/`.
**Fix:** Clean up old outputs, Docker images: `docker system prune -a`. Check `df -h /lfs/$(hostname -s)/0/`.

### Wrong Python env
**Symptom:** Import errors for installed packages.
**Fix:** Check `which python` and ensure the correct venv is activated.

### GPU contention
**Symptom:** OOM or slow training despite "free" GPUs.
**Fix:** `nvidia-smi` — check for zombie processes from other users. Use `CUDA_VISIBLE_DEVICES` to pin to free GPUs.

---

## Tips

- **Use DFS for repos, LFS for speed.** Repos on DFS are accessible from all nodes. Symlink into LFS home for short paths.
- **Use `byobu`** for persistent sessions that survive SSH disconnects. Status bar shows hostname.
- **Prefer `uv`** over conda for new Python environments.
- **Check GPU availability** before starting jobs: `nvidia-smi --query-gpu=index,memory.used,memory.free,utilization.gpu --format=csv,noheader`.
