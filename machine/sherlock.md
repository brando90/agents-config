# Machine: Sherlock — Stanford Sherlock HPC Cluster

**Doc link:** <https://github.com/brando90/agents-config/blob/main/machine/sherlock.md>

**TLDR:** Stanford Sherlock uses scheduled compute jobs. For unattended agent commands and the distinction between fresh Duo login and existing authenticated access, start with [reusable agent access](sherlock-agent-access.md).

---

## Connection

```bash
ssh <user>@login.sherlock.stanford.edu
```

- **Hostname:** `login.sherlock.stanford.edu`
- **Authentication:** Stanford SUNet ID + two-factor (Duo)
- **Port:** 22

---

## Filesystem

| Path | Description |
|:-----|:------------|
| `$HOME` | Home directory (small quota, backed up) |
| `$SCRATCH` | Per-user scratch (large, auto-purged after 90 days) |
| `$OAK` | Oak storage (group-allocated, persistent) |
| `$GROUP_HOME` | Group home directory |

**Storage notes:**
- `$SCRATCH` files are purged after 90 days without content modification. Do not store important results there long-term.
- `$HOME` has a small quota (~15 GB). Use `$SCRATCH` or `$OAK` for large data.
- Oak storage requires a PI allocation.

---

## Compute

Sherlock is a shared cluster with heterogeneous nodes. Request resources via Slurm.

```bash
# Interactive GPU session
srun -p gpu -c 4 --gres=gpu:1 --mem=32G --time=4:00:00 --pty bash

# Batch job
sbatch <JOB_SCRIPT>.sh
```

- **GPU partitions:** `gpu` (general), `owners` (priority for owners)
- **GPU types:** V100, A100, H100 (specify with `--gres=gpu:<TYPE>:1`)

### Dispatcher & Multi-Job Etiquette

Use `scripts/sherlock_dispatch.sh` (mirrors `snap_dispatch.sh`) to launch and track Slurm jobs:

```bash
# Launch jobs (submitting multiple distinct jobs at once is fine and encouraged)
bash scripts/sherlock_dispatch.sh run exp1 'python train.py --lr 1e-4' --gpu 1
bash scripts/sherlock_dispatch.sh run exp2 'python train.py --lr 3e-4' --gpu 1

# List active jobs
bash scripts/sherlock_dispatch.sh list
```

**Anti-Spam Cluster Safeguards:**
- **Concurrent jobs:** Submitting multiple distinct Slurm jobs concurrently is standard and supported.
- **No tight polling loops:** Never run tight loops or `watch` querying `squeue`/`sacct` (wait $\ge 60\text{s}$ between status checks).
- **No SSH storms:** Always reuse the multiplexed SSH `ControlMaster` connection.
- **No duplicate submissions:** Do not resubmit an identical job while an earlier copy is still pending.
- **Agents on login nodes:** Running coding agents (`claude`, `codex`, `grok`, `agy`, `agent`, `vibe`) directly on the login node is explicitly fine and approved by Brando (they are low-CPU orchestrators for editing, git, and job dispatch).
- **Keep heavy compute on compute nodes:** Always dispatch heavy computation (training, large model inference, heavy preprocessing) to compute nodes via Slurm.

---

## Environment Setup

The primary scientific Python 3.12 environment is located at `~/venvs/main` and is automatically activated in `~/.bashrc` and by `scripts/sherlock_dispatch.sh`:

```bash
# Modules loaded automatically:
module load gcc/12.4.0 python/3.12.1 uv
source ~/venvs/main/bin/activate
```

**Installed & verified libraries in `~/venvs/main`:**
- `scipy` (1.16.3), `numpy` (2.2.6), `pandas` (2.3.2), `scikit-learn` (1.7.2)
- `torch` (2.6.0+cu124), `torchvision` (0.21.0), `torchaudio` (2.6.0)
- `transformers` (4.57.6), `datasets` (2.14.4), `accelerate` (1.15.0)
- `tqdm` (4.70.1), `wandb` (0.23.0), `einops` (0.8.2), `matplotlib` (3.11.2)

To install additional packages into `~/venvs/main` without glibc compilation errors, always use `--only-binary :all:`:
```bash
uv pip install --python ~/venvs/main/bin/python --only-binary :all: <package_name>
```

---

## Common Issues

### Job pending forever
**Symptom:** `squeue` shows PD (pending) for a long time.
**Fix:** Check cluster load with `squeue -u $USER`. Try a different partition or reduce resource request.

### Module conflicts
**Symptom:** Wrong library versions after loading modules.
**Fix:** `module purge` then load only what you need.

---

## Tips

- Use `$SCRATCH` for intermediate results, `$OAK` for final results.
- Check your quota: `sh_quota`.
- Sherlock docs: https://www.sherlock.stanford.edu/docs/
