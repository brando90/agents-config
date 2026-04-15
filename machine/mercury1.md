# Mercury1 — SNAP Node

## Hardware
- GPU: 10× NVIDIA RTX A4000 (16 GB VRAM each)
- CPU: 96 cores
- RAM: 487 GB
- LFS: `/lfs/mercury1/0/brando9` (fast local storage, used as `$HOME`)

## Behavioral Notes
- Home directory is on LFS (`/lfs/mercury1/0/brando9`), NOT DFS. DFS is at `/dfs/scratch0/brando9`.
- Many projects are cloned on both LFS and DFS — DFS copies are the canonical ones shared across machines.
- Keys are at `~/keys/` (symlink to DFS).

## Common Development Patterns

### Python Projects (uv / pip editable installs)
Most projects use `pyproject.toml`. Install in editable mode:
```bash
pip install -e ~/veribench
pip install -e ~/lean4ai
pip install -e ~/ZIP-FIT
```

### Running Tests
```bash
pytest tests/ -v                          # Run all tests
pytest tests/test_foo.py -v               # Single file
pytest tests/test_foo.py::TestClass -v    # Single class
```

### Lean 4 / Mathlib (Lake build system)
```bash
cd ~/veribench/veribench_dataset/lean_src
lake exe cache get   # Fetch precompiled Mathlib caches (required before first build)
lake build
lake lean path/to/file.lean  # Compile a single Lean file
```

### lean4ai Setup
```bash
conda create -y -n lean4ai python=3.10
conda activate lean4ai
pip install -e ~/lean4ai
pip install -e ~/ZIP-FIT
```

## Key Paths
- `~/keys/.brando90_github_token.txt` — GitHub token (on DFS, shared across servers)
- `~/veribench/snap_setup.sh` — Full SNAP cluster first-time setup script
- `~/veribench/setup.sh` — Local (non-SNAP) setup for veribench
