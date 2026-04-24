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
- **Kerberos auto-renewal:** Server-side tickets are auto-renewed every 4h by `krenew.sh` (DFS keytab + `.bashrc` background loop + cron). `krbtmux`/`reauth` are no longer needed for ticket renewal. See `~/agents-config/todo_infinite_reauth_kinit_server_side.md` for details. Fallback: `/afs/cs/software/bin/krbtmux` and `/afs/cs/software/bin/reauth` still work if auto-renewal is not set up. Ref: https://ilwiki.stanford.edu/doku.php?id=hints:long-jobs.

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
- **LFS project paths are always symlinks to DFS.** Every project directory under `~/` (LFS) must be a symlink to its canonical location on `/dfs/scratch0/<user>/`. For example, `~/veribench` → `/dfs/scratch0/<user>/veribench`. This ensures all servers see the same repo state and avoids stale or divergent copies. The `snap_setup.sh` and new-node setup scripts create these symlinks automatically.
- **`~/dfs` must be a symlink to `/dfs/scratch0/<user>`.** Required by the DFS job queue watcher (`workflows/remote-job-dispatch.md`) and any tooling that references `~/dfs/...`. Create with `ln -sfn /dfs/scratch0/<user> ~/dfs`. `snap_setup.sh` creates this automatically.
- **Run Docker/Harbor from LFS**, not AFS/DFS. NFS/AFS has root-squash that blocks Docker writes.
- If a `/dfs/` mount is missing, `cd /dfs/scratch0` triggers AutoFS. If still missing, check https://ilwiki.stanford.edu/doku.php?id=hints:storefiles.

---

## Slurm migration & DFS stale handles (2026-04, in progress)

SNAP is in the middle of migrating GPU nodes behind `pam_slurm_adopt`. Status as of **2026-04-24**:

| Node | ssh access | DFS mount | Watcher viable? |
|------|------------|-----------|-----------------|
| `mercury1`, `mercury2` | open (CS) | OK | ✅ |
| `skampere1`, `skampere2`, `skampere3` | open (CS) | OK | ✅ |
| `hyperturing1` | open (CS) | OK (after symlink fix) | ✅ |
| `rambo` (ICL compute) | open (CS) | OK | ✅ (CPU-only, needs `lark`) |
| `hyperturing2` | **Slurm-gated** | n/a | ❌ without `sbatch` |
| `turing3` | **Slurm-gated** | n/a | ❌ without `sbatch` |
| `ampere1`–`ampere9` | Slurm-gated (varies, `ampere8` sometimes open) | n/a | ❌ without `sbatch` |
| `blackwell1` | **Slurm-gated** + unreachable | n/a | ❌ |
| `turing1`, `turing2` | open | **`/dfs/scratch0/...` Stale file handle** | ❌ node-level fix needed |
| `trinity`, `furiosa`, `madmax2–6`, `hyperion3` | open | OK | ❌ Ubuntu 16 / Python 3.5 — too old for uutils (f-strings) |
| `madmax1`, `madmax5`, `rambino` | unreachable | — | ❌ |

**Symptoms to recognize:**
- `Access denied by pam_slurm_adopt: you have no active jobs on this node` → the node has been migrated; you need `sbatch`/`srun` to get in.
- `Stale file handle` on `/dfs/scratch0/...` → the DFS mount is broken on that node; reboot or file a ticket (user cannot fix).
- Watcher tmux session silently exits right after launch → usually the module import raises (e.g. missing `dill`, `pandas`, `lark`, or Python too old for f-strings). Use `bash -c '... 2>&1 | tee log'` inside the tmux session so the traceback survives.

**Playbook when adding a new watcher:**
1. ssh probes: `ssh <host>.stanford.edu "hostname && ls /dfs/scratch0/brando9 >/dev/null && echo DFS-OK"`. Abort if either fails.
2. Use `/dfs/scratch0/brando9/bin/launch_watcher_remote.sh` — it auto-detects python, bootstraps missing deps, pins `--job-dir /dfs/scratch0/brando9/job_queue`, and wraps in `tmux new-session -d … bash -c '…'` so import errors land in `logs/watcher_daemon_<host>.log` instead of vanishing.
3. Verify the heartbeat appears in `/dfs/scratch0/brando9/job_queue/watchers/<host>.stanford.edu.heartbeat` within ~20s.

**If you need a Slurm-gated node:** you must submit the watcher as a Slurm job (`sbatch --time=48:00:00 --wrap='…launch_watcher_remote.sh…'`). The existing workflow does not do this automatically — plan a `scripts/sbatch-watcher.sh` wrapper if this becomes the common case.

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
| `skampere1` | 8x A100-SXM4-80GB | ~2 TiB |
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
- Auth: `~/.claude/` is symlinked to `/dfs/scratch0/<user>/.claude` — shared auth across all SNAP nodes. Run `claude auth login` once on any server, all nodes pick it up.

### npm globals — "update loop" gotcha

If a globally-installed npm tool (`codex`, `claude`, `gemini`, etc.) keeps nagging "please restart / update again" *after* you run `npm install -g <pkg>`, it's almost always **two installs in different PATH positions** — npm writes to one prefix but the shell resolves a stale copy earlier in PATH.

Diagnose:
```bash
which -a <tool>                      # multiple hits = shadowed install
npm config get prefix                # where `npm install -g` writes
dirname "$(command -v <tool>)"       # what the shell actually runs
# the two above MUST match; if not, the earlier-in-PATH copy is stale.
```

Fix: delete the stale bin + lib (common culprits: `~/.local/bin/<tool>` + `~/.local/lib/node_modules/<@scope>/<pkg>`, or a root-owned `/usr/local/bin/<tool>` from a past system install).

Prevent: **never prepend a hardcoded Node version to PATH in `.bashrc`** — e.g. `export PATH=".../.nvm/versions/node/v24.14.0/bin:$PATH"`. `nvm.sh` (sourced in `.bashrc`) already prepends the active-node bin, and hardcoding will silently shadow a newer node after `nvm install`, resurrecting this bug on every node upgrade.

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
ln -sfn /dfs/scratch0/<user>/agents-config ~/agents-config
ln -sf ~/agents-config/CLAUDE.md ~/CLAUDE.md
ln -sf ~/agents-config/agents.md ~/agents.md

# 5b. Symlink entire ~/.claude dir to DFS (shared auth + settings across all nodes)
# Run 'claude auth login' once on any node — all nodes share the credential.
rm -rf ~/.claude 2>/dev/null
ln -sfn /dfs/scratch0/<user>/.claude ~/.claude

# 5c. Symlink ~/dfs → DFS root (required by dfs-job-watcher and any ~/dfs/... path)
ln -sfn /dfs/scratch0/<user> ~/dfs

# 6. Create DFS project symlinks in LFS home (idempotent — re-run whenever a new DFS repo is added)
bash ~/agents-config/scripts/relink-dfs-projects.sh

# 7. Verify
which claude && which clauded
```

### Adding a new DFS repo later

The step-6 script is idempotent. After cloning or migrating a new repo into `/dfs/scratch0/<user>/`, re-run it on every node where you want the `~/<newrepo>` shortcut:

```bash
bash ~/agents-config/scripts/relink-dfs-projects.sh
```

Without this step, `~/<newrepo>` silently doesn't exist on that node, which breaks any tooling that assumes `~/<newrepo>/...` paths (this is what happened to `~/veribench-dt` between 2026-04-10 and 2026-04-20). The migration checklist in [`workflows/repo-init.md`](../workflows/repo-init.md) includes this as a required step.

For **first-time-ever cluster setup** (fresh user, no DFS yet), see `~/veribench/snap_setup.sh`. It:
1. Creates DFS/LFS directories and symlinks `.bashrc` (AFS → DFS, LFS → DFS)
2. Clones `veribench` and `agents-config` to DFS, symlinks entry points
3. Symlinks `~/keys` → DFS keys dir, and all DFS projects into LFS home
4. Calls `~/veribench/veribench_setup.sh` which installs uv, Lean/elan, Mathlib, and Python deps

**Warning:** `snap_setup.sh` unconditionally copies `veribench/experiments/.bashrc` over `$DFS/.bashrc`. If your `.bashrc` has diverged (check with `wc -c`), back it up first or the copy will overwrite your customizations.

---

## Common Issues

### Codex sandbox fails (bwrap)
**Symptom:** `codex exec --full-auto` errors with `bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`.
**Cause:** SNAP nodes block unprivileged user network namespaces, which bubblewrap requires.
**Fix:** Set `use_legacy_landlock = true` under `[features]` in `~/.codex/config.toml`. Landlock works on kernel 5.13+ without user namespaces. Also add `[shell_environment_policy]` / `inherit = "all"` so Codex inherits API keys.

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
