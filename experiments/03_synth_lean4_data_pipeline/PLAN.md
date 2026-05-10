# Synthetic Lean 4 Data Pipeline for VeriBench

**TLDR:** Generate validated Python/C → Lean 4 translations at scale by routing open-source code through a Gemini-driven autoformalization pipeline (compiler-checked, theorem-augmented), publish the dataset to Hugging Face, then fine-tune an open-source coder LM. Reuses VeriBench's existing `alphaapollo_agent.py` for the agent loop. **Allen-key constraint: VeriBench scope only — explicit Allen sign-off required before the first non-trivial batch run.**

---

## Vision (long-term)

Eventually translate large swaths of the world's open-source code into Lean 4 with verified properties — turning unverified codebases into machine-checkable formal models. This is multi-quarter; this experiment is the first credible end-to-end run.

## Scope (this experiment, MVP)

- Single corpus, single language, single model: ~1k Python functions from `bigcode/the-stack` → Lean 4 via `gemini-3-pro-preview`.
- Validate end-to-end: Lean compiles, theorems are non-trivial, Python and Lean tests agree.
- Published HF dataset: `<org>/veribench-synth-py-lean4-v0` (org TBD — see Open Question 2).
- Smoke fine-tune: train a small OSS coder LM (e.g. Qwen2.5-Coder-7B) on accepted records to confirm the data is useful; full training in Phase 5.

This is **not framed as distillation** — output is filtered by a deterministic Lean compiler, so the trained model learns from compiler-validated translations that happen to originate from Gemini, not Gemini's writing style. We don't use the word "distillation" externally.

---

## Hard Constraint — Allen Gemini Key (READ FIRST)

`~/keys/gemini_allen_key.txt` is on loan from Allen for **VeriBench evaluations only** per `~/keys/readme_gemini.md`. Synthetic-data generation is not strictly an "evaluation" — it's a translation-then-validate workflow whose output trains a model that VeriBench then evaluates. **This is borderline within scope; we get explicit Allen sign-off before the first non-trivial batch run.** Until then we can:

- Read the README again
- Wire the pipeline + dry-run with `gemini-3-flash-preview` on 5 toy programs (well within the eval scope by call-volume)
- Push code, prompts, infra to GitHub

Hard rules (per `readme_gemini.md`):

- One model at a time per host; no parallel runs across the three nodes hitting the same key
- 401/403 → don't retry, ping Allen
- 429 → back off, serialize harder
- Never paste the key into chats, logs, screenshots, PRs
- Never share with other agents or services
- Allowed models only: `gemini-3.1-pro-preview`, `gemini-3-pro-preview`, `gemini-3-flash-preview`

If Allen says no → fall back to a paid Google AI Studio key on Brando's account, or a different model provider. The pipeline architecture is provider-agnostic.

---

## Pipeline Architecture

```
┌────────────────┐    ┌─────────────────┐    ┌────────────────────┐
│ Source Corpus  │ →  │ Filter + Topo   │ →  │ Per-function       │
│ bigcode/the-   │    │ sort callgraph  │    │ formalization      │
│ stack (Py/C)   │    │ (skip OS/state) │    │ (Gemini agent loop)│
└────────────────┘    └─────────────────┘    └─────────┬──────────┘
                                                       │
                                                       ▼
                                             ┌────────────────────┐
                                             │ Validation gates   │
                                             │ 1. lake env lean   │
                                             │ 2. native_decide   │
                                             │ 3. Py/C unit tests │
                                             │ 4. Theorem proofs  │
                                             └─────────┬──────────┘
                                                       │
                                       ┌───────────────┴───────────────┐
                                       │                               │
                                       ▼                               ▼
                                ┌──────────────┐             ┌────────────────┐
                                │ Accepted     │             │ Rejected       │
                                │ → HF dataset │             │ → curated bank │
                                │ (compiles +  │             │ for "hard"     │
                                │  proofs OK)  │             │ examples       │
                                └──────────────┘             └────────────────┘
```

**Per-function record schema** (verbatim from Eshaan's prompt — preserve for portability):

```json
{
  "language": "Python | C",
  "source": "<original function text>",
  "lean_translation": "<Lean 4 functional + imperative impl>",
  "tests": "<original-language test harness, complete file>",
  "lean_tests": "<Lean #eval / #check tests>",
  "theorems": [{"name": "...", "statement": "...", "proof": "..."}],
  "deps_fully_translated": ["callee_a", "callee_b"],
  "axiomatized_deps": [{"name": "callee_c", "lean_axiom": "..."}],
  "skip_reason": null
}
```

---

## Reusable Code

`~/veribench/experiments/35_vb_x_harbor/adapter/alphaapollo_agent.py` is the canonical agent we adapt:

- Already supports Gemini via OpenAI-compatible Base URL (`https://generativelanguage.googleapis.com/v1beta/openai/`)
- Already does propose → judge (`lake env lean`) → update with `EvolvingMemory` (score-ordered candidate history)
- Already extracts code from fenced blocks, manages retries, handles model-call failures gracefully
- Has both Anthropic and OpenAI-compatible code paths

**Adapter for this experiment:** wrap `AlphaApolloAgent` in a non-Harbor driver (`scripts/run_pipeline.py`) that:

1. Streams candidates from a HF source dataset (`bigcode/the-stack`)
2. Pre-filters per Eshaan's skip rules (OS calls, malloc, varargs, fnptrs, …)
3. Builds the per-function autoformalization instruction
4. Invokes the agent with VeriBench's `lean_project` mounted (`~/veribench/lean_project/` or its container equivalent)
5. Parses the Lean output, runs the validation gates
6. Writes the JSON record to a local `data/v0/` shard
7. Periodically pushes shards to the HF dataset hub via `datasets.Dataset.push_to_hub`

---

## Prompt Strategy

- **`prompts/v0_eshaan_initial.md`** — verbatim copy of Eshaan's `~/lean-ebm/experiments/claude_prompt.md` plus a frontmatter provenance block. This is the living source for the system prompt.
- **Prompt-change log discipline (per Eshaan 2026-05-10 Discord ask, 1:47pm):** every prompt revision lives in `prompts/vN_<short_name>.md` with a YAML frontmatter:

  ```yaml
  ---
  parent: vN-1
  date: YYYY-MM-DD
  author: <agent or human>
  agentic_cli: <claude-code | codex | clauded | gemini | ...>
  model_tested: <claude-sonnet-4-6 | gemini-3-pro-preview | ...>
  problem: "What was wrong with vN-1?"
  rationale: "Why this change fixes it."
  diff_summary: "1-line summary of what changed."
  ---
  ```

The 1:47pm message specifically asks: document reasons + which agentic CLI / model the prompt was tested with. We do this in the frontmatter so future readers (and other agents) understand *why* a prompt looks the way it does, not just *what* it says.

See [`prompts/README.md`](./prompts/README.md) for the full discipline.

---

## Storage

**Hugging Face Datasets** — free, public, training-friendly, push-easy.

Per Eshaan's prompt, the long-term canonical home is `StanfordAILean/c-py-dataset`. For this MVP (versioned, separable from the long-term home so we can iterate without polluting the canonical dataset), we publish to:

- `<org>/veribench-synth-py-lean4-v0` ← MVP, this experiment (org TBD per Open Q2)
- Eventually merged into / promoted to `StanfordAILean/c-py-dataset` (or kept as a sibling shard)

**Auth:** `~/keys/master_hf_token.txt` (already present). Push via `datasets` library + `push_to_hub`. License: Apache-2.0. Visibility: public.

**Backup:** every record also written to `~/dfs/scratch0/brando9/synth_lean4/v0/` on the SNAP cluster (DFS, persists across nodes, survives HF outages).

**Why HF and not e.g. an S3 bucket:** HF is free, public, training-loader-native (`load_dataset(...)` works on every training framework), versioned via git-LFS, and aligns with how Brando's other datasets are distributed. No new infra to maintain.

---

## Hardware

3× H200/B200-class servers (Stanford STAIR / Koyejo lab — exact hostnames TBD per Open Q3; `mercury2` is currently the only one documented in `~/agents-config/machine/snap.md`).

- **Phase 4 (data gen):** run the pipeline at scale, one Gemini model per node — `gemini-3-flash-preview` on node A, `gemini-3-pro-preview` on node B, `gemini-3.1-pro-preview` on node C. Three models, three concurrent runs, no within-model parallelism (per Allen's serial-per-model rule).
- **Phase 5 (training):** fine-tune Qwen2.5-Coder-7B (or DeepSeek-Coder-V2 — see Open Q4) on accepted records. With 3× H200 / B200 we can comfortably full-fine-tune a 7B model; for larger models (32B+) use one node + LoRA / QLoRA.

---

## Phases

| Phase | Deliverable | ETA | Owner | Allen sign-off |
|---|---|---|---|---|
| 0 | This plan + `prompts/v0_eshaan_initial.md` + `TODO.md` committed | today | CC | no |
| 1 | `scripts/run_pipeline.py` driver (adapt `alphaapollo_agent.py` off-Harbor) | +2d | CC + Brando | no |
| 2 | Dry-run on 5 toy Python programs with `gemini-3-flash-preview` — validate Lean compiles, theorem proofs land, HF push works | +3d | CC | dry-run within eval scope (very low call volume) |
| 3 | Allen sign-off → batch run on 1k Python from the-stack with `gemini-3-pro-preview` | +1w | Brando | **YES — REQUIRED** |
| 4 | Scale to 10k Python + 10k C, `gemini-3.1-pro-preview` for hardest cases | +2w | CC | implicit if Phase 3 OK |
| 5 | Fine-tune Qwen2.5-Coder-7B on accepted records, eval on VeriBench held-out | +3w | Brando | n/a |

---

## Open Questions (Brando — please answer)

1. **Allen sign-off plan** — who pings Allen, when, and what's our exact ask? Suggested draft message:

   > Hey Allen — we're building a synth-data pipeline that uses your Gemini key to translate open-source Python/C to Lean 4. Output goes to a public HF dataset and is used to train an open-source coder model that we then evaluate on VeriBench. The Lean compiler verifies every record before it lands in the dataset. We'd run ~10k generation calls total over a week, serial-per-model per the README. Is this within the spirit of the key's intended VeriBench scope, or off-label?

2. **HF org** — `StanfordAILean` (matches Eshaan's prompt) or `brando90`? Need write access on `StanfordAILean` if that's the choice.
3. **3-server hostnames** — confirm: are these `mercury2`, `mercury1`, `mercury3`? Or different names? `~/agents-config/machine/snap.md` only documents `mercury2`. We need at least the SSH config entries before we can dispatch.
4. **OSS coder LM choice** — Qwen2.5-Coder-7B (default), DeepSeek-Coder-V2-Lite, Qwen2.5-Coder-32B + LoRA, or something else?
5. **Initial corpus filter** — start with permissive-licensed Python only (MIT/Apache/BSD) to keep dataset clean? `bigcode/the-stack` already exposes per-file license metadata.
6. **Discord channel for status updates** — `#emb` (per Eshaan thread), `#free-energy`, or new dedicated channel?

---

## References

- **Eshaan's initial prompt:** `~/lean-ebm/experiments/claude_prompt.md` → copied verbatim to [`prompts/v0_eshaan_initial.md`](./prompts/v0_eshaan_initial.md)
- **Reusable agent:** `~/veribench/experiments/35_vb_x_harbor/adapter/alphaapollo_agent.py`
- **Gemini key invocation pattern:** `~/veribench/scripts/test_gemini_key.py`
- **Gemini key constraints:** `~/keys/readme_gemini.md`
- **VeriBench format spec:** `~/veribench/README.md`
- **Discord context:**
  - `#emb` (Stanford-AI-for-LEAN — Eshaan's thread + 2026-05-10 1:47pm prompt-change-log ask)
  - `#free-energy` (Brando's `free-energy` repo — long-term post-transformer architecture context, separate from this experiment)
- **Source corpus candidate:** [`bigcode/the-stack`](https://huggingface.co/datasets/bigcode/the-stack)
- **HF target dataset (long-term canonical):** [`StanfordAILean/c-py-dataset`](https://huggingface.co/datasets/StanfordAILean/c-py-dataset)
- **HF target dataset (this MVP):** `<org>/veribench-synth-py-lean4-v0` (org TBD)
- **lean-ebm sibling experiment:** `~/lean-ebm/experiments/03_synth_data_generation/` (different angle — EBM-driven synth data; we share the prompt but not the architecture)
