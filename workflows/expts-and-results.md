# Workflow: Experiments & Results

How to structure experiments, store results, and report findings.

---

## Requirements Checklist (quick reference)

Every experiment **must** have:

- [ ] **Numbered directory** — `experiments/<NN>_<name>/` (sequential numbering, descriptive name)
- [ ] **README.md at root** — goal, structure tree, method, dependencies, status table
- [ ] **Versioned sub-experiments** — `expt_v1/`, `expt_v2/`, … each self-contained with own agent prompt, scripts, and `results/` dir
- [ ] **Agent prompt per version** — `cc.md` or `agents_vN.md` (paste-into-agent runnable prompt)
- [ ] **Writing draft** — `writing.tex` at experiment root (mandatory for paper-bound experiments; mark `% Status: DRAFT`)
- [ ] **W&B Report** — every completed experiment version must produce a W&B Report with permanent URL (not just logged runs)
- [ ] **Local results summary** — timestamped markdown in `expt_vN/results/results_summary_<date>.md` with TL;DR, config, metrics, plots, W&B link
- [ ] **QA review** — cross-agent correctness review before committing results (per `qa-correctness.md`)
- [ ] **GPU cleanup** — kill zombie processes, verify GPUs freed, report `nvidia-smi` state after completion

Encouraged (not mandatory):
- [ ] **todo.md** — open tasks / next steps for the experiment
- [ ] **results/paper_table.tex** — LaTeX table ready to `\input{}` into the paper

---

## Experiment Directory Structure

Each experiment lives under `experiments/<NN>_<name>/` in the project repo. Every experiment **must** have a `README.md` at its root and at least one versioned sub-experiment directory.

```
experiments/<NN>_<name>/
├── README.md                   ← goal, structure, method, dependencies, status table (MANDATORY)
├── todo.md                     ← open tasks / next steps for this experiment (optional but encouraged)
├── writing.tex                 ← draft paper section for this experiment (MANDATORY for paper-bound expts)
│                                  Mark as DRAFT; do not \input{} into main paper until finalized.
│                                  Example header: % Status: DRAFT — do not include in paper_latex/ yet
│
├── expt_v1/                    ← first iteration (self-contained)
│   ├── cc.md                   ← agent prompt (paste into Claude Code / Codex to run this version)
│   ├── run_*.sh / run_*.py     ← execution scripts
│   ├── push_to_wandb.py        ← W&B logging for this version
│   └── results/                ← outputs: JSONs, CSVs, plots, results_summary_<date>.md
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
├── collect_scores.py           ← shared scoring script (or per-version in expt_vN/)
├── compute_correlations.py     ← correlation analysis
├── generate_plots.py           ← scatter plots + histograms
├── results_summary/            ← top-level verified summaries (if not inside expt_vN/results/)
│   ├── results_summary_YYYY-MM-DD__HH-MM-SS.md
│   └── temporary_results/      ← unverified intermediates
└── expt_results/               ← top-level CSVs, JSONs, plots/ (if not inside expt_vN/results/)
```

### Versioned Sub-Experiments (`expt_v1/`, `expt_v2/`, …)

Most experiments evolve through iterations — changed metrics, added agents, new data splits, etc. Each iteration is a **self-contained directory** with its own agent prompt, scripts, and results. This keeps iterations reproducible and avoids overwriting prior results.

- Name versions sequentially: `expt_v1/`, `expt_v2/`, …
- Each version has its own agent prompt (`cc.md`, `agents_v2.md`, etc.) — the prompt you paste into Claude Code or Codex to run that version.
- Results stay inside the version dir: `expt_v1/results/`, `expt_v2/results/`.
- The top-level `README.md` documents all versions and their status.

### Experiment README.md (mandatory)

Every experiment root **must** contain a `README.md` with:

1. **Goal** — one paragraph: what this experiment tests and why it matters
2. **Structure** — ASCII tree of the experiment directory (keep it current)
3. **Method** — numbered steps describing the experimental procedure
4. **Dependencies** — what prior experiments, data, or API keys this needs
5. **Status table** — per-step status (`Done`, `TODO`, `In Progress`, `Blocked`)

Example status table:
```markdown
| Step | Status | Notes |
|------|--------|-------|
| v1 agent runs | Done | 15 agents, results in expt_v1/results/ |
| v1 paper table | Done | expt_v1/results/paper_table.tex |
| v2 real eval | In Progress | new metric, 3 agents so far |
| Writing draft | TODO | writing.tex started |
```

### Experiment Writing Draft (mandatory for paper-bound experiments)

If the experiment will produce a section or subsection in a paper, keep a **draft `.tex` file** (`writing.tex` or `draft_paper_section.tex`) at the experiment root. This is where you iterate on the paper text alongside the data — not in the main paper directory.

Rules:
- Mark it `% Status: DRAFT` at the top so no one accidentally `\input{}`s it.
- Reference the experiment's prompts, proposal, and data files in `%` comments.
- When the draft is finalized, copy/adapt it into `paper_latex/` — the experiment dir keeps the historical draft.
- Follow `~/agents-config/writing/ml_research_writing.md` for writing style.

---

## Results Storage

- **Results live inside the version dir:** `expt_v1/results/`, `expt_v2/results/`, etc. This keeps each iteration self-contained and reproducible.
- **Timestamped summaries:** Every results summary file is timestamped (`YYYY-MM-DD` or `YYYY-MM-DD__HH-MM-SS`). Never overwrite — create a new file per run.
- **Temporary results:** Unverified intermediates go in `results/temporary_results/` within the version dir. Never promoted; kept for audit trail.
- **Verification before commit:** Always run the verification checklist (in the experiment's agent prompt) and QA review before committing results to the repo.
- **Top-level fallback:** If the experiment doesn't use versioned sub-dirs (simple single-run experiments), results go in `results_summary/` and `expt_results/` at the experiment root.

---

## Results Reporting

- **1-3 sentence finding at the top.** Every results summary starts with a TL;DR of the key finding before tables or details.
- **Record exact model IDs** used in the results summary for reproducibility (e.g., `claude-opus-4-6`, `gpt-5.4`).
- **Include correlation metrics** where applicable: Pearson r, Spearman ρ, Kendall τ, R², ICC.

---

## W&B Logging & Reports

- **Entity:** `brando-su`
- **Project:** depends on experiment (e.g., `vb-thm-eq` for judge correlation, `veribench-e3-agents` for agent benchmarks).
- **API key:** `export WANDB_API_KEY=$(cat ~/keys/brandos_wandb_key.txt)`
- **Dependency:** `pip install wandb[workspaces]` (required for Reports API).
- Log all key metrics, plots, and config as artifacts.

### W&B Reports (mandatory)

Every experiment must produce a W&B Report — a shareable interactive document with a permanent URL. A logged run alone is NOT sufficient. Ref: https://docs.wandb.ai/models/reports

After any experiment completes:

1. **Push metrics** via `push_to_wandb.py` or inline `wandb.log()`.
2. **Create a Report** with: title (`<Experiment> — <Date>`), TL;DR, metric plots, config details, leaderboard table (if comparing models).
3. **Print the Report URL** — this is the primary deliverable.
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

**Reference test:** See `~/agents-config/tests/dummy_experiment/train.py` for a working example.

### Local Experiment Reports

In addition to W&B, **always save a local markdown report** in the experiment's `results_summary/` folder. This is the offline-readable copy of what the W&B Report shows.

The local report must include:
- **TL;DR** — 1-3 sentence summary of results at the top
- **Config table** — all hyperparameters
- **Results table** — final metrics
- **Plots** — saved as PNGs in `results_summary/plots/`, referenced via relative paths (e.g., `![Loss](plots/loss_<timestamp>.png)`)
- **W&B link** — Report URL if available, otherwise "N/A (offline or no API key)"

File naming: `results_summary/results_summary_<YYYY-MM-DD__HH-MM-SS>.md`.

Markdown with relative-path PNGs works in GitHub, VS Code, and most editors — no localhost server needed.

---

## Post-Experiment GPU Cleanup

After any training, eval, or QA run completes, check that no GPU processes are left behind. Handle this autonomously — only escalate to the user if there is a critical ambiguity.

1. **Confirm the experiment is actually finished:**
   - The process exited (exit code 0 or non-zero)
   - W&B sync/push completed (if applicable)
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

## GPU Allocation Rules

GPUs on SNAP are **shared** with other lab members. Blocking GPUs you aren't using prevents colleagues from running their work.

### Before launching: estimate, suggest, and ask

1. **Estimate VRAM and utilization.** Before launching, figure out how much GPU memory the job needs and whether it will be GPU-bound or CPU-bound. Common patterns:
   - **CPU-bound with GPU probe** (Task2Vec, Fisher Info, streaming data + small model): ~1–5 GB VRAM, <10% GPU utilization. The GPU sits idle 90%+ of the time while data streams/tokenizes on CPU.
   - **GPU-bound training** (fine-tuning, full model training): 10–140 GB VRAM, 80–100% GPU utilization.
   - **Inference serving** (vLLM, TGI): 20–140 GB VRAM depending on model size, high utilization under load.

2. **Suggest the right machine for the job.** If the job needs <20 GB VRAM, suggest a smaller-GPU machine (e.g., Mercury nodes on SNAP) instead of occupying an H200 (140 GB) or A100 (80 GB). Present this to the user: *"This job needs ~5 GB VRAM. We could run it on Mercury instead of using an H200 — want me to do that?"* The user may have reasons to stay (e.g., next job is large, or they want everything on one machine) — that's fine, but make them aware of the tradeoff.

3. **Warn about multi-GPU plans.** If you plan to use 2+ GPUs, tell the user the allocation plan with estimated VRAM and utilization per GPU, and ask for approval. Never silently claim multiple GPUs. For CPU-bound jobs, recommend running sequentially on 1 GPU.

4. **Check who else needs GPUs.** Run `nvidia-smi` and note current usage. If the machine is busy, mention it.

### After launching: verify within 2 minutes

Sample GPU utilization shortly after launch:
```bash
for i in 1 2 3 4 5; do nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader -i <GPU_ID>; sleep 2; done
```
If utilization is <10% on most samples, report this to the user and suggest consolidating or switching machines.

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

## Prompt Templates

Each experiment keeps its own prompts under its folder — not in a shared top-level `prompts/` directory. This keeps prompts versioned with the experiment they belong to.
