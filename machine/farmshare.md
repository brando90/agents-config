# Machine: FarmShare — Stanford FarmShare Community Cluster

**Doc link:** <https://github.com/brando90/agents-config/blob/main/machine/farmshare.md>

**TLDR:** FarmShare is Stanford's free Slurm cluster for coursework and unsponsored research: 24 NVIDIA L40S graphics processing units (GPUs, 46 GB each) on six `oat` nodes, at most 4 GPUs per user at a time. Connect with `ssh farmshare` (ControlMaster alias), submit all compute with `sbatch`, install with pip into a virtual environment (venv) in `$HOME` (there is no module system), and set Slurm mail per [Trigger Rule 82](../rules/hosts.md#trigger-rule-82). Verified 10-20-2026 (CPU job 1860187, GPU job 1860189, vLLM job 1860269).

---

## Connection

Add this Secure Shell (SSH) alias to `~/.ssh/config` on the Mac (done 10-20-2026; backup `~/.ssh/config.before-farmshare-*`):

```sshconfig
Host farmshare
    HostName login.farmshare.stanford.edu
    User brando9
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 4h
```

```bash
ssh farmshare                    # Brando: SUNet password + Duo (SMS code) once; opens the shared socket
ssh -O check farmshare           # agents: is the socket alive?
ssh farmshare 'squeue -u $USER'  # agents: reuse the socket, no new Duo prompt
```

- **Hostname:** `login.farmshare.stanford.edu` (load-balanced login nodes `rice-0x`, Ubuntu 24.04).
- **Authentication:** SUNet ID + password + Duo two-step. Brando types it; agents never type, store or ask for the password and never create SSH keys, cron jobs or `scrontab` entries.
- **Use the alias, not the full hostname.** `ssh brando9@login.farmshare.stanford.edu` does not match `Host farmshare`, so it leaves no ControlMaster socket for agents to reuse.
- **First login (one time per account):** the first real SSH login prints `Creating directory '/home/users/brando9'` and creates the home directory and the Slurm account. Before that, jobs cannot run and Open OnDemand shows "Home directory not found"; after it, click OnDemand's "Restart Web Server" once.
- **Open OnDemand (web):** <https://ondemand.farmshare.stanford.edu>. Its Shell app asks for the SUNet password; its JupyterLab app's terminal runs on a compute node with `sbatch`, `squeue`, `git` and internet, and works without a password.

---

## Fair use (hard rules)

- **Coursework and unsponsored research only.** FarmShare is not for sponsored research (work paid by a grant, contract or company) and never for high-risk data such as protected health information or personally identifiable information ([policy](https://docs.farmshare.stanford.edu/policy/)). Sponsored or company-funded runs go to Sherlock or SNAP.
- **No compute on login nodes.** `rice` is for editing, git, `sbatch`, `squeue` and reading results; light agent orchestration is fine. Training, inference, preprocessing and large pip builds run in a Slurm job (batch, or `srun --pty` on a compute node).
- **Throttle arrays.** QOS (quality of service) `gpu` allows 4 running jobs and 32 submitted jobs per user, and every array task counts toward the 32. Pack shards into a throttled array (`--array=0-30%4` with 31 shards), never a 155-task array (refused with `QOSMaxSubmitJobPerUserLimit`). The 32 slots are shared by all of your experiments, so check `squeue -u $USER -q gpu -h | wc -l` before a GPU submit.
- **No flooding.** Wait ≥60 s between `squeue`/`sacct` polls, never resubmit an identical job that is still pending, and reuse the ControlMaster socket instead of opening new SSH sessions.
- **Stay inside the quality of service.** Queue as much as the scheduler accepts, but no extra accounts, renamed jobs or other tricks to get past per-user limits. One person per SUNet ID; never share credentials.

---

## Partitions and limits

Live values from `sacctmgr` on 10-20-2026 (account `operator`). The [docs table](https://docs.farmshare.stanford.edu/slurm/) is older (it shows `gpu` = 6 GPUs, `long` = 32 CPUs); trust the cluster:
`sacctmgr -nP show qos format=name,maxwall,maxtrespu,maxjobspu,maxsubmitpu`.

| QOS | Partition | Wall limit | Per-user limit | Use |
|:----|:----------|:-----------|:---------------|:----|
| `normal` (default) | `normal` | 2 days | cpu=512, 1 GPU, 128 running / 1024 submitted | CPU jobs |
| `gpu` | `gpu` | 2 days | 4 GPUs, 4 running / 32 submitted | all GPU work |
| `long` | `normal` | 7 days | cpu=128, 4 jobs | long CPU-only jobs |
| `dev` | `dev` | 8 hours | cpu=8, mem=32G, 1 job | quick tests |
| `interactive` | `interactive` | 1 day (docs) | cpu=16, mem=64G, 4 jobs | `srun --pty` shells |
| `bigmem` | `bigmem` | 2 days | mem=1.5T, 4 jobs | jobs needing >192 GB RAM |
| `caddyshack` | `caddyshack` | — | cpu=8, mem=32G, 1 job | small side jobs |

**Hardware:** 6 GPU nodes `oat-01`..`oat-06`, each 4x NVIDIA L40S 46 GB (64 CPUs, 256 GB RAM; driver 595.91.07, CUDA 13.2; 46.3 TFLOPS on an fp32 4096x4096 matmul); 14 CPU nodes (80+ CPUs, 191 GB+); 2 bigmem nodes (512 CPUs, 1.5 TB).

**Queue:** GPUs are busy midday (10-20-2026 13:00: ~17 of 24 L40S running, ~50 jobs pending, `squeue --start` estimated ~15 h). Submit early and check `squeue --start -u $USER`.

---

## Compute

Exact GPU flags (job 1860189, accepted on the first try): `-p gpu --qos=gpu --gres=gpu:N`, with N ≤ 4.

```bash
#!/bin/bash
#SBATCH --job-name=<run_name>
#SBATCH -p gpu
#SBATCH --qos=gpu
#SBATCH --gres=gpu:1
#SBATCH -c 4
#SBATCH --mem=32G
#SBATCH -t 0-12:00:00
#SBATCH --output=%x_%j.out
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=brandojazz@gmail.com,brando.science@gmail.com

source ~/venvs/fs_hf/bin/activate
export HF_HOME=$HOME/hf_cache
python train.py
```

```bash
# CPU job: the default partition and QOS (normal), 2-day max
sbatch -c 8 --mem=32G -t 1-00:00:00 job.sh
# Long CPU job: 7 days, CPU only
sbatch -p normal --qos=long -c 16 -t 7-00:00:00 job.sh
# Interactive GPU shell (not yet tested on FarmShare)
srun -p gpu --qos=gpu --gres=gpu:1 -c 4 --mem=32G -t 2:00:00 --pty bash
```

Slurm mail from FarmShare comes from `nobody@stanford.edu` and reaches both inboxes within seconds (job 1860206).

### Model size per L40S (46 GB)

- **Full training (bf16 weights + AdamW):** up to ~1.7B parameters on one L40S (e.g. Qwen3-1.7B-Base).
- **~4B:** LoRA (low-rank adaptation) on one GPU, or full training with FSDP (fully sharded data parallel) across the 4 GPUs of one node (`--gres=gpu:4`, which takes your whole GPU limit). Check memory with a short `dev` or 1-step run first.
- **Larger than 4B full training:** not on FarmShare; use Sherlock, SNAP or Marlowe.

---

## Filesystem

| Path | Description |
|:-----|:------------|
| `$HOME` = `/home/users/<user>` | Home on NFS (network file system), 198 TB free on 10-20-2026, no quota error seen. Keep code, venvs, data and `HF_HOME` here. |
| `/scratch` | Listed in the docs, but not mounted on the login node (10-20-2026). Run `df -h /scratch` inside a job before relying on it. |

---

## Environment Setup

There is no module system (`module: command not found`), so skip `module load`. Build venvs with `/usr/bin/python3.12 -m venv`, not the Python 3.14 that Jupyter puts on `PATH`, and install with pip.

| Venv | Contents |
|:-----|:---------|
| `~/venvs/fs_torch` | torch 2.14.1+cu130, numpy (3.2 GB); GPU smoke test |
| `~/venvs/fs_hf` | vllm 0.32.0, transformers 5.19.0, datasets 5.1.0, accelerate 1.15.0, torch 2.13.0+cu130; lock file `~/venvs/fs_hf/requirements.lock.txt` |

- **Per-experiment extras:** make `~/venvs/<exp>`, `pip install -r ~/venvs/fs_hf/requirements.lock.txt`, then the extras, so `fs_hf` stays shared.
- **vLLM:** nodes have no CUDA toolkit. `fs_hf/bin/activate` exports `CUDA_HOME=<venv>/.../site-packages/nvidia/cu13` (pip `nvcc`) and `VLLM_USE_FLASHINFER_SAMPLER=0`. Copy both lines into any new venv's `activate`; without them vLLM dies at warmup (jobs 1860208, 1860264). Prefer non-flashinfer backends.

---

## Common Issues

### `QOSMaxSubmitJobPerUserLimit`
**Symptom:** `sbatch` refuses a GPU job or array.
**Fix:** you already have 32 jobs or array tasks submitted under QOS `gpu`. Pack shards into fewer tasks, or wait for jobs to finish.

### `python3.12 -m venv` fails within seconds
**Symptom:** the venv build job dies on `wheat-01`.
**Fix:** that node lacks `python3.12-venv`. Add `--exclude=wheat-01`, or build in the JupyterLab terminal.

### OnDemand says "Home directory not found"
**Fix:** make the first SSH login (see Connection), then click "Restart Web Server" in OnDemand.

---

## Tips

- FarmShare vs the others: FarmShare is free and has 4 L40S per user but only unsponsored work; Sherlock takes sponsored work; SNAP is the lab cluster ([snap.md](snap.md), [sherlock.md](sherlock.md)).
- Docs: <https://docs.farmshare.stanford.edu/>
