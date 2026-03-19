# Machine: Ampere1 — GPU Cluster Node

Template for a GPU cluster node with Ampere-class GPUs (A100/H100).

---

## Connection

```bash
ssh <YOUR_USERNAME>@<HOSTNAME>
```

- **Hostname:** `<HOSTNAME>`
- **Jump host:** `<JUMP_HOST>` (if behind a bastion)
- **Port:** 22

---

## Filesystem

| Path | Description |
|:-----|:------------|
| `~/` | Home directory (NFS-mounted, backed up, small quota) |
| `/lfs/<HOSTNAME>/0/<USERNAME>/` | Local scratch (fast SSD, large, NOT backed up) |
| `<DFS_PATH>` | Distributed filesystem (shared across nodes) |
| `<AFS_PATH>` | AFS home (if applicable) |

**Storage notes:**
- Run compute jobs from local scratch (`/lfs/`), not from NFS home. NFS has root-squash issues with Docker.
- DFS/AFS may have stale mount issues after network disruptions.

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
# Python via uv
source <VENV_PATH>/bin/activate

# Docker (for Harbor, etc.)
cat <TOKEN_PATH> | docker login ghcr.io -u <GITHUB_USERNAME> --password-stdin

# GPU check
nvidia-smi
```

---

## Common Issues

### Stale DFS/AFS mounts
**Symptom:** `ls ~/` hangs or returns I/O errors after network blip.
**Fix:** `kinit <USERNAME>@<REALM>` to refresh Kerberos ticket. If that fails, ask sysadmin to remount.

### Docker permission denied
**Symptom:** `docker: Got permission denied while trying to connect to the Docker daemon socket`
**Fix:** Ensure your user is in the `docker` group: `sudo usermod -aG docker $USER`, then re-login.

### GPU OOM during training
**Symptom:** `CUDA out of memory` despite free GPUs.
**Fix:** Check for zombie processes: `nvidia-smi` → kill stale PIDs. Or reduce batch size.

---

## Tips

- Always run Harbor/Docker jobs from `/lfs/` local scratch, not NFS home.
- Use `byobu` for persistent sessions that survive SSH disconnects.
- Check GPU allocation before starting large jobs: `nvidia-smi -L`.
