# Machine: Sherlock — Stanford Sherlock HPC Cluster

Template for Stanford's Sherlock high-performance computing cluster.

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
- `$SCRATCH` files are purged after 90 days of no access. Do not store important results there long-term.
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

---

## Environment Setup

```bash
# Load modules
module load python/<VERSION>
module load cuda/<VERSION>

# Or use uv
source <VENV_PATH>/bin/activate
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
