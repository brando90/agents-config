# Machine: skampere2 — SNAP Cluster Node

**skampere2 is a node in the Stanford SNAP cluster.** For full environment, filesystem, and workflow documentation, see `~/agents-config/machine/snap.md`.

This file only lists skampere2-specific hardware. Everything else (DFS/AFS/LFS layout, environment setup, new-node bootstrap, common issues) is in `~/agents-config/machine/snap.md`.

---

## Hardware

| Spec | Value |
|:-----|:------|
| **Hostname** | `skampere2.stanford.edu` |
| **GPUs** | 8x NVIDIA H200 140 GiB |
| **GPU RAM** | 140 GiB per GPU (1.1 TiB total) |
| **CPUs** | 224 cores — Intel Xeon Platinum 8480+ (2x socket, NUMA) |
| **System RAM** | ~3 TiB |
| **NUMA** | 2 nodes: CPUs 0-55,112-167 (node0) and 56-111,168-223 (node1). Pin with `numactl --cpunodebind=0 --membind=0` when needed. |
| **OS** | Ubuntu (verify: `lsb_release -a`) |

```bash
# Quick verify
ssh <user>@skampere2.stanford.edu
nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv,noheader
```

---

## See Also

- `~/agents-config/machine/snap.md` — full SNAP cluster docs (filesystem, env setup, new-node bootstrap, common issues)
