# Machine: mercury2 — SNAP Cluster Node

**mercury2 is a node in the Stanford SNAP cluster.** For full environment, filesystem, and workflow documentation, see `~/agents-config/machine/snap.md`.

This file only lists mercury2-specific hardware. Everything else (DFS/AFS/LFS layout, environment setup, new-node bootstrap, common issues) is in `~/agents-config/machine/snap.md`.

---

## Hardware

| Spec | Value |
|:-----|:------|
| **Hostname** | `mercury2.stanford.edu` |
| **GPUs** | 10x NVIDIA RTX A4000 |
| **GPU RAM** | 16 GB per GPU (160 GB total) |
| **CPU** | 96x Intel Xeon Gold 6342 |
| **System RAM** | ~503 GiB |
| **LFS** | `/lfs/mercury2/0/brando9` (fast local storage, used as `$HOME`) |
| **CUDA** | 12.4 (verify: `nvcc --version`) |
| **OS** | Ubuntu 20.04 |

```bash
# Quick verify
nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv,noheader
nproc && free -h
```

---

## Notes

- `docker` resolves to the user-owned `~/.local/bin/docker` compatibility shim backed by Podman 5.4.1; verify workload compatibility before relying on Docker-specific behavior.
- Harbor is installed per-node via `uv tool install harbor` at `~/.local/bin/harbor`; invoke it through `/dfs/scratch0/brando9/bin/harbor`, which removes the incompatible shared `PYTHONPATH` first.

---

## See Also

- `~/agents-config/machine/snap.md` — full SNAP cluster docs (filesystem, env setup, new-node bootstrap, common issues)
