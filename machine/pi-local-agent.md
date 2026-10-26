# Pi coding agent on a local open-weight model (SNAP nodes)

**Doc link:** <https://github.com/brando90/agents-config/blob/main/machine/pi-local-agent.md>

**TLDR:** Pi 1.4.0 installs with no sudo (`npm install -g --prefix ~/.local @earendil-works/pi-coding-agent`) and works on skampere1, skampere2, mercury1 and mercury2 against a vLLM-served Qwen3-Coder-30B-A3B (FP8) on one idle A100. One small real task (pytest for `scripts/paper_watch.py`) took 38 s on skampere1, 92 s on skampere2, 176 s on mercury1 and 54 s on mercury2 (the last three through a tunnel to skampere1), and the tests passed on every node. No credits used. skampere3 was not tested. Tested Thu 10-22-2026.

This is the SNAP-side, vLLM-served recipe. The Mac-side free local route (`pi-local`, Ollama) and the shared `pi` configuration sync are documented in [`../config/pi/README.md`](../config/pi/README.md) and [`../config/pi/skills/pi-local-herdr/SKILL.md`](../config/pi/skills/pi-local-herdr/SKILL.md); this recipe uses its own `PI_CODING_AGENT_DIR` and does not change those. Follow [GPU selection](snap.md#choose-gpus-for-new-work) before starting the server.

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
| skampere1 | 1.4.0 | local, GPU 2 | works: 38 s, 2 tests pass; decode up to ~94 tok/s, KV cache 352k tokens |
| skampere2 | 1.4.0 | tunnel to skampere1 | works: 92 s, 2 tests pass |
| mercury1 | 1.4.0 | tunnel to skampere1 | works: 176 s, 2 tests pass (node load average ~115, so slow) |
| mercury2 | 1.4.0 | tunnel to skampere1 | works: 54 s, 2 tests pass |
| skampere3 | not installed | none | not tested: outside the stored login, no idle GPU |

Tunnel from a node: `ssh -N -L 18200:127.0.0.1:18200 skampere1.stanford.edu &`, closed after each run. Times are wall clock for the whole agent run including the model; the model sits on skampere1 either way, so differences come from node load and tunnel latency.

Quality: the tests were correct and ran green on every node (re-run with pytest in a fresh venv), but generic: few edge cases, no failure paths, and one run's tests were looser than the others. A reviewer is needed for anything subtle. "Vs a paid agent" is an expectation, not a measurement (no paid agent was run): a local 30B-A3B coder handles small, well-specified edits and test writing; use a paid model for multi-file or ambiguous work.

## Gotchas
- mercury nodes: driver 570 (CUDA 12.8), so the default vLLM wheel (CUDA 13 torch) fails with "driver too old". Use the cu129 build the judge-search env uses (`vllm-0.30.0+cu129`, `--torch-backend=cu129`).
- mercury A4000 has 16 GB: a 30B model needs 4-bit weights and 2 GPUs. Small coder models (7B to 14B AWQ) fit one GPU.
- Take only idle GPUs and pin them with `CUDA_VISIBLE_DEVICES`. Stop the server when done (it holds about 65 GB). The test server on skampere1 GPU 2 and its 38 GB of weights and caches were removed after the tests.
- System python on mercury1 is 3.8 and breaks pytest; make a venv (`uv venv --python 3.12 vt && uv pip install pytest`).
