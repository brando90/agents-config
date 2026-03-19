# Machine: Mac — Local Development Machine

Template for a macOS development machine (Apple Silicon or Intel).

---

## Connection

Local machine. No SSH needed.

---

## Filesystem

| Path | Description |
|:-----|:------------|
| `~/` | Home directory |
| `~/keys/` | API keys and tokens (not committed to git) |
| `~/uv_envs/` | uv-managed Python virtual environments |
| `~/.virtualenvs/` | Legacy virtualenvs (if any) |

**Storage notes:**
- No root-squash or mount issues. Straightforward local filesystem.
- APFS with case-insensitive filenames by default.

---

## Compute

- **Chip:** <CHIP_MODEL> (e.g., Apple M3 Max)
- **RAM:** <RAM_AMOUNT> (unified memory)
- **GPU:** Integrated (Metal, not CUDA)
- **OS:** macOS <VERSION>

---

## Environment Setup

```bash
# Homebrew
brew update && brew upgrade

# Python via uv
uv venv <VENV_PATH>
source <VENV_PATH>/bin/activate

# Lean 4 via elan
elan toolchain install leanprover/lean4:<VERSION>
elan default leanprover/lean4:<VERSION>

# Docker Desktop (for Harbor)
open -a Docker
```

---

## Differences from Cluster

| Aspect | Mac | Cluster |
|:-------|:----|:--------|
| GPU | Metal (no CUDA) | NVIDIA CUDA |
| Docker | Docker Desktop | Native Docker |
| Filesystem | Local APFS | NFS/AFS/LFS |
| Package manager | Homebrew | apt/yum |
| Python | uv preferred | uv or conda |
| vllm/sglang | Not supported (Linux-only) | Supported |

---

## Common Issues

### Docker Desktop not running
**Symptom:** `Cannot connect to the Docker daemon`
**Fix:** Open Docker Desktop app, wait for it to start.

### Rosetta translation issues (Apple Silicon)
**Symptom:** Segfaults or missing libraries in x86 packages.
**Fix:** Use native arm64 packages where available. For x86-only tools: `arch -x86_64 <command>`.

---

## Tips

- Use `uv` for all new Python environments.
- Docker Desktop has limited resources by default; increase RAM/CPU in Docker Desktop settings for Harbor jobs.
- macOS does not support Linux-only packages (vllm, sglang, bitsandbytes). Develop on Mac, run on cluster.
