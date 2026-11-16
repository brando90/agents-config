# Pi coding agent on a local open-weight model (SNAP nodes, FarmShare, Sherlock)

**Doc link:** <https://github.com/brando90/agents-config/blob/main/machine/pi-local-agent.md>

**TLDR:** Pi 1.4.0 installs with no sudo (`npm install -g --prefix ~/.local @earendil-works/pi-coding-agent`) and works on skampere1, skampere2, mercury1 and mercury2 against a vLLM-served Qwen3-Coder-30B-A3B (FP8) on one idle A100. One small real task (pytest for `scripts/paper_watch.py`) took 38 s on skampere1, 92 s on skampere2, 176 s on mercury1 and 54 s on mercury2 (the last three through a tunnel to skampere1), and the tests passed on every node. No credits used. skampere3 was not tested. Tested Thu 10-22-2026. FarmShare and Sherlock (added Mon 11-16-2026, see the last section): Pi installs there with no sudo and works against a local Qwen3-4B-Instruct-2507 served by vLLM in a GPU session or job; FarmShare repaired a small bug and passed its test, Sherlock ran Pi on 256 VeriBench tasks (0 compiled, a model limit).

This is the SNAP-side, vLLM-served recipe. The Mac-side free local route (`pi-local`, Ollama) and the shared `pi` configuration sync are documented in [`../config/pi/README.md`](../config/pi/README.md) and [`../skills/pi-local-herdr/SKILL.md`](../skills/pi-local-herdr/SKILL.md); this recipe uses its own `PI_CODING_AGENT_DIR` and does not change those. Follow [GPU selection](snap.md#choose-gpus-for-new-work) before starting the server.

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

## FarmShare and Sherlock (tested Oct 22 to Nov 16, 2026; model Qwen3-4B-Instruct-2507, vLLM, no paid API)
Both clusters have no always-on GPU, so the model is served inside a GPU session or job and Pi runs on the same node. Pi is 1.4.0 on both.

| Cluster | Install | Result |
|---|---|---|
| FarmShare | Nodes have no Node.js: unpack the official Node 24 tarball into `~/.local` (`--strip-components=1`), then `npm install -g --prefix ~/.local --ignore-scripts @earendil-works/pi-coding-agent` (13 s) | works: on one L40S (JupyterLab "Allocate a GPU", Large, 2 h, queue wait about 13 min) vLLM was up in about 170 s and Pi fixed `a - b` to `a + b` in a small `calc.py`; the test passed (exit 0) |
| Sherlock | `module load nodejs/24.13.0` (loaded by default), then the same `npm install` (18 s); `pi` lands in `~/.local/bin` | works: in a Slurm GPU job on one L40S (node sh04-01n10, vLLM from an Apptainer image) Pi wrote a solution file for 242 of 256 VeriBench Tiny256 tasks in 42 min with 16 tasks at a time; 0 of 256 compiled in Lean, which is the 4B model's Lean, not the setup (3 known-good files pass the same grader) |

FarmShare recipe: a script that installs Node and Pi, downloads the model with `huggingface_hub` into `~/pi_test/models`, starts vLLM on the session GPU (`--enable-auto-tool-choice --tool-call-parser hermes`, `--max-model-len 16384`), writes `models.json` and runs one task. Run it inside a JupyterLab terminal started with "Allocate a GPU", then cancel the session.

Sherlock recipe: weights under `$SCRATCH`, a `gpu` job pinned with `-C "GPU_SKU:L40S|GPU_SKU:H100_SXM5"` (the `dev` partition's GPU is a 5.8 GiB MIG slice, too small for vLLM), vLLM in Apptainer on 127.0.0.1, then Pi against it. The GPU queue wait was hours, so submit one job and use it for the whole task; no filler jobs.

Sherlock gotchas that cost three failed runs (Pi in `-p` mode prints nothing when vLLM answers 400, so check the vLLM log):
- vLLM 0.30 rejected Pi's default request fields. Add to the provider in `models.json`: `"compat":{"supportsStore":false,"supportsDeveloperRole":false,"supportsReasoningEffort":false,"supportsUsageInStreaming":false,"maxTokensField":"max_tokens"}`.
- With vLLM at its default `--max-model-len 16384`, Pi asked for `max_tokens` 16384 on top of the prompt, so the request exceeded the context and got a 400. Serve with `--max-model-len 32768` and set the model entry to `"contextWindow":32768,"maxTokens":4096`. This config is the one that ran the 256 tasks.
- Put Lean's folder on `PATH` if a job also compiles Lean.

Not tested: quality against a paid agent on these clusters (no paid agent was run), and larger coder models (the 30B model above needs an A100-class GPU or two). Qwen3-4B writes simple fixes but, per the 256-task run, its Lean is poor, so use it as a fallback for small edits.

## Same Pi setup on every node (Thu 10-22-2026)
Reference node: skampere1. All seven (skampere1, skampere2, skampere3, mercury1, mercury2, Sherlock, FarmShare) have Pi 1.4.0, rg 15.2.0, gh 2.103.0, node, claude, codex and `git credential.helper=store`, in bash; FarmShare zsh was fixed with `~/.zshenv` that adds `~/.local/bin` to PATH. Each SNAP node has its own local home, so every tool is installed per node.

Recipe on a SNAP node, no sudo: put the shared Node 24 on PATH (`/dfs/scratch0/brando9/.nvm/versions/node/v24.14.0/bin`), run `npm install -g --prefix ~/.local --ignore-scripts @earendil-works/pi-coding-agent@1.4.0`, then copy `~/.pi/agent/models.json` and `settings.json` from skampere1 (mode 600; they hold the local-endpoint key, never print or paste them), plus `fd` and `rg`. Check: `bash -lc 'pi --version'`.

- The `snap-qwen` provider (127.0.0.1:18127) exists only where a vLLM is up; Sherlock and FarmShare use the per-job `vllm` provider above.
- Claude Code needs its postinstall: install it WITHOUT `--ignore-scripts` (with it: "claude native binary not installed"). Pi and codex are fine with it.
- Not the same everywhere: `gh` is logged in only on skampere1/2/3; mercury tmux is 3.0a (OS).
- Not tested: the CPU servers (rambo, trinity, furiosa, madmax); they are Slurm-gated.

## Herdr on the clusters (tested Thu 10-22-2026)
Herdr 0.9.5, installed per machine with its official script (`curl -fsSL https://herdr.dev/install.sh | sh`), lands in `~/.local/bin`, no sudo; works on Sherlock's glibc 2.17 and FarmShare's 2.39. In non-interactive shells run `export PATH=$HOME/.local/bin:$PATH` first. skampere1, skampere2, mercury1, mercury2, Sherlock and FarmShare each ran `herdr server` and answered `herdr status` (endpoint compatible: yes) and `herdr api snapshot`.

- Start: `nohup setsid herdr server > server.log 2>&1 < /dev/null &`; stop: `herdr server stop`. Servers do not survive a node reboot or a session end (FarmShare's ran inside a JupyterLab session that was then cancelled).
- Sherlock login nodes are only a control point; jobs go through Slurm.
- From the Mac each machine needs an ssh Host entry, then `herdr machine add <label>` and `herdr machine status`; reconnect when Duo or the Kerberos ticket lapses.
- As of 10-23-2026 the Mac-to-Sherlock and Mac-to-FarmShare profiles still failed at authentication; see [herdr-stanford-access.md](herdr-stanford-access.md). Not verified: whether a saved profile forwards to the cluster servers from the Mac.

## How this page ages
Model quality notes are dated 10-22-2026 and 11-16-2026 (Qwen3-Coder-30B-A3B, Qwen3-4B). Versions (Pi 1.4.0, Herdr 0.9.5, vLLM 0.30 to 0.32) change fast; re-check flags before reuse. Google Doc copy: <https://docs.google.com/document/d/1Az0APH7bTGWycBBoiwZMRwuXslTbdj3mnJ0qiFfFl9o/edit>.
