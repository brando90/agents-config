# Machine: mercury1 — SNAP Cluster Node

**mercury1 is a node in the Stanford SNAP cluster.** For full environment, filesystem, and workflow documentation, see `~/agents-config/machine/snap.md`.

This file only lists mercury1-specific hardware. Everything else (DFS/AFS/LFS layout, environment setup, new-node bootstrap, common issues) is in `~/agents-config/machine/snap.md`.

---

## Hardware

| Spec | Value |
|:-----|:------|
| **Hostname** | `mercury1.stanford.edu` |
| **GPUs** | 10x NVIDIA RTX A4000 |
| **GPU RAM** | 16 GB per GPU (160 GB total) |
| **System RAM** | ~487 GB |
| **CPU** | 96 cores |
| **CUDA** | 12.4 (verify: `nvcc --version`) |
| **OS** | Ubuntu 22.04 |

```bash
# Quick verify
ssh <user>@mercury1.stanford.edu
nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv,noheader
```

---

## See Also

- `~/agents-config/machine/snap.md` — full SNAP cluster docs (filesystem, env setup, new-node bootstrap, common issues)
