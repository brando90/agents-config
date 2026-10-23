# Pi coding agent on a local open-weight model (SNAP nodes)

**TLDR:** Pi 1.4.0 installs with no sudo (`npm install -g --prefix ~/.local @earendil-works/pi-coding-agent`) and runs well against a vLLM-served Qwen3-Coder-30B-A3B (FP8) on one idle A100. It finished a small real task (tests for `scripts/paper_watch.py`) in 38 s on skampere1 and 92 s on skampere2 through a tunnel, and pytest passed both times. It costs no credits. Quality is that of a solid mid-size model, not a frontier one. mercury1/2 have Pi installed, but no idle GPU to serve from. Tested Thu 10-22-2026.

## What Pi is
Open-source (MIT) terminal coding agent (`@earendil-works/pi-coding-agent`). Built-in tools: read, bash, edit, write. It asks for no approval before tool calls. Custom endpoints go in `models.json` under `$PI_CODING_AGENT_DIR` (default `~/.pi/agent`). Docs: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/models.md

## Setup that worked (skampere1, A100-80GB, driver 580)
1. Install Pi: `npm install -g --prefix ~/.local @earendil-works/pi-coding-agent` (Node 24 from the shared nvm; 20 s).
2. vLLM env: `uv venv --python 3.12 ~/uv_envs/pi_vllm && VIRTUAL_ENV=~/uv_envs/pi_vllm uv pip install vllm huggingface_hub` (vLLM 0.32.0, torch 2.13 cu130).
3. Weights: `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8` (31 GB; `HF_HOME` on /lfs, which is nearly full on skampere1, so delete after use).
4. Serve on ONE idle GPU, localhost only:
   `CUDA_VISIBLE_DEVICES=2 VLLM_USE_FLASHINFER_SAMPLER=0 vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8 --served-model-name qwen3-coder-30b --host 127.0.0.1 --port 18200 --max-model-len 65536 --gpu-memory-utilization 0.80 --enable-auto-tool-choice --tool-call-parser qwen3_coder`
   `VLLM_USE_FLASHINFER_SAMPLER=0` is needed: the flashinfer JIT picks `/usr/local/cuda-12.4` nvcc and fails (`Unknown option --compress-mode=size`). Tool calling needs `--enable-auto-tool-choice` plus the `qwen3_coder` parser.
5. `$PI_CODING_AGENT_DIR/models.json`:
   `{"providers":{"vllm":{"baseUrl":"http://127.0.0.1:18200/v1","api":"openai-completions","apiKey":"none","models":[{"id":"qwen3-coder-30b","contextWindow":65536,"maxTokens":8192}]}}}`
6. Run: `PI_CODING_AGENT_DIR=~/pi-test/agent pi -p --no-session --no-extensions --no-skills --provider vllm --model qwen3-coder-30b "<task>"`.
From another node, forward the port first: `ssh -N -L 18200:127.0.0.1:18200 skampere1.stanford.edu &`.

## Results (task: write short pytest tests for `paper_dirs` and `snapshot` in `scripts/paper_watch.py`, run them, fix until green, do not edit the source)
| Node | Pi | Model | Result |
|---|---|---|---|
| skampere1 | installed, runs | local, GPU 2 | works: 38 s, 2 tests pass; decode ~94 tok/s peak, KV cache 352k tokens |
| skampere2 | installed, runs | tunnel to skampere1 | works: 92 s, 2 tests pass (system python has no pytest; Pi found one) |
| mercury1 | installed (`pi --version` 1.4.0) | none | not run: no idle GPU, and no model reachable without a second hop |
| mercury2 | installed (1.4.0) | none | not run: all 10 GPUs busy, disk 99% full |

Quality: tests were correct and ran green, but generic (few edge cases, no failure paths). Needs a reviewer for anything subtle. No paid agent was run for comparison (no paid API calls were allowed), so "vs paid" is an expectation: a local 30B-A3B coder handles small, well-specified edits and test writing; for multi-file or ambiguous work use a paid model.

## Gotchas
- mercury nodes: driver 570 (CUDA 12.8), so the default vLLM wheel (CUDA 13 torch) fails with "driver too old". Use the cu129 build the judge-search env uses (`vllm-0.30.0+cu129`, `--torch-backend=cu129`).
- mercury A4000 has 16 GB: a 30B model needs 4-bit weights and 2 GPUs. Small coder models (7B to 14B AWQ) fit one GPU.
- Take only idle GPUs and pin them with `CUDA_VISIBLE_DEVICES`. Stop the server when done (it holds about 65 GB).
