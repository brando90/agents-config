# Machine: SNAP — Stanford SNAP / Infolab Cluster

Multi-node GPU cluster. Shared DFS/AFS filesystems, per-node LFS local scratch. No job scheduler — direct SSH to nodes. **Shell: bash** (`~/.bashrc`).

Cluster wiki:
- Storage: https://ilwiki.stanford.edu/doku.php?id=hints:storefiles
- Long jobs: https://ilwiki.stanford.edu/doku.php?id=hints:long-jobs
- Server inventory (Jure/SNAP): https://ilwiki.stanford.edu/doku.php?id=snap-servers:snap-servers
- Server inventory (Koyejo): https://ilwiki.stanford.edu/doku.php?id=koyejo-servers:koyejo

---

## Connection

```bash
# Agents: can run one-shot remote commands (e.g., ssh ampere1.stanford.edu "nvidia-smi")
# but cannot maintain interactive sessions. Auth via ~/.ssh/config and ~/keys/.
ssh <user>@<hostname>.stanford.edu
```

- **Access:** Direct SSH from Stanford network or VPN. No jump host.
- **Port:** 22
- **Persistent sessions:** Use `byobu` (tmux-based, human-only — agents cannot interact with tmux). Config is shared across nodes via DFS (`BYOBU_CONFIG_DIR` set in `.bashrc`).
- **Kerberos reauth for persistent sessions:** Kerberos tickets expire (~3 days), breaking AFS access inside detached sessions. Use `/afs/cs/software/bin/krbtmux` (or `krbscreen`) to launch the multiplexer, then run `/afs/cs/software/bin/reauth` inside to keep tickets renewed. See https://ilwiki.stanford.edu/doku.php?id=hints:long-jobs.

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
- `~/.bashrc` is a symlink to `/dfs/scratch0/<user>/.bashrc` — shared across all nodes. Originally seeded from `veribench/experiments/.bashrc` by `snap_setup.sh`.
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
- `/dfs/scratch0/<user>/bin/` — shared binaries on PATH (vibe, etc.). Note: `claude` resolves from NVM and `clauded` from AFS `bin/` — see [Claude Code](#claude-code) below.
- `/dfs/scratch0/<user>/.nvm/` — Node.js via nvm (shared on DFS via `NVM_DIR`)
- `~/.virtualenvs/` — legacy Python venvs under LFS `$HOME` (contains `venv_for_poetry`, activated conditionally by `.bashrc`)
- `~/uv_envs/veribench/` — uv-managed venv for VeriBench (created by `veribench_setup.sh`; activate: `source ~/uv_envs/veribench/bin/activate`)
- `~/.elan/bin/` — Lean 4 toolchain (lean, lake, elan) installed by `veribench_setup.sh`
- `BYOBU_CONFIG_DIR` = `/dfs/scratch0/<user>/.byobu_shared` (shared tmux config)

### Claude Code

- `claude` binary: installed via `npm` under NVM (resolves from `$NVM_DIR/versions/node/…/bin/claude`). A stale copy also exists at `/dfs/scratch0/<user>/bin/claude` but NVM takes precedence on PATH.
- `clauded` script: `/afs/cs.stanford.edu/u/<user>/bin/clauded` (AFS `bin/` is on PATH; runs `claude --dangerously-skip-permissions "$@"`). A duplicate exists at `/dfs/scratch0/<user>/bin/clauded`.
- Auth: `CLAUDE_CODE_OAUTH_TOKEN` set in `.bashrc`

### Vibe (Mistral)

- Binary: `/dfs/scratch0/<user>/bin/vibe` (DFS, shared across nodes)
- Packages: `/dfs/scratch0/<user>/lib/python3.12/site-packages` (needs `PYTHONPATH`)
- API key: `MISTRAL_API_KEY` loaded from `~/keys/mistral_personal_key.txt`
- If missing, reinstall: `python3.12 -m pip install mistral-vibe --prefix /dfs/scratch0/<user>`

### Docker

```bash
cat ~/keys/<ghcr_token_file> | docker login ghcr.io -u <github_username> --password-stdin
```

---

## New Node Setup

When SSH-ing into a new SNAP node for the first time (assumes DFS is already set up with `.bashrc`, repos, etc.):

```bash
# 1. Create LFS home
mkdir -p /lfs/$(hostname -s)/0/<user>

# 2. Symlink .bashrc from AFS → DFS (before HOME is moved)
ln -sf /dfs/scratch0/<user>/.bashrc /afs/cs.stanford.edu/u/<user>/.bashrc

# 3. Source it (sets HOME to LFS, adds DFS/bin to PATH, loads nvm)
source ~/.bashrc

# 4. Also symlink in LFS home (for after HOME is set)
ln -sf /dfs/scratch0/<user>/.bashrc ~/.bashrc

# 5. Symlink agent-config repo and entry points
ln -sfn /dfs/scratch0/<user>/agents-config ~/agent-config
ln -sf ~/agent-config/CLAUDE.md ~/CLAUDE.md
ln -sf ~/agent-config/agents.md ~/agents.md

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

For **first-time-ever cluster setup** (fresh user, no DFS yet), see `~/veribench/snap_setup.sh`. It:
1. Creates DFS/LFS directories and symlinks `.bashrc` (AFS → DFS, LFS → DFS)
2. Clones `veribench` and `agents-config` to DFS, symlinks entry points
3. Calls `~/veribench/veribench_setup.sh` which installs uv, Lean/elan, Mathlib, and Python deps

**Warning:** `snap_setup.sh` unconditionally copies `veribench/experiments/.bashrc` over `$DFS/.bashrc`. If your `.bashrc` has diverged (check with `wc -c`), back it up first or the copy will overwrite your customizations.

---

## Common Issues

### DFS scratch nearly full
**Symptom:** Write failures or slow I/O on `/dfs/scratch0`.
**Fix:** `df -h /dfs/scratch0` — if above 90%, clean up old checkpoints, logs, and unused repos.

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
