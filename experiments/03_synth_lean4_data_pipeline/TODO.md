# Synthetic Lean 4 Pipeline — TODOs

**TLDR:** Punch list to take the [`PLAN.md`](./PLAN.md) from spec to a 10k-record HF dataset and a fine-tuned OSS coder LM. Phases mirror PLAN.md.

## Phase 0 — Plan + scaffolding (today)

- [x] **0.1** Write [`PLAN.md`](./PLAN.md) — vision, scope, Allen-key constraint, pipeline arch, prompt strategy, storage, hardware, phases, open questions.
- [x] **0.2** Stand up `prompts/` directory with versioning discipline ([`prompts/README.md`](./prompts/README.md)).
- [x] **0.3** Snapshot Eshaan's prompt as [`prompts/v0_eshaan_initial.md`](./prompts/v0_eshaan_initial.md) with provenance frontmatter.
- [x] **0.4** Push to `main` so the rest of the team (and other agents) can pick it up.

## Phase 1 — Driver script (~2 days)

- [ ] **1.1** Adapt `~/veribench/experiments/35_vb_x_harbor/adapter/alphaapollo_agent.py` into an off-Harbor driver `scripts/run_pipeline.py` that:
  - reads the active prompt via `prompts/active.md` symlink
  - takes a `--source-dataset` arg (default `bigcode/the-stack` Python subset)
  - takes a `--model` arg (default `gemini-3-flash-preview` for dry-runs)
  - writes records to `data/v0/shard-<n>.jsonl` (local) AND mirrors to `~/dfs/scratch0/brando9/synth_lean4/v0/`
  - logs which prompt-version + model + commit SHA produced each record
- [ ] **1.2** Wire the Lean validation gates as a separate module `scripts/validate.py`:
  - `lake env lean <file>` for translation correctness
  - `gcc -o test && ./test` for C tests / `python <file>` for Py tests
  - `lake env lean <theorem_file>` for proofs (max 5 retries with feedback per Eshaan's spec)
  - downgrade to `sorry` + flag `proof_incomplete: true` on persistent failure
- [ ] **1.3** Add `prompts/active.md` symlink → `v0_eshaan_initial.md`.
- [ ] **1.4** Wire `huggingface-cli login` via `~/keys/master_hf_token.txt`; verify `datasets.Dataset.push_to_hub` works on a dummy 5-row dataset.

## Phase 2 — Dry-run on 5 toy programs (~3 days; within Allen-key scope)

- [ ] **2.1** Hand-pick 5 small Python programs that exercise different Lean idioms: `gcd`, `is_prime`, `binary_search`, `fizzbuzz`, `merge_sort`.
- [ ] **2.2** Run `scripts/run_pipeline.py --model gemini-3-flash-preview --source toy --n 5` end-to-end on the local Mac (so we can tail logs interactively).
- [ ] **2.3** Verify: 5 Lean files compile, ≥1 theorem per file is non-trivial (not `native_decide` on a literal), Python and Lean tests agree on canned inputs.
- [ ] **2.4** Push the 5-record dataset to `<org>/veribench-synth-py-lean4-dryrun` (private) and verify `load_dataset(...)` round-trips.
- [ ] **2.5** Demo the round-trip in `#emb` Discord with a screenshot — invites Eshaan / team feedback before scaling.

## Phase 3 — 1k batch with Allen sign-off (~1 week; **REQUIRES ALLEN APPROVAL**)

- [ ] **3.1** **👤 Brando: ping Allen** with the draft message in [`PLAN.md`](./PLAN.md) § Open Q1. Wait for explicit "yes / no / modify scope".
- [ ] **3.2** If yes → run `scripts/run_pipeline.py --model gemini-3-pro-preview --source the-stack-py --license MIT,Apache-2.0,BSD --n 1000` on one node, serial.
- [ ] **3.3** Push to `<org>/veribench-synth-py-lean4-v0` (public). License: Apache-2.0.
- [ ] **3.4** Spot-check 30 records by hand for theorem quality + translation faithfulness.
- [ ] **3.5** Failure analysis: of the rejected 1k, what's the modal failure mode? (compile? proof? test mismatch?) Update prompt → `prompts/v1_<targeted_fix>.md`.

## Phase 4 — Scale to 10k Py + 10k C (~2 weeks)

- [ ] **4.1** Confirm the 3-server hostnames (PLAN.md Open Q3); add SSH config entries.
- [ ] **4.2** One Gemini model per node (one of `gemini-3-flash-preview`, `gemini-3-pro-preview`, `gemini-3.1-pro-preview`); each node serial-per-model per Allen rule.
- [ ] **4.3** Add C-language path: source from `bigcode/the-stack` C subset; pre-filter rules per Eshaan's spec (skip malloc/FILE\*/inline asm/varargs/fnptrs).
- [ ] **4.4** Heartbeat to OpenClaw `openclaw-ops` Telegram channel every 30 min: `[node-X] gen run alive — accepted=N rejected=M elapsed=H:MM`.
- [ ] **4.5** Push final dataset to `<org>/veribench-synth-py-lean4-v0` and `<org>/veribench-synth-c-lean4-v0` (separate datasets, easier to filter).

## Phase 5 — Fine-tune + eval (~3 weeks)

- [ ] **5.1** Pick model per PLAN.md Open Q4 — default Qwen2.5-Coder-7B.
- [ ] **5.2** SFT on accepted records (filter to compiler-clean + theorem-non-trivial). Mix C and Python in a single training set.
- [ ] **5.3** Evaluate on VeriBench held-out set (the official benchmark, not the training corpus). Compare vs base Qwen2.5-Coder-7B and vs `gemini-3-pro-preview` directly.
- [ ] **5.4** Publish model + checkpoints to HF model hub: `<org>/veribench-coder-7b-v0`. Model card explains: data source, license, training recipe, eval numbers, NOT framed as distillation (per PLAN.md § Why This Isn't Distillation).
- [ ] **5.5** Write up results — short blog post or arXiv preprint, depending on numbers.

## Hygiene / blocking

- [ ] **H.1** Verify Allen Gemini key still works before Phase 2: `python ~/veribench/scripts/test_gemini_key.py --all`. If 401 → ping Allen.
- [ ] **H.2** Add a `.gitignore` to this experiment dir for `data/`, `*.log`, and any local shard files (HF dataset is the source of truth, not git).
- [ ] **H.3** Add the experiment to `~/agents-config/experiments/` parent README / index if one exists.
- [ ] **H.4** Watch for Gemini-3 model deprecation — preview models can be retired with little notice. If Allen rotates the key or swaps allowed models, update `prompts/v0` frontmatter `model_tested` field.

## Open questions to answer in PLAN.md (mirror)

See [`PLAN.md`](./PLAN.md) § Open Questions for the canonical list. Brando-only answers needed:

- [ ] Q1 Allen sign-off plan + draft message
- [ ] Q2 HF org (`StanfordAILean` vs `brando90`)
- [ ] Q3 3-server hostnames
- [ ] Q4 OSS coder LM choice (Qwen2.5-Coder-7B default)
- [ ] Q5 Initial corpus license filter (permissive-only?)
- [ ] Q6 Discord channel for status updates
