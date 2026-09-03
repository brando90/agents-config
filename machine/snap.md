# Machine: SNAP — Stanford SNAP / Infolab Cluster

Multi-node GPU cluster. Shared DFS/AFS filesystems, per-node LFS local scratch. Older nodes use direct SSH; migrated nodes use Slurm through `ilc.stanford.edu`. **Shell: bash** (`~/.bashrc`).

Cluster wiki:
- Storage: https://ilwiki.stanford.edu/doku.php?id=hints:storefiles
- Long jobs: https://ilwiki.stanford.edu/doku.php?id=hints:long-jobs
- Server inventory (Jure/SNAP): https://ilwiki.stanford.edu/doku.php?id=snap-servers:snap-servers
- Server inventory (Koyejo): https://ilwiki.stanford.edu/doku.php?id=koyejo-servers:koyejo

---

## Connection

```bash
# Agents: can run one-shot commands on a direct-SSH node (e.g., ssh skampere2.stanford.edu "nvidia-smi")
# but cannot maintain interactive sessions. Auth via ~/.ssh/config and ~/keys/.
ssh <user>@<hostname>.stanford.edu
```

- **Access:** Direct SSH from Stanford network or VPN. No jump host.
- **Port:** 22
- **Persistent sessions:** Use `byobu` (tmux-based, human-only — agents cannot interact with tmux). Config is shared across nodes via DFS (`BYOBU_CONFIG_DIR` set in `.bashrc`).
- **Kerberos auto-renewal:** Server-side tickets are auto-renewed every 4h by `krenew.sh` (DFS keytab + `.bashrc` background loop + cron). `krbtmux`/`reauth` are no longer needed for ticket renewal. See `~/agents-config/todo_infinite_reauth_kinit_server_side.md` for details. Fallback: `/afs/cs/software/bin/krbtmux` and `/afs/cs/software/bin/reauth` still work if auto-renewal is not set up. Ref: https://ilwiki.stanford.edu/doku.php?id=hints:long-jobs.

---

## Cluster health

Run this **before dispatching any SNAP agent job**:

```bash
bash ~/agents-config/scripts/snap_health.sh
```

It audits the five direct-SSH nodes, probes the Slurm-gated nodes, inventories every command hit,
checks local and shared disk headroom, authentication, required links, and every top-level DFS Git
clone. It exits nonzero for actionable failures. Useful modes are `--fix` (conservative user-owned
repairs only), `--node <host>`, `--json`, and `--smoke`. Never add `--smoke` to routine dispatch: it
makes paid/subscription-backed one-line model calls.

### Canonical command-line tool policy

- `claude`, `codex`, and `node` have one canonical install under the dynamically selected
  `/dfs/scratch0/brando9/.nvm/versions/node/<current>/`; `nvm use default` chooses `<current>`.
  Never hardcode that version in `PATH`.
- Shared wrappers (`clauded`, `claude-vals`, `clauded-vals`, `valkyrie`) are canonical in
  `/dfs/scratch0/brando9/bin`. AFS copies are compatibility mirrors, not update targets.
- `uv` and the actual Harbor environment are per-node under LFS (`~/.local`). The shared
  `/dfs/scratch0/brando9/bin/harbor` wrapper executes the node-local Harbor with `PYTHONPATH`
  removed; the global Mistral package path otherwise contaminates Harbor's isolated environment.
- `/dfs/scratch0/brando9/.bash_env` selects NVM dynamically and puts the NVM and DFS bins first.
  The marked block in `/dfs/scratch0/brando9/.bashrc` exports `BASH_ENV`, covering login shells,
  `ssh host 'cmd'`, and inherited `bash -c` shells. Cron and service definitions must explicitly set
  `BASH_ENV=/dfs/scratch0/brando9/.bash_env` because they do not inherit a login environment.
- Each node's `~/.bash_profile` points to `/dfs/scratch0/brando9/.bash_profile`, which sources the
  shared `.bashrc`; without it, an explicit `bash -l` falls back to the node-local `.profile` and
  misses the canonical command policy.
- Root-owned `/usr/local/bin/claude` and `/usr/local/bin/codex` are stale unsupported copies. User
  shell resolution avoids them; only an administrator can remove them.
- `~/agents-config/scripts/auto-update-tools.sh` updates both Node-based agents in the selected NVM
  prefix, uses a shared lock and six-hour success stamp, and records failures in
  `/dfs/scratch0/brando9/.cache/agent-cli-update.log` instead of swallowing them.

### LFS headroom and Harbor

Harbor job directories **must live on LFS**, never AFS or DFS. `snap_health.sh` warns below 10% free
and fails below 5% free. Before a run, treat a disk failure as a scheduling failure: inspect with
`du -x -h --max-depth=1 /lfs/<host>/0/brando9 | sort -h | tail -20`, then remove only reviewed,
finished, regenerable data. Package caches are safe only when no installer is active. Delete an old
Harbor job directory only after its run is finished and its result artifacts are committed; never
remove a directory merely because its name looks old.

### Slurm-gated nodes

The Slurm client is on `ilc.stanford.edu`, not on the direct-SSH `skampere*` or `mercury*` nodes.
First verify that `showaccount` lists the `infolab` account. Then run work directly under `srun`:

```bash
ssh -t ilc.stanford.edu
showaccount
srun --partition=il --qos=il-interactive --account=infolab \
  --nodelist=ampere1 --gres=gpu:1 --time=00:10:00 --pty bash -l
```

For a CPU-only health/setup shell, use `--partition=il-cpu`, omit `--gres`, and request one task and
one CPU. Once an allocation is running, direct SSH to its node is accepted by `pam_slurm_adopt`, or
the job can remain under `srun`. If `showaccount` is empty, request the `infolab` Slurm association
from `il-action@cs.stanford.edu`; no local command can grant it. Current syntax and limits are at
https://ilops.stanford.edu/wiki/doku.php?id=hints%3Aslurm.

### One dedicated clone per agent job

Never run two agents from one working tree. Make one dedicated DFS clone per job, fetch the exact
remote-tracking ref, and start from it. Leave shared dirty clones untouched:

```bash
git clone https://github.com/brando90/veribench.git /dfs/scratch0/brando9/<job>/veribench
git -C /dfs/scratch0/brando9/<job>/veribench \
  fetch origin '+refs/heads/main:refs/remotes/origin/main'
git -C /dfs/scratch0/brando9/<job>/veribench switch -c <job> origin/main
```

A bare `git fetch origin main` updates only `FETCH_HEAD` in these clones; it does **not** reliably
refresh `refs/remotes/origin/main`. Use the explicit refspec above before any checkout based on the
remote-tracking branch.

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
- `~/.bash_profile` is a symlink to `/dfs/scratch0/<user>/.bash_profile` — makes explicit Bash login shells source that shared `.bashrc`.
- **Clone repos to DFS** (`/dfs/scratch0/<user>/`), then symlink from LFS home. Never clone directly to LFS — it's node-local and not backed up.
- **LFS project paths are always symlinks to DFS.** Every project directory under `~/` (LFS) must be a symlink to its canonical location on `/dfs/scratch0/<user>/`. For example, `~/veribench` → `/dfs/scratch0/<user>/veribench`. This ensures all servers see the same repo state and avoids stale or divergent copies. The `snap_setup.sh` and new-node setup scripts create these symlinks automatically.
- **`~/dfs` must be a symlink to `/dfs/scratch0/<user>`.** Required by the DFS job queue watcher (`workflows/remote-job-dispatch.md`) and any tooling that references `~/dfs/...`. Create with `ln -sfn /dfs/scratch0/<user> ~/dfs`. `snap_setup.sh` creates this automatically.
- **Run Docker/Harbor from LFS**, not AFS/DFS. NFS/AFS has root-squash that blocks Docker writes.
- If a `/dfs/` mount is missing, `cd /dfs/scratch0` triggers AutoFS. If still missing, check https://ilwiki.stanford.edu/doku.php?id=hints:storefiles.

---

## Local ↔ DFS sync (Mac → SNAP)

**Default after agent edits: backgrounded `rsync` to DFS + best-effort `git push`.** DFS is shared across every SNAP node, so one rsync into any node propagates everywhere. Both jobs are detached (`&`) so they never block the next agent turn, and both swallow failures — `rsync` is the operational sync (must succeed eventually but doesn't block now); `git push` is a cheap durability backstop (skip silently if it fails).

```bash
SNAP_HOST=skampere1.stanford.edu       # any open SNAP node — DFS handles fan-out
REPO="${CLAUDE_PROJECT_DIR:-$PWD}"     # repo root; CLAUDE_PROJECT_DIR is set in hooks
NAME=$(basename "$REPO")

# 1) Backgrounded rsync to DFS (cluster-wide visibility, fire-and-forget)
( rsync -av --update \
    --exclude='.git/' --exclude='__pycache__/' --exclude='*.pyc' \
    --exclude='.venv/' --exclude='node_modules/' --exclude='.pytest_cache/' \
    --exclude='wandb/' --exclude='outputs/' --exclude='checkpoints/' \
    --exclude='.DS_Store' \
    "$REPO/" "brando9@${SNAP_HOST}:/dfs/scratch0/brando9/${NAME}/" \
    > "/tmp/snap-sync-${NAME}.log" 2>&1 ) &

# 2) Best-effort git push (durability backstop; silent on failure)
( cd "$REPO" && git push 2>/dev/null ) &

# Both processes detach. Do NOT `wait` — they self-terminate when done.
```

- `--update` skips files where the destination is newer → protects work edited directly on the cluster.
- **Never use `--delete` or `git push --force`** in automated sync — either can nuke concurrent edits.
- `git push` here pushes the current branch to its tracking remote. If push fails (no upstream, conflicts, branch protection, hooks), the rsync already landed the bytes — don't retry, don't error, don't escalate.
- **Multiple repos in one turn run in parallel** — emit one backgrounded `rsync`+`git push` pair per edited repo and let them race to completion independently.
- **Wire as a `Stop` hook in `~/.claude/settings.json`** so this fires automatically after every agent turn that touched a DFS-mirrored repo. The hook returns instantly because both jobs are backgrounded; `tail /tmp/snap-sync-*.log` if you ever want to audit. (Trigger Rule 6 still governs deliberate `agents-config` commits — that path is unaffected.)
- ⚠ **Secrets ⨉ auto-push.** The auto-`git push` only ships *already-committed* work, so Hard Rule 1's commit-time scan is the real safety net here. If a secret ever slips into a commit, the Stop hook will leak it within seconds — there is no buffer to amend. Treat anything that auto-pushed as already public; rotate the credential rather than trying to scrub history. Run a project-level `gitleaks`/`pre-commit` hook for defense-in-depth.

---

## Slurm migration and node access (audited 2026-09-03)

SNAP GPU nodes have moved behind `pam_slurm_adopt`. The live Slurm inventory on
`ilc.stanford.edu` showed every gated target below; none of the requested audit targets is known to
be permanently gone. Filesystem state on a gated node can be tested only from inside an allocation.

| Node | ssh access | DFS mount | Watcher viable? |
|------|------------|-----------|-----------------|
| `mercury1`, `mercury2` | open (CS) | OK | ✅ |
| `skampere1`, `skampere2`, `skampere3` | open (CS) | OK | ✅ |
| `rambo` (ICL compute) | open (CS) | OK | ✅ (CPU-only, needs `lark`) |
| `hyperturing1`, `hyperturing2` | **Slurm-gated; present** | test in allocation | via `srun`/`sbatch` |
| `ampere1`–`ampere9` | **Slurm-gated; present** | test in allocation | via `srun`/`sbatch` |
| `turing1`–`turing3` | **Slurm-gated; present** | test in allocation | via `srun`/`sbatch` |
| `blackwell1` | **Slurm-gated; present** | test in allocation | via `srun`/`sbatch` |
| `trinity`, `furiosa`, `madmax2–6`, `hyperion3` | open | OK | ❌ Ubuntu 16 / Python 3.5 — too old for uutils (f-strings) |
| `madmax1`, `madmax5`, `rambino` | unreachable | — | ❌ |

**Symptoms to recognize:**
- `Access denied by pam_slurm_adopt: you have no active jobs on this node` → the node has been migrated; you need `sbatch`/`srun` to get in.
- `Stale file handle` on `/dfs/scratch0/...` from inside an allocation → the DFS mount is broken on that node; file a ticket (a user cannot fix it).
- Watcher tmux session silently exits right after launch → usually the module import raises (e.g. missing `dill`, `pandas`, `lark`, or Python too old for f-strings). Use `bash -c '... 2>&1 | tee log'` inside the tmux session so the traceback survives.

**Playbook when adding a new watcher:**
1. For direct-SSH nodes, probe with `ssh <host>.stanford.edu "hostname && ls /dfs/scratch0/brando9 >/dev/null && echo DFS-OK"`. For gated nodes, obtain an allocation through `ilc.stanford.edu` first. Abort if either check fails.
2. Use `/dfs/scratch0/brando9/bin/launch_watcher_remote.sh` — it auto-detects python, bootstraps missing deps, pins `--job-dir /dfs/scratch0/brando9/job_queue`, and wraps in `tmux new-session -d … bash -c '…'` so import errors land in `logs/watcher_daemon_<host>.log` instead of vanishing.
3. Verify the heartbeat appears in `/dfs/scratch0/brando9/job_queue/watchers/<host>.stanford.edu.heartbeat` within ~20s.
4. Install both cron entries so the watcher survives ticket expiry **and** node reboot:
   ```
   ssh <host> "(crontab -l 2>/dev/null | grep -vE 'krenew|start_watcher_at_reboot'; \
                printf '0 */4 * * * /dfs/scratch0/brando9/bin/krenew.sh\n@reboot /dfs/scratch0/brando9/bin/start_watcher_at_reboot.sh\n') | crontab -"
   ```
   The first refreshes Kerberos+AFS via the DFS keytab (no password prompt — see "How keytab reauth works" below). The second waits for DFS to come up after boot, runs `krenew.sh`, then re-launches the watcher in tmux. Boot wrapper logs to `/tmp/start_watcher_at_reboot_<host>.log`.

**How keytab reauth works (and why no password is ever entered after one-time setup):**
- The "secret" is `/dfs/scratch0/brando9/.keytab` — a 83-byte file derived once from your Stanford password via `ktutil` (see [`../init_no_passwords_snap_kinit.md`](../init_no_passwords_snap_kinit.md) Part A). It is chmod 600, on shared DFS, so every node and every cron job can read it.
- `krenew.sh` runs `kinit -kt $KEYTAB brando9@CS.STANFORD.EDU && aklog`. The keytab acts as proof-of-password to the KDC. **No interactive prompt, no env var, no agent ever has to type or store the password itself.**
- If you change your Stanford password, regenerate the keytab — until you do, all 7 watchers' auth will start failing within ~10h.

**If you need a Slurm-gated node:** first ensure `showaccount` lists `infolab`, then submit the
watcher through `ilc.stanford.edu` as a Slurm job. See [Slurm-gated nodes](#slurm-gated-nodes) for
the tested interactive form. The existing workflow does not do this automatically.

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
- **OS:** Ubuntu 24.04 on `skampere1`–`skampere3`; Ubuntu 20.04 on `mercury1`–`mercury2` as audited 2026-09-03. Always verify at runtime.
- **System Python:** `/usr/bin/python3` (version varies per node — check `python3 --version`)

---

## Environment Setup

Read `~/.bashrc` directly — it is the source of truth for paths, env vars, and tool setup. Do not duplicate secrets here.

Key paths and vars set in `.bashrc`:
- `$HOME` = `/lfs/<hostname>/0/<user>` (LFS, set dynamically per server)
- `$AFS` = `/afs/cs.stanford.edu/u/<user>`
- `$DFS` = `/dfs/scratch0/<user>`
- `~/keys/` — API keys and tokens (loaded by `.bashrc`, never committed)
- `/dfs/scratch0/<user>/bin/` — canonical shared wrappers on PATH (`clauded`, Vals wrappers, Valkyrie, Harbor, vibe, etc.); `claude`, `codex`, and `node` resolve from NVM. See [Claude Code](#claude-code) below.
- `/dfs/scratch0/<user>/.nvm/` — Node.js via nvm (shared on DFS via `NVM_DIR`)
- `~/.virtualenvs/` — legacy Python venvs under LFS `$HOME` (contains `venv_for_poetry`, activated conditionally by `.bashrc`)
- `~/uv_envs/veribench/` — uv-managed venv for VeriBench (created by `veribench_setup.sh`; activate: `source ~/uv_envs/veribench/bin/activate`)
- `~/.elan/bin/` — Lean 4 toolchain (lean, lake, elan) installed by `veribench_setup.sh`
- `BYOBU_CONFIG_DIR` = `/dfs/scratch0/<user>/.byobu_shared` (shared tmux config)

### Claude Code

- `claude` binary: installed via `npm` under NVM (resolves from `$NVM_DIR/versions/node/…/bin/claude`). The old user-owned DFS-prefix duplicate was removed; the stale root-owned `/usr/local/bin/claude` remains visible later in `which -a` but must never resolve first.
- `clauded` script: canonical at `/dfs/scratch0/<user>/bin/clauded` (runs `claude --dangerously-skip-permissions "$@"`). The AFS script is a compatibility mirror and resolves second.
- Auth: `~/.claude/` is symlinked to `/dfs/scratch0/<user>/.claude` — shared auth across all SNAP nodes. Run `claude auth login` once on any server, all nodes pick it up.

#### Vals AI profile — `claude-vals` / `clauded-vals`

A second Claude Code login (the Vals AI team account, `brando@vals.ai`) kept fully separate from the
personal one, mirroring the mac's `claude-vals` / `clauded-vals` shell functions.

- `claude-vals` = `claude` with `CLAUDE_CONFIG_DIR=~/.claude-vals`; `clauded-vals` = same plus
  `--dangerously-skip-permissions` (the Vals-profile equivalent of `clauded`).
- Both are scripts installed canonically in `/dfs/scratch0/<user>/bin`, with `$AFS/bin` compatibility
  mirrors later in `PATH`, the same pattern as `clauded`. They `unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN
  CLAUDE_CODE_OAUTH_TOKEN CLAUDE_CODE_USE_BEDROCK CLAUDE_CODE_USE_VERTEX` first — `CLAUDE_CODE_OAUTH_TOKEN`
  is the *personal* token and would silently hijack the Vals profile — and resolve `claude` out of the
  DFS nvm install *first* (newest by mtime) rather than trusting PATH, so they work identically under
  `ssh host 'cmd'`, cron, and tmux `send-keys`. That ordering is deliberate: every node also carries an
  old root-owned `/usr/local/bin/claude` (2.1.75) that wins in a minimal PATH and, on mercury, crashes
  against the system node — see the "npm globals" gotcha below.
- Config + credentials live once on DFS at `/dfs/scratch0/<user>/.claude-vals`, symlinked into each
  node's `$HOME/.claude-vals`. Profile-level `settings.json` (`opus[1m]`, xhigh effort),
  `CLAUDE.md`, and the profile's auto-memories are seeded from the mac.
- Install / repair on a node: `bash ~/agents-config/scripts/setup_claude_vals_snap.sh`.
- Credentials come **from the mac** (Keychain service `Claude Code-credentials-<sha256(config dir)[:8]>`),
  pushed with `bash ~/agents-config/scripts/push_claude_vals_creds.sh` — which also runs the installer
  on each node and smoke-tests `clauded-vals -p`. Never run an interactive `/login` on a node for this.
- **Rotation caveat:** OAuth refresh tokens rotate on use, so the mac and the cluster sharing one
  credential set can invalidate each other ("refresh token was already used"). Use one machine at a
  time for the Vals profile, and re-run `push_claude_vals_creds.sh` if a node reports being logged out.

### Valkyrie (Vals evaluation platform CLI)

- `valkyrie` / `valk` (same tool, two names) installed via `uv tool install git+https://github.com/vals-ai/Valkyrie@prod`
  into DFS: venv at `/dfs/scratch0/<user>/uv/tools/valkyrie`, shims in `/dfs/scratch0/<user>/bin`
  (+ AFS `bin/` mirrors), so every node runs one shared install.
- The tool venv **must** use a uv-managed interpreter under `/dfs/scratch0/<user>/uv/python`
  (`UV_PYTHON_PREFERENCE=only-managed`): skampere nodes have `/usr/bin/python3.12`, but mercury nodes
  only ship python 3.8, so a system-pinned venv is broken there.
- Config: `~/.config/valkyrie/valkyrie.yaml` (override path with `VALKYRIE_CONFIG_PATH`), symlinked
  from each node to `/dfs/scratch0/<user>/.config/valkyrie` so credentials are entered once.
  Create it with `export VALKYRIE_API_KEY=<vals key> && valkyrie config init` — the key is read from
  `VALKYRIE_API_KEY` if set, otherwise prompted for, and is *not* stored in `~/keys` by any script.
- Repos cloned to DFS alongside it: `Valkyrie/`, `vals-public-agent-registry/`,
  `vals-create-benchmark-service/`.
- The shared wrapper dynamically selects `/dfs/scratch0/brando9/uv/tools/valkyrie` on glibc 2.34+
  and `/dfs/scratch0/brando9/uv/tools-glibc2.31/valkyrie` on the Ubuntu 20.04 Mercury nodes. It also
  removes the shared `PYTHONPATH`; bypassing the wrapper can still produce glibc or OpenTelemetry
  import failures. `snap_health.sh` runs a bounded `--help` startup check, not metadata alone. First
  start is slow (~1-5 min cold, ~5 s warm) because the imports come off DFS.
- `valkyrie` has **no `--version` flag**; `valkyrie --help` is the smoke test.
- Install / repair on a node: `bash ~/agents-config/scripts/setup_valkyrie_snap.sh`.
- VeriBench-specific state (agents, benchmark service, gateway secret) lives in
  `~/veribench/experiments/71_vals_ai_eval_code/docs/04_valkyrie_setup.md`.

### npm globals — "update loop" gotcha

If a globally-installed npm tool (`codex`, `claude`, etc.) keeps nagging "please restart / update again" *after* you run `npm install -g <pkg>`, it's almost always **two installs in different PATH positions** — npm writes to one prefix but the shell resolves a stale copy earlier in PATH.

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
mkdir -p ~/.codex
ln -sf ~/agents-config/AGENTS.md ~/.codex/AGENTS.md
ln -sf ~/agents-config/AGENTS.md ~/AGENTS.md       # optional compatibility
ln -sf ~/agents-config/AGENTS.md ~/agents.md       # legacy home-level compatibility

# 5b. Symlink entire ~/.claude dir to DFS (shared auth + settings across all nodes)
# Run 'claude auth login' once on any node — all nodes share the credential.
rm -rf ~/.claude 2>/dev/null
ln -sfn /dfs/scratch0/<user>/.claude ~/.claude

# 5c. Symlink ~/dfs → DFS root (required by dfs-job-watcher and any ~/dfs/... path)
ln -sfn /dfs/scratch0/<user> ~/dfs

# 5d. Vals AI Claude Code profile + Valkyrie CLI (idempotent; see the two sections above)
bash ~/agents-config/scripts/setup_claude_vals_snap.sh
bash ~/agents-config/scripts/setup_valkyrie_snap.sh
# Credentials for the Vals profile are pushed FROM THE MAC (not logged into here):
#   bash ~/agents-config/scripts/push_claude_vals_creds.sh <newhost>

# 6. Create DFS project symlinks in LFS home (idempotent — re-run whenever a new DFS repo is added)
bash ~/agents-config/scripts/relink-dfs-projects.sh

# 7. Verify
which claude && which clauded && which clauded-vals && which valkyrie
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
