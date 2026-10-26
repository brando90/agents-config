# Machine: Sherlock — Stanford Research Computing HPC Cluster

**Doc link:** <https://github.com/brando90/agents-config/blob/main/machine/sherlock.md>

**TLDR:** Stanford's shared Slurm cluster, run by Stanford Research Computing (SRCC): Duo login reused through one SSH ControlMaster socket, every computation through Slurm, `$SCRATCH` purged after 90 days, no Anaconda, sponsored research only. For unattended agent commands and the distinction between fresh Duo login and existing authenticated access, start with [reusable agent access](sherlock-agent-access.md); for Slurm mail follow [Trigger Rule 82](../rules/hosts.md#trigger-rule-82).

Load-balanced login nodes, Slurm for all compute, Lustre (parallel filesystem) `$SCRATCH`, NFS (Network File System) `$HOME`/`$GROUP_HOME`. Account: `brando9`, PI (principal investigator) group: Sanmi Koyejo. Account created 10-15-2026. **Shell: bash** (`~/.bashrc`).

Official docs (every fact below cites one of these; facts checked 10-15-2026):
- Connecting: https://www.sherlock.stanford.edu/docs/getting-started/connecting/
- Advanced connection options (ControlMaster, GSSAPI): https://www.sherlock.stanford.edu/docs/advanced-topics/connection/
- Running jobs, partitions, limits: https://www.sherlock.stanford.edu/docs/user-guide/running-jobs/
- GPUs: https://www.sherlock.stanford.edu/docs/user-guide/gpu/
- Node features: https://www.sherlock.stanford.edu/docs/advanced-topics/node-features/
- Storage, quotas: https://www.sherlock.stanford.edu/docs/storage/ and https://www.sherlock.stanford.edu/docs/storage/filesystems/
- Data transfer: https://www.sherlock.stanford.edu/docs/storage/data-transfer/
- Python, uv, venv: https://www.sherlock.stanford.edu/docs/software/using/python/
- Anaconda (avoid): https://www.sherlock.stanford.edu/docs/software/using/anaconda/
- Modules (Lmod): https://www.sherlock.stanford.edu/docs/software/modules/
- OnDemand (browser access): https://www.sherlock.stanford.edu/docs/user-guide/ondemand/
- Troubleshooting / how to report issues: https://www.sherlock.stanford.edu/docs/user-guide/troubleshoot/
- System status and news: https://status.sherlock.stanford.edu and https://news.sherlock.stanford.edu

**Status (10-18-2026):** Verified live on the cluster via OpenSSH multiplexing (`login.sherlock.stanford.edu`). Account `brando9`, primary group `sanmi` (`/home/groups/sanmi`). Quotas, partitions, interactive CPU/GPU Slurm execution on `dev`, batch CPU/GPU jobs on `normal`/`gpu`, and Python 3.12.1 venvs verified live (see [Live Verification](#live-verification-results-10-18-2026)). Preflight script: `bash ~/agents-config/scripts/sherlock_preflight.sh` (add `--jobs` to submit a 5-minute CPU and a 10-minute GPU test job; it polls `sacct` once a minute).

---

## Hard rules for agents (read first)

1. **Never compute on a login node.** Login nodes are shared, and processes that exceed their CPU time, memory or run-time limits are killed automatically ([running-jobs](https://www.sherlock.stanford.edu/docs/user-guide/running-jobs/)). Login nodes are for editing, `git`, `sbatch`, `squeue`, small file copies and low-CPU agent orchestration (see [Dispatcher & Multi-Job Etiquette](#dispatcher--multi-job-etiquette)). Everything else goes through Slurm (`sbatch`, `srun`, `salloc`, `sh_dev`).
2. **Never type, store or echo Brando's password, and never trigger Duo yourself.** Password + Duo are Brando's. If there is no live ControlMaster socket, stop and ask him to run `ssh sherlock` once (other routes: [reusable agent access](sherlock-agent-access.md)).
3. **Never retry a failing login in a loop.** Sherlock bans IP addresses that produce too many authentication failures in a short span; the symptom is `Connection refused` or a timeout on port 22 ([connecting](https://www.sherlock.stanford.edu/docs/getting-started/connecting/)). One failure: stop and report the exact error.
4. **Never "refresh" files on `$SCRATCH`/`$GROUP_SCRATCH`.** Files whose contents were not modified for 90 days are purged. Any script or job that rewrites, copies over or `touch`es files to dodge the purge gets the account **suspended on the first occurrence, without warning** ([filesystems](https://www.sherlock.stanford.edu/docs/storage/filesystems/)). Results that must survive go to `$GROUP_HOME`, `$OAK` (if the group has it) or back to the laptop/git.
5. **No Anaconda.** SRCC recommends against it on Sherlock (fills `$HOME`, edits `.bashrc`, duplicates modules) ([anaconda](https://www.sherlock.stanford.edu/docs/software/using/anaconda/)). Use `ml python` + `uv` or `venv`.
6. **Persistent services go to the `service` partition**, not a tmux session on a login node ([running-jobs](https://www.sherlock.stanford.edu/docs/user-guide/running-jobs/)). The live `/etc/agents/AGENTS.md` (read 10-23-2026) forbids servers and processes that outlive an interactive session on login nodes; read it on each session.
7. **No high-risk data.** Sherlock is *not* approved for HIPAA (Health Insurance Portability and Accountability Act) data, PHI (protected health information), PII (personally identifiable information) or any other High Risk data; the user is responsible for compliance (SRCC welcome email, 10-15-2026; [Stanford HIPAA FAQ](https://privacy.stanford.edu/faqs/hipaa-faqs)). Public benchmarks, model weights, code and synthetic data are fine.
8. **Never share credentials.** The cluster falls under Stanford's Computer and Network Usage Policy, which strictly prohibits sharing authentication credentials ([Administrative Guide 6.2.1, Computer and Network Usage Policy](https://adminguide.stanford.edu/chapters/computing/computer-and-network-usage/computer-and-network-usage-policy); SRCC welcome email). Agents only *reuse Brando's live SSH socket on his own computer*; they never copy keys, tickets or passwords to other machines or people.
9. **Sponsored research only.** Sherlock supports sponsored research, not course work, class assignments or general training sessions (SRCC welcome email). Unsponsored or coursework runs go to [FarmShare](farmshare.md).

---

## Connection

```bash
ssh sherlock            # alias defined below; first connection = password + Duo (Brando)
```

- **Hostname:** `login.sherlock.stanford.edu` (DNS alias over the load-balanced login nodes; you land on the least-loaded one) ([connection](https://www.sherlock.stanford.edu/docs/advanced-topics/connection/)).
- **Data Transfer Node (DTN):** `dtn.sherlock.stanford.edu`, for large transfers ([data-transfer](https://www.sherlock.stanford.edu/docs/storage/data-transfer/)).
- **Auth:** SUNet password (checked by Stanford's central Kerberos; never stored on Sherlock) + Duo two-factor ([connection](https://www.sherlock.stanford.edu/docs/advanced-topics/connection/)).
- **Network:** reachable from anywhere, no VPN needed; SRCC does not restrict inbound SSH by IP ([connection](https://www.sherlock.stanford.edu/docs/advanced-topics/connection/)).
- **Browser alternative:** https://ondemand.sherlock.stanford.edu (shell, files, Jupyter) ([ondemand](https://www.sherlock.stanford.edu/docs/user-guide/ondemand/)).

### One Duo per session: `~/.ssh/config` (on each laptop/desktop)

SRCC documents OpenSSH multiplexing (`ControlMaster`) to avoid a Duo prompt on every new connection ([connection](https://www.sherlock.stanford.edu/docs/advanced-topics/connection/)). `ControlPersist` keeps the master socket alive after the first shell closes, so agents can reuse it:

```sshconfig
Host sherlock login.sherlock.stanford.edu
    HostName login.sherlock.stanford.edu
    User brando9
    ControlMaster auto
    ControlPath ~/.ssh/%C
    ControlPersist 12h
    ServerAliveInterval 60

Host sherlock-dtn dtn.sherlock.stanford.edu
    HostName dtn.sherlock.stanford.edu
    User brando9
    ControlMaster auto
    ControlPath ~/.ssh/%C
    ControlPersist 12h
```

- `ControlPath ~/.ssh/%C` is SRCC's fix for the macOS `unix_listener ... too long for Unix domain socket` error ([connection](https://www.sherlock.stanford.edu/docs/advanced-topics/connection/)); it works on Linux too.
- Trade-off (SRCC): every multiplexed connection lands on the **same login node**, which also means a tmux session there is findable again.
- **Agent check before any Sherlock command:** `ssh -O check sherlock` → `Master running` means go; anything else means ask Brando to run `ssh sherlock` once (rule 2), or use another verified route from [reusable agent access](sherlock-agent-access.md).
- Optional, fewer password prompts: GSSAPI (Kerberos single sign-on for SSH) with `kinit brando9@stanford.edu` (Kerberos tickets last 25 h, so about once a day) plus `GSSAPIAuthentication yes` / `GSSAPIDelegateCredentials yes` in the host block; Duo is still required ([connection](https://www.sherlock.stanford.edu/docs/advanced-topics/connection/)).

### First-time setup Brando must do himself (once per computer)

1. Add the `~/.ssh/config` block above.
2. `ssh sherlock` → accept the host key, type the password, approve Duo.
3. Leave it; for the next 12 h (`ControlPersist`) agents on that computer reuse the socket with no prompts.

---

## Compute (Slurm)

Check what *this account* can use before submitting: `sh_part` (partitions, idle/total cores and GPUs, default/max runtime, per-node sizes). Whether the Koyejo group has its own owner partition shows up here ([running-jobs](https://www.sherlock.stanford.edu/docs/user-guide/running-jobs/)).

| Partition | Purpose | Limits (SRCC docs) |
|:--|:--|:--|
| `normal` (default) | general CPU jobs, 20-64 cores/node, 6-8 GB RAM/core | default 2 h, max 2 days; up to 7 days with `--qos=long` (only for users not in an owner group) |
| `bigmem` | jobs needing > 256 GB, up to 4 TB RAM/node | max 1 day |
| `gpu` | GPU jobs, 4 or 8 GPUs/node, up to 2 TB RAM/node | 16 GPUs/user; `sh_part` example shows default 1 h, max 2 days |
| `dev` | testing/debugging; dedicated nodes + MIG (Multi-Instance GPU) slices | 2 h max, 4 cores + 2 GPUs/user |
| `service` | lightweight recurring/persistent tasks (transfers, small servers) | 2 jobs, 16 cores/user, 2 days |
| `owners` | only for members of groups that bought nodes; huge pool | **preemptible**: jobs are killed and re-queued when the owner needs the node |
| `<PI sunetid>` | a PI group's own partition, if it bought nodes | up to 7 days, `--qos=high_p` for priority |

Sources: [running-jobs](https://www.sherlock.stanford.edu/docs/user-guide/running-jobs/), [gpu](https://www.sherlock.stanford.edu/docs/user-guide/gpu/).

### Interactive

```bash
sh_dev                              # 1 core, 4 GB, 1 h on the dev partition, usually no wait
sh_dev -c 4 -m 8GB -g 1 -p gpu      # 4 cores, 8 GB, 1 GPU on the gpu partition
salloc -p normal -c 4 --mem=16G -t 2:00:00   # full Slurm options
```

`sh_dev` with no `-p` gets at most 2 cores and 8 GB per user at a time ([running-jobs](https://www.sherlock.stanford.edu/docs/user-guide/running-jobs/)).

### GPUs

- SRCC documents `--gpus`/`-G` for requesting GPUs ([gpu](https://www.sherlock.stanford.edu/docs/user-guide/gpu/)); `--gres=gpu:N`, which `scripts/sherlock_dispatch.sh` emits, is also accepted.
- Pick a GPU type with constraints: `-C GPU_SKU:A100_SXM4`, `-C GPU_MEM:80GB`, `-C GPU_GEN:AMP`. List what a partition has with `sh_node_feat -p gpu | grep GPU_SKU`; an unsatisfiable constraint is rejected outright ([node-features](https://www.sherlock.stanford.edu/docs/advanced-topics/node-features/)).
- GPUs default to "Exclusive Process" compute mode; `--gpu_cmode=shared` if several processes must share one ([gpu](https://www.sherlock.stanford.edu/docs/user-guide/gpu/)).

### Example: CPU batch job

```bash
#!/bin/bash
#SBATCH --job-name=cpu_job
#SBATCH --partition=normal
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com

set -euo pipefail
ml python/3.12.1 uv
cd "$SCRATCH/<repo>"
source .venv/bin/activate
export PYTHONUNBUFFERED=1          # see prints live in the .out file
python my_script.py
```

### Example: GPU batch job

```bash
#!/bin/bash
#SBATCH --job-name=gpu_job
#SBATCH --partition=gpu
#SBATCH --gpus=1
#SBATCH --cpus-per-gpu=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH -C GPU_MEM:80GB            # optional; check sh_node_feat -p gpu first
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err
#SBATCH --mail-type=BEGIN,END,FAIL  # BEGIN only for long or important runs (Rule 82)
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com

set -euo pipefail
ml python/3.12.1 uv cuda           # pick versions with: ml spider cuda
cd "$SCRATCH/<repo>"
source .venv/bin/activate
export PYTHONUNBUFFERED=1
nvidia-smi -L
python train.py
```

For jobs over 2 days on `normal`: `#SBATCH --qos=long` and `--time=7-00:00:00` max ([running-jobs](https://www.sherlock.stanford.edu/docs/user-guide/running-jobs/)).

### Watching jobs

```bash
squeue -u $USER                       # PD = pending (reason in last column), R = running
sacct -j <jobid> --format=JobID,State,Elapsed,MaxRSS,ExitCode
scancel <jobid>
```

### Dispatcher & Multi-Job Etiquette

Use `scripts/sherlock_dispatch.sh` (mirrors `snap_dispatch.sh`) to launch and track Slurm jobs; it activates `~/venvs/main` (below) in the job:

```bash
# Launch jobs (submitting multiple distinct jobs at once is fine and encouraged)
bash scripts/sherlock_dispatch.sh run exp1 'python train.py --lr 1e-4' --gpu 1
bash scripts/sherlock_dispatch.sh run exp2 'python train.py --lr 3e-4' --gpu 1

# List active jobs
bash scripts/sherlock_dispatch.sh list
```

**Anti-spam cluster safeguards (10-18-2026):**
- **Concurrent jobs:** submitting multiple distinct Slurm jobs concurrently is standard and supported.
- **No tight polling loops:** never run tight loops or `watch` querying `squeue`/`sacct` (wait at least 60 s between status checks).
- **No SSH storms:** always reuse the multiplexed SSH `ControlMaster` connection.
- **No duplicate submissions:** do not resubmit an identical job while an earlier copy is still pending.
- **Agents on login nodes:** running coding agents (`claude`, `codex`, `grok`, `agy`, `agent`, `vibe`) directly on the login node is explicitly fine and approved by Brando (they are low-CPU orchestrators for editing, git and job dispatch). They are interactive-session processes; persistent servers that outlive the session are not (hard rule 6).
- **Keep heavy compute on compute nodes:** always dispatch heavy computation (training, large model inference, heavy preprocessing) to compute nodes via Slurm.

---

## Filesystem

| Path | Type / backups | Quota | Retention | Use for |
|:--|:--|:--|:--|:--|
| `$HOME` | NFS, snapshots + off-site replication | 15 GB | kept while account exists | code, configs, small scripts |
| `$GROUP_HOME` | NFS, snapshots + replication; shared with the PI group | 1 TB | kept | shared code, venvs, software |
| `$SCRATCH` | Lustre, fast, no backup | 100 TB, 20M inodes | **purged 90 days after last content change** | active job I/O, checkpoints |
| `$GROUP_SCRATCH` | Lustre, shared with group | 100 TB, 20M inodes | purged 90 days | shared job I/O |
| `$L_SCRATCH` | node-local SSD | n/a | deleted when the job ends | many small reads/writes inside one job |
| `$OAK` | Lustre, purchased per group | what the group bought | kept | long-term data (only if the group pays) |

Source: [storage](https://www.sherlock.stanford.edu/docs/storage/), [filesystems](https://www.sherlock.stanford.edu/docs/storage/filesystems/).

- `sh_quota` shows usage on every filesystem (`sh_quota -f SCRATCH -j` for JSON).
- Purge clock is the file's *content* modification; reading, renaming, `chmod` or `touch` do not reset it. Do not try (hard rule 4).
- `$HOME`/`$GROUP_HOME` are NFS: fine for code, bad for many jobs hammering the same files. Stage `$OAK` data to `$SCRATCH` at job start ([storage](https://www.sherlock.stanford.edu/docs/storage/)).

### Moving data

```bash
rsync -avP ./data/ sherlock:'$SCRATCH'/data/          # casual transfers via login nodes
rsync -avP ./big/ sherlock-dtn:'$SCRATCH'/big/        # large transfers via the DTN
```

Large transfers through login nodes can hit login-node limits; use the DTN or Globus ([data-transfer](https://www.sherlock.stanford.edu/docs/storage/data-transfer/)).

---

## Environment Setup

The primary scientific Python 3.12 environment is `~/venvs/main`, activated automatically in `~/.bashrc` and by `scripts/sherlock_dispatch.sh`:

```bash
# Modules loaded automatically:
module load gcc/12.4.0 python/3.12.1 uv
source ~/venvs/main/bin/activate
```

Installed and verified in `~/venvs/main` (10-18-2026): `scipy` 1.16.3, `numpy` 2.2.6, `pandas` 2.3.2, `scikit-learn` 1.7.2, `torch` 2.6.0+cu124, `torchvision` 0.21.0, `torchaudio` 2.6.0, `transformers` 4.57.6, `datasets` 2.14.4, `accelerate` 1.15.0, `tqdm` 4.70.1, `wandb` 0.23.0, `einops` 0.8.2, `matplotlib` 3.11.2.

To install additional packages into `~/venvs/main` without glibc compilation errors, always use `--only-binary :all:`:

```bash
uv pip install --python ~/venvs/main/bin/python --only-binary :all: <package_name>
```

New per-project venvs, the SRCC way:

```bash
ml spider python            # list versions (Lmod; `ml` = `module`)
ml python/3.12.1 uv
export UV_PYTHON=$(which python3)   # make uv use the module Python, not download its own
cd "$GROUP_HOME/<repo>"      # venvs have many files: $GROUP_HOME, not $HOME, when $HOME's 15 GB is tight
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

- SRCC recommends the module Python with `uv` and setting `UV_PYTHON`; large venvs belong in `$GROUP_HOME` to stay under the `$HOME` quota ([python](https://www.sherlock.stanford.edu/docs/software/using/python/)).
- Many concurrent jobs reading one venv on NFS is heavy I/O; for big job arrays, put a copy of the venv on `$SCRATCH` ([python](https://www.sherlock.stanford.edu/docs/software/using/python/)).
- CUDA/cuDNN come from modules (`ml spider cuda`), not pip/conda ([anaconda](https://www.sherlock.stanford.edu/docs/software/using/anaconda/)).
- `module purge` before loading a clean set if versions conflict ([modules](https://www.sherlock.stanford.edu/docs/software/modules/)).

---

## Sherlock vs SNAP vs FarmShare: which to pick

| Situation | Pick |
|:--|:--|
| Need a GPU now and SNAP's Koyejo nodes are busy | Sherlock `gpu` (16 GPUs/user cap) or `dev` for a quick test; also [Rule 75](../rules/workers.md#trigger-rule-75): try every reachable cluster |
| Long-running agent sessions, tmux, Vals/Claude CLI profiles already set up | SNAP (see [snap.md](snap.md)) |
| Many independent CPU jobs (sweeps, evals at $0) | Sherlock `normal` (thousands of cores, 2-day jobs, 7 with `--qos=long`) |
| Jobs needing > 256 GB RAM | Sherlock `bigmem` |
| Unsponsored or coursework runs, up to 4 L40S | [FarmShare](farmshare.md) |
| Data that must live for months | SNAP DFS, `$GROUP_HOME`, or `$OAK`; never `$SCRATCH` alone |
| Agent can't get a Duo-free connection | SNAP, or wait for Brando to open the Sherlock master socket |

---

## Common Issues

### `Connection refused` / timeout on port 22
**Cause:** IP temporarily banned after too many failed logins, or a stale macOS SSHFS mount retrying ([connecting](https://www.sherlock.stanford.edu/docs/getting-started/connecting/)).
**Fix:** stop retrying, wait, unmount SSHFS; report to Brando.

### `unix_listener: ... too long for Unix domain socket`
**Fix:** `ControlPath ~/.ssh/%C` ([connection](https://www.sherlock.stanford.edu/docs/advanced-topics/connection/)).

### Process killed on the login node
**Cause:** login-node resource limits. **Fix:** `sh_dev` or `sbatch`.

### `Job violates accounting/QOS policy`
**Cause:** request over a partition limit (e.g. more GPUs/time than allowed) ([gpu](https://www.sherlock.stanford.edu/docs/user-guide/gpu/)). **Fix:** check `sh_part`, shrink the request.

### Job pending a long time
**Fix:** `squeue -u $USER` reason column; ask for less (time, memory, GPU type), or use `dev` for tests.

### Module conflicts
**Symptom:** wrong library versions after loading modules. **Fix:** `module purge` then load only what you need.

### Output file empty while job runs
**Cause:** Python buffering. **Fix:** `python -u` or `export PYTHONUNBUFFERED=1` ([python](https://www.sherlock.stanford.edu/docs/software/using/python/)).

---

## Tips

- `ssh -O check sherlock` before anything; `ssh -O exit sherlock` to drop the master.
- Code in `$HOME`/`$GROUP_HOME` (backed up), data and checkpoints in `$SCRATCH`, final results copied off or committed.
- Profile in `sh_dev` (`htop`, `nvtop`) before sizing a big `sbatch` request; smaller requests start sooner ([running-jobs](https://www.sherlock.stanford.edu/docs/user-guide/running-jobs/)).
- Sherlock docs: https://www.sherlock.stanford.edu/docs/
- Report problems to srcc-support@stanford.edu with the details their [troubleshoot page](https://www.sherlock.stanford.edu/docs/user-guide/troubleshoot/) asks for (job ID, exact error, what you ran).

---

## Live Verification Results (10-18-2026)

Verified live via authenticated OpenSSH ControlMaster session:

1. **Identity and Paths:**
   ```text
   Hostname: sh02-ln03.stanford.edu
   User: brando9 (uid=412530) | Primary group: sanmi (gid=267909) | Groups: sanmi, sh_s-eng, sh_users
   $HOME: /home/users/brando9
   $SCRATCH: /scratch/users/brando9
   $GROUP_HOME: /home/groups/sanmi
   ```
2. **Storage Quotas (`sh_quota`):**
   - `$HOME`: 1.0 MB / 15.0 GB (0%)
   - `$GROUP_HOME`: 204.7 GB / 1.0 TB (19%)
   - `$SCRATCH`: 4.0 KB / 100.0 TB (0%, 20.0M inodes, 90-day content purge)
   - `$GROUP_SCRATCH`: 4.0 KB / 100.0 TB (0%, 20.0M inodes, 90-day content purge)
3. **Partition Inventory (`sh_part`):**
   - `normal*` (default): 268 nodes, 7,048 cores (707 idle, 66,216 queued), 2h default / 7d max
   - `bigmem`: 13 nodes, 1,080 cores (643 idle), up to 4,096 GB RAM/node, 1d max
   - `gpu`: 49 nodes, 1,508 cores, 200 GPUs (27 idle, 664 queued), 1h default / 2d max
   - `dev`: 4 nodes, 112 cores (92 idle), 64 GPUs (63 idle), interactive only (`srun`/`salloc`/`sh_dev`), 1h default / 2h max
   - `service`: 2 nodes, 64 cores (31 idle), 1h default / 2d max
4. **Slurm Compute Execution Verified:**
   - Interactive CPU: `srun -p dev -c 1 --time=00:01:00 hostname` ran on node `sh04-18n32.int` (Job ID 48398721).
   - Interactive GPU: `srun -p dev -c 1 -G 1 --time=00:01:00 nvidia-smi -L` verified: `NVIDIA A30 MIG 1g.6gb` (Job ID 48398725).
   - Batch CPU (`sbatch -p normal`): Job ID `48398650` completed in 8s on `sh02-02n43.int`.
   - Batch GPU (`sbatch -p gpu -G 1`): Job ID `48398680` allocated `sh04-11n10.int` and completed in 9s (`NVIDIA L40S 46GB`, Driver 550.163.01, CUDA 12.4).
5. **Python Virtual Environment (`venv`):**
   - Module: `python/3.12.1`
   - Path: `/home/groups/sanmi/brando9_envs/sherlock_test_env/bin/python` (Python 3.12.1); the shared working environment is `~/venvs/main` (above).
6. **AI Agent Policy (`/etc/agents/AGENTS.md`):**
   - SRCC cluster policy prohibits unattended background servers or daemons on login nodes.
   - Attended OpenSSH multiplexing (`ControlMaster auto`, `ControlPersist 12h`) is fully compliant.

---

## Acknowledgment in papers

Wording SRCC suggests (welcome email, 10-15-2026):

> Parts of the computing for this project was performed on the Sherlock cluster. We would like to thank Stanford University and the Stanford Research Computing Center for providing computational resources and support that have contributed to these research results.
