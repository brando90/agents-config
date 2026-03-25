# Machine: Mac — MacBook Pro (Local Development)

MacBook Pro 16" (2021), Apple M1 Max, 64 GB unified memory. Primary local development machine.

---

## Connection

Local machine — no SSH needed.

---

## Hardware

| Spec | Value |
|:-----|:------|
| **Model** | MacBook Pro 18,2 (2021 16") |
| **Chip** | Apple M1 Max |
| **Cores** | 10 (8 performance + 2 efficiency) |
| **RAM** | 64 GB unified memory |
| **GPU** | Integrated (Metal, not CUDA) |
| **OS** | macOS 26.3 (Tahoe) |
| **Arch** | arm64 (Rosetta 2 available for x86_64) |

---

## Filesystem

| Path | Description |
|:-----|:------------|
| `~/` | Home directory |
| `~/keys/` | API keys and tokens (loaded by `.zshrc`, never committed) |
| `~/uv_envs/` | uv-managed Python virtual environments |
| `~/agent-config/` | This repo — agent documentation system |
| `~/.zshrc` | Shell configuration (see Shell Config section) |

**Storage notes:**
- APFS with case-insensitive filenames by default.
- No root-squash or mount issues — straightforward local filesystem.

---

## Installed Tools

| Tool | Version | Notes |
|:-----|:--------|:------|
| Python | 3.11.6 | via uv |
| uv | 0.8.3 | Primary Python env manager |
| Homebrew | 5.1.0 | macOS package manager |
| Docker | 25.0.3 | Docker Desktop |
| Git | 2.50.1 | Apple Git |
| Lean 4 | 4.18.0 | Theorem prover (via elan) |
| elan | 4.1.1 | Lean version manager |
| nvm | installed | Node.js version manager (via Homebrew) |
| opam | installed | OCaml package manager |
| gcloud | installed | Google Cloud SDK |
| TeXLive | 2024 | LaTeX distribution |

---

## Python Environments (uv)

All managed via `uv` and stored in `~/uv_envs/`. The `no-gold-ref-judge` environment is auto-activated on shell start via `.zshrc`.

| Environment | Path |
|:------------|:-----|
| no-gold-ref-judge | `~/uv_envs/no-gold-ref-judge/` (default) |
| no-gold-ref-judge-arm64 | `~/uv_envs/no-gold-ref-judge-arm64/` |
| veribench | `~/uv_envs/veribench/` |
| veribench-dt | `~/uv_envs/veribench-dt/` |
| cert-judge | `~/uv_envs/cert-judge/` |
| dark-matter2 | `~/uv_envs/dark-matter2/` |
| self_opt_data_gen | `~/uv_envs/self_opt_data_gen/` |

Switch environments: `source ~/uv_envs/<name>/bin/activate`

---

## Shell Configuration (~/.zshrc)

Key sections (read `~/.zshrc` directly for full details):

- **PATH:** Homebrew (`/opt/homebrew/bin`), Docker, elan, TeXLive, gcloud, nvm
- **Default venv:** `no-gold-ref-judge` auto-activated on shell start
- **API keys and credentials:** Loaded from `~/keys/` files
- **SSH aliases:** Quick access to cluster machines
- **Claude Code aliases:** `clauded` / `claude-yolo` → `claude --dangerously-skip-permissions`
- **Other:** Kerberos config (commented out), opam init, Docker Desktop init

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

### Architecture mismatch in shell
**Note:** `uname -m` may report `x86_64` if the terminal runs under Rosetta. The chip is arm64 (M1 Max). Verify with `sysctl -n hw.optional.arm64`.

---

## Tips

- Use `uv` for all new Python environments.
- Docker Desktop has limited resources by default; increase RAM/CPU in Docker Desktop settings for Harbor jobs.
- macOS does not support Linux-only packages (vllm, sglang, bitsandbytes). Develop on Mac, run on cluster.
- The default activated venv is `no-gold-ref-judge` — switch with `source ~/uv_envs/<name>/bin/activate`.
