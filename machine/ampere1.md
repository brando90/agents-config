# Machine: ampere1 — SNAP Cluster Node

**ampere1 is a node in the Stanford SNAP cluster.** For full environment, filesystem, and workflow documentation, see `~/agent-config/machine/snap.md`.

This file only lists ampere1-specific hardware. Everything else (DFS/AFS/LFS layout, environment setup, new-node bootstrap, common issues) is in `~/agent-config/machine/snap.md`.

---

## Hardware

| Spec | Value |
|:-----|:------|
| **Hostname** | `ampere1.stanford.edu` |
| **GPUs** | 8x NVIDIA A100-SXM4-80GB |
| **GPU RAM** | 80 GB per GPU (640 GB total) |
| **System RAM** | ~2 TiB |
| **CUDA** | 12.4 (verify: `nvcc --version`) |
| **OS** | Ubuntu 22.04 |

```bash
# Quick verify
ssh brando9@ampere1.stanford.edu
nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv,noheader
```

---

## See Also

- `~/agent-config/machine/snap.md` — full SNAP cluster docs (filesystem, env setup, new-node bootstrap, common issues)
