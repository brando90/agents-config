# Machine: Marlowe — Stanford Marlowe Cluster

Template for Stanford's Marlowe cluster.

---

## Connection

```bash
ssh <user>@<MARLOWE_HOSTNAME>
```

- **Hostname:** `<MARLOWE_HOSTNAME>`
- **Authentication:** Stanford SUNet ID
- **Port:** 22

---

## Filesystem

| Path | Description |
|:-----|:------------|
| `~/` | Home directory |
| `<SCRATCH_PATH>` | Scratch storage (large, check purge policy) |
| `<SHARED_DATA_PATH>` | Shared group data |

**Storage notes:**
- Check with your group for specific quota and purge policies.
- Use scratch for large experiments, home for configs and small files.

---

## Compute

- **GPUs:** <GPU_COUNT> x <GPU_MODEL>
- **CPUs:** <CPU_COUNT> cores
- **RAM:** <RAM_AMOUNT>
- **Job scheduler:** <SLURM_OR_OTHER>

---

## Environment Setup

```bash
# Load environment
source <VENV_PATH>/bin/activate

# GPU check
nvidia-smi
```

---

## Common Issues

### SSH connection refused
**Symptom:** `Connection refused` when trying to SSH.
**Fix:** Ensure you're on the Stanford network or VPN. Check if the node is down.

---

## Tips

- Similar workflow to Sherlock but with different node configurations.
- Check group-specific documentation for partition and resource policies.
