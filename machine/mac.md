# Machine: Mac — macOS (Apple Silicon)

Local development machine. Apple Silicon arm64, no CUDA.

---

## Key Constraints

- **No CUDA.** Linux-only packages (vllm, sglang, bitsandbytes) do not work on Mac. Develop on Mac, run on cluster.
- **arm64 architecture.** Use native arm64 packages. For x86-only tools: `arch -x86_64 <command>`.
- **Local APFS filesystem.** No NFS/AFS, no root-squash, no mount issues. Docker Desktop runs locally.

---

## Shell Config

Read `~/.zshrc` directly — it is the source of truth for paths, active Python env, API keys, SSH aliases, and tool locations. Do not duplicate here.

Key paths:
- `~/uv_envs/` — uv-managed Python virtual environments (`ls ~/uv_envs/` to see available envs)
- `~/keys/` — API keys and tokens (loaded by `.zshrc`, never committed)

---

## Mac vs Cluster

| Aspect | Mac | Cluster |
|:-------|:----|:--------|
| GPU | Metal (no CUDA) | NVIDIA CUDA |
| Docker | Docker Desktop (must be running) | Native Docker |
| Filesystem | Local APFS | NFS/AFS/LFS |
| vllm/sglang | Not supported (Linux-only) | Supported |

---

## Common Issues

### Docker Desktop not running
**Symptom:** `Cannot connect to the Docker daemon`
**Fix:** Open Docker Desktop app, wait for it to start.

### Architecture mismatch in shell
**Note:** `uname -m` may report `x86_64` if the terminal runs under Rosetta. Verify with `sysctl -n hw.optional.arm64`.
