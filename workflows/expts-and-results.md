# Workflow: Experiments & Results

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/expts-and-results.md>

**TLDR:** The canonical experiment-folder convention for this account:
`experiments/<NN>_<name>/` with mandatory `README.md`, versioned
sub-experiments, experiment-folder Markdown reports, optional explicitly requested
Weights & Biases (W&B) reporting, GPU rules, and narrowly
scoped completion notifications for user-triggered big/mega QA or explicitly
tracked tasks only. Includes the canonical templates
for the agent prompt (`cc.md` — must open with `**TLDR:**`) and
`PROTOCOL.md` (must open with `## Scientific question (locked)`).
Read end-to-end before starting, opening, or reviewing any experiment dir.

---

## Requirements Checklist (quick reference)

Every **active experiment** must have the following; deferred proposals use the lightweight [ideas convention](#optional-research-ideas) instead:

- [ ] **Numbered directory** — `experiments/<NN>_<name>/` (sequential numbering, descriptive name), or the user-authorized `experiments/ideas/<name>/` home
- [ ] **Data and code together** — all experiment-specific material under its canonical home; shared-code/external-storage exceptions linked in its README ([details](#keep-data-and-code-together))
- [ ] **Experiment-index row** — canonical home, setup/goal and current status in the project's existing index (normally `experiments/README.md`; ideas use their own index)
- [ ] **README.md at root** — goal/hypothesis, decision criterion, structure tree, method, dependencies, status table
- [ ] **Versioned sub-experiments** — `expt_v1/`, `expt_v2/`, … each self-contained with own agent prompt, scripts, and `results/` dir
- [ ] **Full-set evaluation contract (solver/agent evaluations)** — frozen model × task × seed/repetition manifest, bounded completion/continuation procedure, durable execution, per-cell receipts and full-denominator reporting ([details](#uninterrupted-evaluation-of-the-full-declared-set))
- [ ] **Agent prompt per version** — `cc.md` or `agents_vN.md` (paste-into-agent runnable prompt)
- [ ] **Experiment-folder Markdown report** — the primary and sufficient reporting deliverable; save a `.md` report in the canonical experiment folder, normally `expt_vN/results/results_summary_<MM-DD-YYYY__HH-MM-SS>.md`, with findings, config, metrics, limitations, and relevant local artifact links
- [ ] **Stable `results.md` at experiment root** — created at launch, updated as meaningful evidence arrives, latest outcome + TLDRs and links to timestamped summaries (see § Results Storage)
- [ ] **Dated resumable checkpoint for qualifying runs** — `CKPT_<task>.md` (CKPT means checkpoint), with real creation/update timestamps and the next resume step; apply [Trigger Rule 44](../INDEX_RULES.md) for long or dispatched runs
- [ ] **QA review** — cross-agent correctness review before committing results (per `qa-correctness.md`)
- [ ] **GPU cleanup** — if the run used GPUs: kill zombie processes, verify GPUs freed, report `nvidia-smi` state after completion

Paper-bound experiments **must also** have:
- [ ] **Writing draft** — `writing.tex` at experiment root (mark `% Status: DRAFT`)

Encouraged (not mandatory):
- [ ] **todo.md** — open tasks / next steps for the experiment
- [ ] **results/paper_table.tex** — LaTeX table ready to `\input{}` into the paper

---

## Starting or Continuing an Experiment

Apply these conventions automatically when starting or continuing an authorized experiment; do not wait for a documentation reminder. Read the project's experiment index and a matching recent experiment first, then reuse its filenames, version structure and templates while meeting the requirements below. Ordinary edits, short lookups and research conversations alone do not need experiment folders.

For a newly authorized distinct experiment, default to a numbered setup-descriptive home directly under `experiments/`. Check existing and archived homes, reserved index entries, active branches/worktrees and known owners before choosing the next available number; coordinate overlapping work. Honor exact user numbers, labels and names, but do not silently repurpose an occupied number. Reuse the matching canonical home for a continuation, with a new version when the setup changes. Add or update its row in the existing project experiment index (normally `experiments/README.md`). Preserve the optional-ideas exception below, archival policy and frozen/running private paths under [Trigger Rule 39](../INDEX_RULES.md).

State the goal/hypothesis and decision criterion concisely in the existing README/protocol, following [Trigger Rule 50](../INDEX_RULES.md): name the central uncertainty, cheapest sufficient test, evidence for continuing/redirecting/stopping and test bound before measuring. Record inputs and the protocol/runbook using the formats below. At launch create live `results.md`, then update it as meaningful evidence arrives ([Results Storage](#results-storage), Rule 37); for qualifying long or dispatched runs also maintain the dated resumable checkpoint (Rule 44). Link these records rather than duplicating their contents or adding per-step approval gates; existing resource, review and permission requirements still apply.

## Uninterrupted Evaluation of the Full Declared Set

**Current user rule (Brando, 09-20-2026): every solver or agent evaluation must execute the full prespecified procedure for every file, task, question and data point in its declared set.** This applies to every model, provider, harness and project, including every declared model × task × seed/repetition cell. A smoke test, one completed task or a clean subset is not a completed evaluation. This is an execution obligation within declared bounds, not a guarantee against hardware/provider failures or a requirement for successful answers or nonzero scores.

Before measured calls, freeze the complete input/task manifest and expected cell count, input hashes, model/runtime/settings, prompts, tools, scoring rules and output contract. State per-cell and whole-run time, token, call, tool, resource and spend limits; fix continuation triggers, maximum count, session/state handling, completion checks and terminal conditions up front. Verify that **every initial and continuation prompt** includes the [solver completion reminder](#solver-completion-reminder). Preserve existing frozen runs: adding or changing this reminder or a continuation policy creates a separately identified prospective condition.

The orchestrator must preflight the actual execution path: permissions, tool access, context/output capacity, authentication/funding, container lifecycle, final-file capture and compiler/scorer availability. Check nested host/client/container/scheduler/watchdog timeouts so infrastructure cannot accidentally truncate an allowed model attempt. Reserve enough overall allocation for the full declared set at its permitted per-cell budgets plus setup, capture, scoring and cleanup; use a durable planned batch schedule when one allocation cannot hold it. Keep cumulative accounting across setup failures and handoffs. A prospective infrastructure allowance change must be authorized, bounded and recorded before affected admissions; it cannot silently enlarge scientific budgets or reset spent time/calls.

Use a persistent execution owner, durable per-cell ledger/checkpoints and a verified monitor that survive coordinator disconnects, context changes and laptop sleep. Do not stop healthy admitted work because the coordinator turn ends, progress is slow, the first result looks good/bad, a final model message appears, or a GPU looks idle during tool work. Let each cell follow its fixed completion/continuation procedure through its declared terminal condition, then continue the remaining manifest. Respect explicit user cancellation, real safety/resource limits and prespecified abort rules; record the exact stop reason and all affected/unattempted cells. Do not substitute a different measured model or settings to finish a row, add result-dependent continuations, or retry indefinitely.

### Solver Completion Reminder

Include this instruction in **every measured solver/agent initial prompt and every continuation prompt**, alongside that cell's actual task, output paths and declared limits. Adapt only inapplicable output/check names before freezing the condition; do not expose withheld reference answers or private scoring inputs.

> Solve the entire assigned task, including every required file, question and subtask. Produce the complete required deliverable in the specified output location or response format; an outline, partial draft, progress report or claim of completion is not a substitute. Write/save the output, inspect the actual saved artifact or final response, and run the allowed checks, tests or compilation required by the task. Within the declared time, token, call and tool limits, continue working and fixing errors until the requirements are met or a declared terminal condition is reached. Follow the fixed continuation procedure without resetting budgets. If anything remains unresolved, preserve the best current deliverable and report the exact remaining failures and checks that did not pass; never claim success or invent verification.

Prompt text alone does not implement persistence or continuation. The orchestrator must verify the delivered prompt bytes, runtime limits, continuation behavior and finalization path; do not claim these controls exist merely because this policy says they should.

### Per-Cell Evidence and Full-Set Completion

Maintain a row for every declared cell from launch onward, including pending, running, blocked, cancelled and unattempted cells. Bind each terminal receipt to input/condition/attempt identity, actual model/settings, cumulative usage, generation/tool logs, stop reason, final output path/hash/size (or explicit missing status), and compiler/test/scorer results. Capture the actual final file after writes have stopped; independently check its required structure and recorded checks. A nonempty file, exit zero or self-reported success alone proves neither a complete answer nor a correct one.

Report execution validity, deliverable completeness and measured correctness separately. Distinguish a **clean procedure-complete attempt** (the declared procedure and finalization completed without infrastructure interruption or still-unfinished generation; correctness may fail), **budget-exhausted incomplete generation** (the declared budget ended with incomplete/missing work), and **infrastructure-interrupted execution** (the procedure was cut short by a runtime/provider/orchestration failure). Preserve native termination evidence and mixed causes instead of forcing an unsupported clean classification. A failed proof or zero score is not by itself an execution failure; unfinished generation is not clean evidence of task difficulty.

The completion gate reconciles the full manifest: every expected cell has a terminal status, finalization evidence or explicit failure/missing reason, and all required scoring stages are measured or explicitly unresolved. Report expected, attempted, terminal, clean, incomplete, interrupted, cancelled and unattempted counts. Any unattempted cell or unresolved required stage keeps the evaluation partial/blocked even if its controller has exited; terminal accounting alone is not a claim that all cells were evaluated. Keep failed, missing and interrupted rows in the declared denominator; follow the frozen missing-data/scoring rule, leaving unavailable values explicit rather than inventing zeros or dropping rows. Show any clean-subset diagnostic with its subset denominator. A complete clean matrix is a separate claim requiring all declared cells to qualify; neither that diagnostic nor one passing smoke test replaces the full-set report.

### Recovery Without Selective Reruns

Follow only recovery/continuation rules frozen before measurement within their cumulative bounds; retain each original attempt and every charge, reservation and failure. Missing deterministic capture/scoring work may be completed on preserved outputs when its identity and validity can be verified, without regenerating answers. A new retry, changed prompt/harness, extended scientific budget or other unplanned recovery needs a separately frozen and reported prospective condition. Specify its full eligible set and selection rule before new calls, independent of favorable scores; if only interrupted cells are recovered, label that population explicitly and do not present it as a new full clean matrix. Preserve original full-denominator results and disclose prior outcomes known when the new condition was designed. Never overwrite failed evidence, silently splice a best-of mixture, or claim recovery erased interruption or restored an unbiased original run.

## Keep Data and Code Together

**Default: one experiment folder owns both its data and its code** (Brando, 09-19-2026). Put all experiment-specific source snapshots/archives, raw and derived data, candidate datasets, scripts/modules, prompts, configurations, manifests, logs, results and documentation beneath its canonical home. Use `scripts/`, `data/`, `assets/`, `private/` and version folders as useful subdirectories; keep an existing sensible layout instead of renaming it for these examples. Importable code and a dataset under construction still belong to their experiment. Do not scatter them among repo-level `src/`, `scripts/`, `data/`, loose files or separate checkouts merely by file type.

For example, the VeriSoftBench (VSB) → VeriBench V2 (VBV2) construction work has the canonical home `experiments/91_lean_to_python_hopefully_unsaturated_vb/`. Its source archives, derived dataset and construction/evaluation code should be discoverable together from that folder.

Exceptions need a concrete reason and a pointer in the experiment README:

- Shared code used by multiple experiments or production stays in its established project home. Link and pin that dependency where needed; do not duplicate shared infrastructure just to make the experiment appear standalone. Move experiment code out only when real shared use warrants promotion.
- An intentionally released dataset may use the project's established data home; its construction inputs, code and experiment evidence retain their canonical experiment home and link the released version.
- Large artifacts, node-local runtime storage, reusable model caches, or licensing/access constraints may require storage outside the checkout. Keep a manifest in the experiment naming the exact path or URI, the reason, version/hash where practical, and retrieval/sync instructions. Prefer the same experiment-relative directory structure on execution hosts; retain committed, allowed metadata and progress in the canonical home.

This is a location rule, not a publication rule. Keep private/gold material ignored or access-controlled as required, and credentials in their existing secret store. Honor user moves and existing canonical homes; coordinate other owners before relocation, update live imports/configurations/links, and verify preserved contents. Frozen result paths and running checkouts remain unchanged until an appropriate coordinated move. This preference does not authorize a broad repository reorganization.

## Optional Research Ideas

Use `experiments/ideas/<descriptive_setup>/` for research whose priority or paper inclusion is uncertain. Index it in `experiments/ideas/README.md`, separate from core numbered workstreams and concluded archives. Honor explicit names such as `IDEA_00_waterfall_vs_llm_judge`; otherwise use a descriptive unnumbered name without reserving an active experiment number.

The idea's README needs a title and opening summary, execution status, paper-inclusion status, testable hypothesis, motivation/source links, predicted priority/reason, key uncertainty, minimal comparison and revisit condition. Hypotheses remain distinct from measured findings. A concise source summary is optional.

A deferred proposal marked `DEFERRED — NOT RUN` needs no version folders, scripts, prompts, live results, checkpoints, external reports or paper draft. Recording it does not launch work or resume paused work. If the user asks to run it, keep the requested ideas path and mark execution `PLANNED`, `RUNNING`, `BLOCKED` or `DONE` independently of inclusion `UNDECIDED`, `INCLUDE` or `OMIT`. All normal execution requirements below then apply, including versioned runs, live `results.md`, resumable checkpoints, proportional review and publication. Ideas are not exempt from resource or dispatch controls. A running optional study need not be moved into a core numbered home.

Check for overlap with existing workstreams before execution. If promoted to core work, coordinate the move and update indexes and prospective links while preserving provenance and scientific inputs; do not move running private checkouts or rewrite frozen evidence. Keep completed optional evidence while a live paper-inclusion decision depends on it; otherwise follow the project's archive convention. A paper draft becomes required when paper writing is commissioned, not merely because inclusion remains possible.

## Experiment Directory Structure

When the user assigns workstream labels, name the home `experiments/<NN>_<LABEL>_<descriptive_setup>/`, for example `70_E1_harbor_evals_code`. Explain each label in the project experiment index and keep one canonical root per number. Follow exact user-specified names, including pause-marker order. Otherwise put a requested pause marker after the label, for example `73_S2_PAUSED_sol_unsolved_to_astra_ultra`; the status record still controls whether work may run. Unlabelled projects keep the existing descriptive format. A naming change does not authorize a new experiment, a restart, or altered scientific inputs. Coordinate owners, update prospective consumers and check preserved contents, while leaving frozen evidence and running private paths intact; record the old-to-new map in the archive index.

Each active experiment lives under `experiments/<NN>_<name>/` or its explicitly authorized ideas home in the project repo. Every experiment **must** have a `README.md` at its root and at least one versioned sub-experiment directory.

```
experiments/<NN>_<name>/
├── README.md                   ← goal, structure, method, dependencies, status table (MANDATORY)
├── todo.md                     ← open tasks / next steps for this experiment (optional but encouraged)
├── writing.tex                 ← draft paper section for this experiment (MANDATORY for paper-bound expts)
│                                  Mark as DRAFT; do not \input{} into main paper until finalized.
│                                  Example header: % Status: DRAFT — do not include in paper_latex_and_notes/ yet
│
├── expt_v1/                    ← first iteration (self-contained)
│   ├── cc.md                   ← agent prompt (paste into Claude Code / Codex to run this version)
│   ├── run_*.sh / run_*.py     ← execution scripts
│   ├── push_to_wandb.py        ← optional helper; use only when W&B is explicitly requested
│   └── results/                ← outputs: JSONs, CSVs, plots, results_summary_<MM-DD-YYYY__HH-MM-SS>.md
│
├── expt_v2/                    ← next iteration (e.g., changed metric, added agents, new split)
│   ├── agents_v2.md            ← updated agent prompt
│   ├── run_*.sh / run_*.py
│   └── results/
│
├── adapter/                    ← data → task generation (if using Harbor)
│   ├── adapter.py
│   ├── template/               ← Dockerfile, task.toml, test.sh, solve.sh
│   └── single_call_agent.py    ← custom agent (if needed)
├── tasks/                      ← generated task dirs (one per task)
├── assets/                     ← user-attached images: photos of handwritten notes, whiteboards,
│                                  screenshots, paper figures (+ optional .md transcriptions
│                                  with the same basename). Required when a
│                                  hypothesis / experiment / prompt / issue is
│                                  created from an attached image. See
│                                  "Assets folder" below.
├── collect_scores.py           ← shared scoring script (or per-version in expt_vN/)
├── compute_correlations.py     ← correlation analysis
├── generate_plots.py           ← scatter plots + histograms
├── push_to_wandb.py            ← optional shared W&B helper; use only on explicit user request
├── results_summary/            ← optional top-level rollup summaries across versions (or legacy location)
│   ├── results_summary_MM-DD-YYYY__HH-MM-SS.md
│   └── temporary_results/      ← unverified intermediates
└── expt_results/               ← optional shared/aggregated CSVs, JSONs, plots across versions
```

### Assets folder (`assets/`)

When the user attaches an image in a prompt (handwritten note photo, whiteboard, screenshot, paper figure) and asks to save / transcribe / keep it, or asks to create a research hypothesis, experiment, prompt, or GitHub issue from it, save the original image under that hypothesis / experiment folder's `assets/` folder with a descriptive snake_case filename — never leave it only at an opaque `~/.claude/uploads/<uuid>/`, `/tmp/codex-remote-attachments/<uuid>/`, or similar upload path, which is ephemeral and meaningless across sessions and machines. Reference the saved `assets/...` path from the generated `pre_prompt.md`, `issue.md`, transcription, or README. For research hypotheses, also put a compact summary block near the top: one-sentence **Goal**, **Confidence**, **Importance**, and any **Key uncertainty**. If a transcription is requested, save a sibling `.md` with the same basename containing provenance + a `**TLDR:**`. Existing precedent: `experiments/01_toy_ebm_training/assets/{toy_ebm_notes_photo_1.jpg, ...}`. Full rule: [`INDEX_RULES.md`](../INDEX_RULES.md) Trigger Rule 28.

### Versioned Sub-Experiments (`expt_v1/`, `expt_v2/`, …)

Most experiments evolve through iterations — changed metrics, added agents, new data splits, etc. Each iteration is a **self-contained directory** with its own agent prompt, scripts, and results. This keeps iterations reproducible and avoids overwriting prior results.

- Name versions sequentially: `expt_v1/`, `expt_v2/`, …
- Each version has its own agent prompt (`cc.md`, `agents_v2.md`, etc.) — the prompt you paste into Claude Code or Codex to run that version.
- Results stay inside the version dir: `expt_v1/results/`, `expt_v2/results/`.
- The top-level `README.md` documents all versions and their status.

### Experiment README.md (mandatory)

Every experiment root **must** contain a `README.md` with:

1. **Goal/hypothesis and decision criterion** — one concise paragraph: what uncertainty this tests, why it matters and what evidence changes the next decision; link the protocol for detailed thresholds and bounds
2. **Structure** — ASCII tree of the experiment directory (keep it current)
3. **Method** — numbered steps describing the experimental procedure
4. **Dependencies** — what prior experiments, data, or API keys this needs
5. **Status table** — per-step status (`Done`, `TODO`, `In Progress`, `Blocked`)

Dates written in the README (started, updated, per-step notes, decisions) use month-day-year, `MM-DD-YYYY` ([Trigger Rule 53](../INDEX_RULES.md)); existing year-first dates and filenames stay as they are.

Example status table:
```markdown
| Step | Status | Notes |
|------|--------|-------|
| v1 agent runs | Done | 15 agents, results in expt_v1/results/ |
| v1 paper table | Done | expt_v1/results/paper_table.tex |
| v2 real eval | In Progress | new metric, 3 agents so far |
| Writing draft | TODO | writing.tex started |
```

### Agent Prompt (`cc.md`) format — MANDATORY

For measured solver/agent calls, also deliver the [solver completion reminder](#solver-completion-reminder) in every initial and continuation prompt. The orchestration prompt must enforce the entire declared evaluation manifest, not stop after one successful example.

The agent prompt (`cc.md` or `<NN>_cc.md`) is the file the human pastes into
Claude Code / Codex / Cursor to run an experiment. It must be skimmable in
under 30 seconds, otherwise the human cannot quickly verify "what does this
prompt actually do" before pasting.

**Required at the top of every `cc.md` (and every prompt file in this repo,
including workflows under `~/agents-config/workflows/`):**

1. `# <Title>` — one-line title.
2. `**TLDR:**` — 2–6 sentences. State (a) what the prompt makes the agent
   do, (b) the headline pass/fail or success criterion, (c) the deliverable
   (PR title, figure path, email recipient — whichever applies), (d) any
   load-bearing constraint the agent must not violate.
3. (Optional) one sentence pointing the agent at `~/agents-config/INDEX_RULES.md`.

Anything below the TLDR is the full prompt (scientific question, locked
protocol references, steps, manuscript update, closing/PR plan, guardrails,
identity crib). The TLDR exists so the human reading the prompt can
verify it without reading the whole document.

**Why:** A `cc.md` without a TLDR forces the human to read the whole prompt
just to confirm "is this the right one to paste". With the TLDR, the
verification is one screen.

**Required at the BOTTOM of every agent prompt file too — `cc.md`, `agents_vN.md`,
`PROMPT_*.md`, `coding_agent_prompt.md`, any paste-into-agent artifact
(INDEX_RULES.md Trigger Rule 36):**
close the prompt with a 1-2 sentence `TL;DR:` of what it does, what downstream
models/tools it invokes, and what it produces. The two ends are deliberately
different lengths: the top TLDR keeps the fuller 2-6 sentence form specified
above (it must still cover (a)-(d); INDEX_RULES.md Trigger Rule 16 explicitly
admits this longer form for prompt files); the closing one is the short skim line.
Do not shorten the top TLDR to match the bottom. This is additive to the top TLDR above, not a duplicate of
it — the human skimming the end of a long prompt gets the same one-screen
verification as the human skimming the top. Do not "deduplicate" the two.

**And when you hand the prompt to Brando, recommend a model + effort level in
your reply — never inside the prompt file** (Trigger Rule 36a). State the
rationale first, then the recommendation, chosen proportionately to the size and
risk of what the prompt does, anchored in Hard Rule 8's defaults and its
flagship-vs-regular-tier split. The prompt file is what the *agent* reads; the
model/effort call is for *Brando*, so it belongs in the chat, not the artifact.

### PROTOCOL.md format — MANDATORY for any LLM-budget-spending experiment

`PROTOCOL.md` freezes the experiment's contract **before** any expensive run
begins. It is written *prior to* seeing any results. Any deviation observed
during execution is documented in `REPORT.md` → "Open questions for
\<reviewer\>", **not** by editing `PROTOCOL.md`.

**Required sections, in order:**

1. `# Folder <NN> — PROTOCOL (LOCKED before any expensive run)` — title.
2. One short paragraph stating the freeze rule (template):

   ```
   This file freezes the protocol before any LLM-budget-spending run begins.
   It is written PRIOR to seeing any results. Any deviation observed during
   execution is documented in REPORT.md → "Open questions for <reviewer>",
   not by editing this file.
   ```

3. `## Scientific question (locked)` — **MANDATORY**. State the research
   question this experiment answers, then the operational pass/fail
   criterion. Without this section, future-you and reviewers cannot tell
   what the experiment is supposed to *prove*; everything else
   (parameters, data layout, wall-clock) is implementation detail.
4. `## Locked parameters` (or `## Locked metrics & thresholds` +
   `## Locked analysis params`) — every numeric knob that, if changed
   silently after the run, would invalidate the result. Include
   `JUDGE_REPEATS` / `n_samples`, bootstrap iters, permutation iters,
   pass/fail thresholds, primary-vs-ablation split. For solver/agent evaluations,
   include the full cell manifest and bounded completion/continuation contract
   from [the full-set rule](#uninterrupted-evaluation-of-the-full-declared-set).
5. `## Scale verification (no further normalization)` — if any inputs
   are already normalized to `[0, 1]` (judge scores, human labels
   divided by max), state it explicitly so a downstream script doesn't
   re-divide and silently break the run.
6. `## Verified data layout` (or `## Verified data schema`) — for
   Mode-A reuse experiments, name the upstream CSV / JSON columns and
   their interpretations so a future reshape doesn't rediscover them
   the hard way.
7. `## Pre-conditions for run` — env files, API keys, venv, upstream
   folders that must exist.
8. `## Estimated wall-clock` — rough order-of-magnitude per step;
   helps the agent decide whether to background a job.
9. `## Pass/fail / abort rules` — what makes the smoke test pass before
   the full run is launched; what causes a STOP-and-document during the
   full run. A smoke pass admits the declared run; it does not complete it.
   An abort preserves every affected and unattempted cell in its denominator.
10. `## Identity / contact crib (verified)` — GitHub login, email,
    key paths. The "(verified)" tag matters: drop this only after you
    have actually checked the GitHub user exists and their email is
    correct (every PR misassignment in this repo so far has been due
    to a guessed login).

Folders 06, 07, 08 in `~/cert-judge/experiments/` are reference
implementations of this template. If a section is genuinely
inapplicable, write the heading and `_(N/A; reason)_`; do not silently
omit headings.

### Experiment Writing Draft (mandatory for paper-bound experiments)

If the experiment will produce a section or subsection in a paper, keep a **draft `.tex` file** (`writing.tex` or `draft_paper_section.tex`) at the experiment root. This is where you iterate on the paper text alongside the data — not in the main paper directory.

Rules:
- Mark it `% Status: DRAFT` at the top so no one accidentally `\input{}`s it.
- Reference the experiment's prompts, proposal, and data files in `%` comments.
- When the draft is finalized, copy/adapt it into `paper_latex/` — the experiment dir keeps the historical draft.
- Follow `~/agents-config/writing/ml_research/ml_research_writing.md` for writing style.

---

## Results Storage

Report measured numerical results alongside verdicts under [Hard Rule 11](../INDEX_RULES.md#hard-rules-every-response-never-skip), including counts, split/phase, uncertainty, separate correlations and clearly distinguished raw-score variability versus aggregated-score repeatability. Label missing measurements and threshold sources; reporting does not change the locked protocol.

- **Results live inside the version dir:** `expt_v1/results/`, `expt_v2/results/`, etc. This keeps each iteration self-contained and reproducible.
- **Readable results reports:** Name the canonical reader-facing report `RESULTS_<concise_topic>.md`, for example `RESULTS_judge_validation.md` or `RESULTS_theorem_coverage.md`. The topic uses concise descriptive lowercase words separated by underscores. Keep it inside the canonical experiment or relevant phase folder; link it from the experiment README and live `results.md`. Include the document link and summary required by Trigger Rule 16, measured results and their source artifacts. Keep the report current with the latest verified evidence and clearly distinguish historical snapshots from final results.
- **Timestamped archival summaries:** For distinct immutable run snapshots, use `RESULTS_<concise_topic>_<MM-DD-YYYY__HH-MM-SS>.md` in the version results directory. Never overwrite these snapshots. The canonical readable report above stays undated; the mandatory live `results.md` ledger remains unchanged. Preserve existing frozen filenames and raw data formats. When renaming an existing report, coordinate any active writer, update live links and generators, and preserve immutable provenance paths instead of rewriting historical manifests.
- **Stable `results.md` at experiment root (mandatory):** every experiment dir keeps a `results.md` at its root — a stable filename Brando can always open to see the latest outcome without hunting through version dirs. Format (end-only, Brando 09-22-2026; overrides Rule 16's opening summary): `# Title`, headline numbers/verdict, links to the canonical `RESULTS_<concise_topic>.md` report and authoritative timestamped `expt_vN/results/RESULTS_<concise_topic>_<ts>.md` files, then a closing `**TLDR-end:**` with Hard Rule 4's `[proj: task]` tag. **Overwrite/update it on every run** (unlike timestamped summaries) — it is a pointer/rollup, not the archival record.
- **`results.md` is a LIVE document, not an end-of-run deliverable (mandatory):** create it the moment the run starts, with a `**Status:** RUNNING (started <ts>)` line, and **update it whenever a meaningful result lands** — a phase completing, a gate producing counts, a table of tiers, a score — not only when everything finishes. Each update carries a `**Last updated:** <ts>` line and, for a long run, a phase table with one row per phase (`DONE` / `IN PROGRESS` / `PENDING`) plus the numbers obtained so far. **Commit and push each meaningful update**, because an experiment whose only progress record lives on a cluster node (a `PROGRESS.md` under `/dfs/...`) is invisible to the person who asked for it: they cannot answer "what is the state of this?" without an ssh session. A long run that has produced real numbers and shows nothing in the repo is a reporting failure, however good the eventual report is.
- **Temporary results:** Unverified intermediates go in `results/temporary_results/` within the version dir. Never promoted; kept for audit trail.
- **Verification before commit:** Always run the verification checklist (in the active version's agent prompt) and QA review before committing results to the repo.
- **Top-level rollups (optional):** Use `results_summary/` and `expt_results/` at the experiment root only for cross-version summaries or shared aggregates. New experiment runs should keep per-run outputs in `expt_vN/results/`.

### Streaming multi-stage metrics

For an evaluation with dependent metric stages, attempt the first selected example through every authorized pipeline stage early, before a broad batch. Preserve its inputs and provenance, run every available stage, and publish its component values and combined score when complete. If a stage is genuinely blocked, promptly record the blocker and partial example instead; continue useful authorized work within the existing resource budget. As the run proceeds, prioritize completing examples through all available stages; record why a dependency or material resource-efficiency benefit warrants batching instead. A blocked stage does not excuse invisible results or require all other work to stop.

As each stage finishes for an example, immediately save a durable row record: row identifier, immutable input/provenance reference, every measured component, explicit `null` plus status/reason for each missing component, and the per-row combined score only when its required components exist. Keep the experiment-root `results.md` current with links to these records, a small representative row sample, running component aggregates and their measured-row counts, each stage's `completed / selected_total` count, and the count of complete multi-stage rows. Commit and push meaningful updates under the existing verification and publication requirements; do not wait for the entire batch. Preserve partial and unverified status until the applicable acceptance checks pass.

Show both the full selected population and the completed subset. A partial aggregate must identify its row population and missing stages; never present an earlier-stage aggregate as the final multi-stage metric. Missing values remain visible as `null`/incomplete, never silently zeroed or omitted to make a score look complete. Do not combine component means measured on different subsets into a purported completed-subset score: compute that score on the same fully measured rows, show its denominator, and keep the full-population score incomplete while required values are missing, unless the frozen protocol explicitly defines a different missing-data rule.

Preserve the protocol's aggregation formula. The geometric mean of dataset-level component means and the mean of per-row geometric means are different quantities: label them separately and never substitute one for the other. Providing a per-row combined score does not change the dataset-level definition; if the protocol defines only an aggregate, label any added row-level diagnostic explicitly rather than inventing a new official metric.

Once a blocked stage becomes available, resume only the missing stages on the preserved inputs; do not rerun valid earlier stages. If an earlier result is invalidated, record the reason and rerun only the affected stages and dependents. Preserve task selection, model and judge settings, rubric, seeds, inputs, and other frozen scientific choices. The checkpoint under Rule 44 records the exact missing stage and resume command; the live results file records measured values, denominators, and blockers.

Experiment-folder Markdown reports are sufficient for partial progress and completed results. Use Weights & Biases (W&B) logging, dashboards, or Reports only when the user explicitly requests them. A configured account, available key, old helper, or historical URL is not a request. Dashboard credentials, availability, and external publication must not delay ordinary progress, completion, notifications, or handoff. Preserve existing report links and immutable publication receipts as historical evidence. This reporting rule does not waive compilation, provenance, correctness, reference-data, quality-assurance, acceptance, resource, permission, or spending requirements.

---

## Results Reporting

- **1-3 sentence finding at the top.** Every results summary starts with a TL;DR of the key finding before tables or details.
- **Record exact model IDs** used in the results summary for reproducibility (e.g., `claude-opus-4-6`, `gpt-5.4`).
- **Include correlation metrics** where applicable: Pearson r, Spearman ρ, Kendall τ, R², ICC.

---

## Local Experiment Reports

**Experiment-folder Markdown (`.md`) reports are the primary and sufficient reporting deliverable** (Brando, 09-20-2026). Save the report in the canonical experiment folder, normally the active version's `results/` folder (for example, `expt_v2/results/`). Use the experiment-root `results_summary/` folder only for cross-version rollups.

The local report must include:

- **TL;DR** — 1-3 sentence summary of results at the top
- **Config table** — all hyperparameters
- **Results table** — final metrics
- **Plots, when useful** — save locally and reference relative paths (e.g., `![Loss](plots/loss_<timestamp>.png)`)
- **Artifact links** — local results and evidence; an existing external report URL may be included as an optional historical link. No W&B field, credential check, or publication step is required.

File naming: `expt_vN/results/results_summary_<MM-DD-YYYY__HH-MM-SS>.md` for per-version reports, or `results_summary/results_summary_<MM-DD-YYYY__HH-MM-SS>.md` for experiment-level rollups.

Markdown with relative-path PNGs works in GitHub, VS Code, and most editors — no localhost server needed.

---

## W&B Logging & Reports

**Optional; only on an explicit user request.** The Markdown report above satisfies ordinary experiment reporting. Do not inspect/load W&B credentials, install its reporting dependencies, start logging, create a Report, or publish externally merely because an experiment runs or finishes. The following recipe and code example apply only to a requested W&B deliverable; existing historical URLs remain usable.

- **Entity:** `brando-su`
- **Project:** depends on experiment (e.g., `vb-thm-eq` for judge correlation, `veribench-e3-agents` for agent benchmarks).
- **API key:** `export WANDB_API_KEY=$(cat ~/keys/brandos_wandb_key.txt)`
- **Dependency:** `pip install wandb[workspaces]` (required for Reports API).
- If requested, log only the authorized metrics, plots, config, and artifacts; preserve the task's privacy and publication boundaries.

### W&B Reports (explicit request only)

If the user requests a W&B Report, create the requested shareable document and retain its URL. Logging runs alone does not fulfill a specific request for a Report. No W&B artifact is required otherwise. Reference: https://docs.wandb.ai/models/reports

For an explicitly requested W&B Report:

1. **Push metrics** via `push_to_wandb.py` or inline `wandb.log()`.
2. **Create a Report** with: title (`<Experiment> — <Date>`), TL;DR, metric plots, config details, leaderboard table (if comparing models).
3. **Print the Report URL** — an additional deliverable for this explicit request.
4. **Include the Report URL** in the results summary file and in the final response to the user.

```python
import wandb_workspaces.reports.v2 as wr

report = wr.Report(
    entity="brando-su",
    project="<project>",
    title="<title>",
    description="<tldr>",
)
report.blocks = [
    wr.H1(text="Title"),
    wr.MarkdownBlock(text="| Metric | Value |\n|:---|---:|\n| ... | ... |"),
    wr.PanelGrid(
        runsets=[wr.Runset(project="<project>", entity="brando-su")],
        panels=[
            wr.BarPlot(title="Compile Rate", metrics=[wr.Metric(name="compile_%")], groupby="config.agent"),
        ],
    ),
]
report.save()
print(f"Report URL: {report.url}")
```

**Optional historical example:** `~/agents-config/tests/dummy_experiment/train.py` exercises W&B logging and Reports. Run it only for explicitly requested W&B work; it is not a default reporting prerequisite.

---

## Post-Experiment GPU Cleanup

After any training, eval, or QA run completes, check that no GPU processes are left behind. Handle this autonomously — only escalate to the user if there is a critical ambiguity.

1. **Confirm the experiment is actually finished:**
   - The process exited (exit code 0 or non-zero)
   - Any explicitly requested W&B transfer that actually started has finished; an optional dashboard failure does not keep experiment GPU processes alive
   - No checkpoint save or model upload is still in progress
   - No other experiment or pipeline stage depends on the process
2. **Check for lingering GPU processes:**
   ```bash
   nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
   ```
3. **If all checks pass**, kill lingering processes owned by the user without asking:
   ```bash
   kill <pid>
   ```
4. **Only ask the user if there is a critical ambiguity** — e.g., the process is shared across experiments, a multi-stage pipeline has unclear state, or the exit status is unclear. Same escalation rule as QA: autonomous unless critical.

---

## Graphics Processing Unit (GPU) Allocation Rules

Devices on the cluster are shared. The goal is not "never share" — cooperative sharing is fine — but rather "do not reserve more capacity than the job actually needs, especially for long-running, low-utilization work."

### Before launching: baseline, estimate, suggest, and ask

1. **The 1-Device Baseline:** Prefer a short 1-device baseline first (e.g., a ≤5 minute slice) whenever practical.
   Record: throughput, VRAM used, compute utilization, and signs of CPU or IO bottlenecks.
2. **Estimate and report:**
   * Estimated VRAM usage.
   * Expected utilization pattern.
   * Estimated duration (or explicitly state if unknown).
3. **Suggest the right-sized machine.**
   If the workload is small, bursty, or strictly data-bound, suggest a CPU run or a smaller node. If the user approves the current machine, proceed.
4. **Ask before scaling.**
   Never silently claim 2+ devices. Show which devices, estimated memory per device, expected utilization per device, and wait for approval.
5. **Hard Sandboxing:**
   You MUST isolate the environment using `export CUDA_VISIBLE_DEVICES=<id>` before running the code. Do not rely on framework defaults.

### After launching: verify

Sample utilization shortly after launch to ensure the script is behaving as expected.
If utilization is persistently low (<10%) but memory is held, do not automatically keep scaling. Instead, flag the issue to the user and suggest:
* Consolidating onto fewer devices.
* Fixing data loading / tokenization bottlenecks.
* Moving to a CPU node.

---

## Post-Experiment Cleanup

After every experiment run completes (success or failure):

1. **Kill zombie processes.** Check for orphaned Python/CUDA processes from the run:
   ```bash
   # Find your GPU processes
   nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
   # Cross-reference with your user's processes
   ps aux | grep $USER | grep -E 'python|torch|cuda' | grep -v grep
   ```
   Kill any leftover processes that are no longer needed. Do NOT kill other users' processes.

2. **Verify GPUs are freed.** Run `nvidia-smi` and confirm your experiment's GPU memory is fully released. If memory is still held, identify and kill the holding PID.

3. **Run QA review.** Dispatch a cross-agent reviewer per [`qa-correctness.md`](qa-correctness.md) to verify experiment results are correct before committing. This is mandatory — not optional.

4. **Report GPU state.** Include a final `nvidia-smi` summary in your completion message so the user can confirm resources are available for the next run.

**This is non-negotiable.** Zombie processes waste shared GPU resources and block other users and future experiments.

---

## Email Notification on Significant QA / Tracked Completion

Email is intentionally narrow. Send one email to `brando.science@gmail.com` only when a user-triggered "mega QA", "deep QA", "big QA", or explicitly requested tracked task finishes. Routine experiment runs, ordinary paper edits, default QA, exploratory reads, and small fixes should report in chat/Telegram only unless Brando explicitly asks for email.

**Why this matters:** Email is useful as a durable audit trail for major work, but automatic emails on every edit slow agents down and spam Brando's personal workflows. Keep email for user-triggered big/mega QA or explicitly tracked completions; use the current chat/Telegram thread for normal progress.

### Email Template

Use this structure when the notification trigger in `INDEX_RULES.md` Trigger Rule 14 actually fires. Adapt the sections to fit the task — not every task has a comparison — but include the final status, key artifacts, QA verdict, and links.

```
To: brando.science@gmail.com
Subject: [QA] <task or experiment name> — <PASS|FIXED|FAIL> (<key takeaway>)

Hi Brando,

Here is the completion summary for <task / experiment / QA pass>.

== RESULTS SUMMARY ==

<X/Y pass rate, one-line headline metric>

  [PASS] <item 1> (<attempts> attempt(s)) — <category/domain>
  [PASS] <item 2> (<attempts> attempt(s)) — <category/domain>
  [FAIL] <item 3> (<failure reason>) — <category/domain>
  ...

== COMPARISON == (if applicable — e.g., vs baseline, vs other system)

<Comparison metrics organized by dimension (verification, cost, discovery, etc.)>

== KEY INSIGHTS == (optional — 2-3 bullets on what was learned)

- <insight 1>
- <insight 2>

== QA / CONFIG ==

Model: <exact model ID, e.g., claude-opus-4-6, gpt-5-pro>
Backend: <backend used>
Max attempts: <N>
Lean: <version>
Mathlib: <branch> (<N> cached oleans)
Runtime: ~<duration>
QA verdict: <PASS / FIXED / FAIL>

== LINKS ==

Full results at: experiments/<NN>_<name>/results_summary/<file>.md
Experiment plan at: experiments/<NN>_<name>/experiment_plan.md
Optional existing external report: <URL, only if relevant; omit this line otherwise>

<email signature from ~/agents-config/email-signature.md>
```

### Rules

1. **Send only when Trigger Rule 14 fires.** Default QA, ordinary edits, routine experiment runs, and exploratory reads do not email by default.
2. **No CC by default.** Internal notifications go to `brando.science@gmail.com` only. Do not CC personal email unless Brando explicitly asks.
3. **Subject line** must include the experiment number, name, pass rate, and a short takeaway. Keep it scannable from a phone notification.
4. **[PASS]/[FAIL] tags** on every individual item — Brando skims these first.
5. **Exact model IDs** in the Config section — never "Claude" or "GPT", always the full ID.
6. **Link the experiment-folder Markdown report.** It is sufficient under `== LINKS ==`. Include an existing external report URL when relevant, but do not create or update W&B artifacts without an explicit user request, and do not delay an otherwise authorized completion notification for them.
7. **Include file paths** to the full results and experiment plan so Brando can jump straight to the details.
8. **Append the signature** from `~/agents-config/email-signature.md`.
9. **If an explicitly tracked task failed entirely**, still send the email. Subject: `[QA] <name> — FAILED (<reason>)`. Include the error details and what you think went wrong. Link the partial Markdown report; an existing external report URL may be included as optional historical evidence.

---

## Research/Paper Completion Notification (Only If Explicitly Tracked)

Per `INDEX_RULES.md` Trigger Rule 14, email `brando.science@gmail.com` only when a user-triggered big/mega QA pass finishes or Brando explicitly requested email/notification/tracking on completion. A normal paper edit, table fix, default QA run, or small research cleanup does not email by default. When Telegram initiated or approved the task, send a concise Telegram completion message in the originating chat.

### What counts as a "big" task

Send the email only if any of these apply:
- Brando explicitly asked for email/notification/tracking on completion.
- The task was a user-triggered "mega QA", "deep QA", "big QA", or similar substantial review pass.

Do NOT send for: single-line edits, routine paper edits, a light QA round Brando asked for in passing, read-only questions, exploratory searches, ordinary refactors, or agent-judged "significant" work that Brando did not explicitly ask to track by email.

**When in doubt, do not email.** Summarize in chat/Telegram instead.

### Explicitly Tracked Task Email Template

```
To: brando.science@gmail.com
Subject: [Task] <one-line task description> — <DONE|PARTIAL|BLOCKED> (<key outcome>)

Hi Brando,

Finished the task you asked for: <one-sentence description>.

== WHAT CHANGED ==

- <file 1 path> — <one-line what/why>
- <file 2 path> — <one-line what/why>
- ...

== COMMITS / PUSHES ==

- <repo>: <short SHA> — <commit subject>  (pushed: yes/no)
- ...

== QA ==

<QA verdict: PASS / FIXED / FAIL. One line on what was checked and by whom (Codex / CC / self-review; other providers only when eligible under the canonical QA policy and Trigger Rule 48). Link or path to QA output if substantive.>

== NOTES == (optional — 1-3 bullets on anything surprising, partial, or needing follow-up)

- <note 1>
- <note 2>

Links:
- <repo URL(s) or PR link(s) if applicable>
- <doc path(s)>

<email signature from ~/agents-config/email-signature.md>
```

### Rules (explicitly tracked-task emails)

1. **Send only for explicitly tracked significant tasks** — after the final commit/push/QA, not before.
2. **No CC by default.** Use `brando.science@gmail.com` only unless Brando explicitly names additional recipients.
3. **Subject line** must be scannable from a phone lock screen — task in 5-8 words, outcome tag (DONE / PARTIAL / BLOCKED).
4. **List every touched file** under WHAT CHANGED with a one-liner. No walls of prose.
5. **Include commit SHAs and push status** so Brando can pull/verify from any machine.
6. **Append the signature** from `~/agents-config/email-signature.md`.
7. **If the task is BLOCKED or PARTIAL**, still send the email. Subject: `[Task] <desc> — BLOCKED (<reason>)` or `— PARTIAL`. Explain what's done, what's not, what's needed to unblock.

---

## Prompt Templates

Each experiment keeps its own prompts under its versioned sub-experiment folders — not in a shared top-level `prompts/` directory. This keeps prompts versioned with the experiment iteration they belong to.

## Quota-aware remote execution

For dispatched experiments, apply [reliable agent dispatch](reliable-agent-dispatch.md) and Trigger Rule 48. The strong master chooses phase-appropriate execution models/effort, budgets shared usage through acceptance/publication, and verifies that the remote target has the exact runbook, checkpoint and inputs. Keep quota/failover events and actual model identities in the live records. A changed executor cannot silently change the model being measured, judge, sample, effort or scoring protocol. Meaningful quota-risk, provider-handoff and exhausted-recovery notices are authorized exceptions to the ordinary final-only email convention above; route and deduplicate them per Rule 48.
