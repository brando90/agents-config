# Machine: SNAP — Stanford SNAP Cluster

Template for Stanford's SNAP GPU cluster nodes.

---

## Connection

```bash
ssh <YOUR_USERNAME>@<SNAP_HOSTNAME>
```

- **Hostname:** `<SNAP_HOSTNAME>`
- **Jump host:** N/A (direct SSH from Stanford network or VPN)
- **Port:** 22

---

## Filesystem

| Path | Description |
|:-----|:------------|
| `~/` | AFS/DFS home (shared across nodes, has quota) |
| `/lfs/<HOSTNAME>/0/<USERNAME>/` | Local scratch (fast, large, NOT backed up) |
| `<DFS_SHARED_PATH>` | DFS shared data directory |

**Storage notes:**
- **Critical:** Run Docker/Harbor jobs from `/lfs/`, not `~/`. NFS/AFS has root-squash that blocks Docker writes.
- AFS tickets expire; run `kinit` if `ls ~/` hangs.
- Local scratch is per-node and not shared. Copy data to each node you use.

---

## Compute

- **GPUs:** <GPU_COUNT> x <GPU_MODEL> (<VRAM> each)
- **CPUs:** <CPU_COUNT> cores
- **RAM:** <RAM_AMOUNT>
- **CUDA:** <CUDA_VERSION>
- **OS:** Ubuntu <VERSION>

---

## Environment Setup

```bash
# Setup script (handles AFS/DFS/LFS paths)
source <PROJECT_DIR>/snap_setup.sh

# Python via uv
source <VENV_PATH>/bin/activate

# Docker auth
cat <TOKEN_PATH> | docker login ghcr.io -u <GITHUB_USERNAME> --password-stdin
```

---

## Common Issues

### AFS token expiration
**Symptom:** Home directory becomes unresponsive. `ls ~/` hangs.
**Fix:** `kinit <USERNAME>@<REALM>` then `aklog`.

### Local scratch full
**Symptom:** Write failures on `/lfs/`.
**Fix:** Clean up old job outputs, Docker images: `docker system prune -a`.

### Wrong Python env
**Symptom:** Import errors for packages you've installed.
**Fix:** Check `which python` and ensure the correct venv is activated.

---

## Tips

- Use `snap_setup.sh` before any job to ensure filesystem mounts are correct.
- Prefer `uv` over conda for new Python environments.
- Use `byobu` for persistent sessions.
