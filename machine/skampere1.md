# Machine: skampere1 — SNAP Cluster Node

**skampere1 is a node in the Stanford SNAP cluster.** For full environment, filesystem, and workflow documentation, see `~/agents-config/machine/snap.md`.

This file only lists skampere1-specific hardware. Everything else (DFS/AFS/LFS layout, environment setup, new-node bootstrap, common issues) is in `~/agents-config/machine/snap.md`.

---

## Hardware

| Spec | Value |
|:-----|:------|
| **Hostname** | `skampere1.stanford.edu` |
| **GPUs** | 8x NVIDIA A100-SXM4-80GB |
| **GPU RAM** | 80 GB per GPU (640 GB total) |
| **System RAM** | ~2 TiB |
| **CUDA** | 12.4 (verify: `nvcc --version`) |
| **OS** | Ubuntu 24.04 |

```bash
# Quick verify
ssh <user>@skampere1.stanford.edu
nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv,noheader
```

---

## See Also

- `~/agents-config/machine/snap.md` — full SNAP cluster docs (filesystem, env setup, new-node bootstrap, common issues)
