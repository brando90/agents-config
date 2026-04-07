# Workflow: Experiments & Results

How to structure experiments, store results, and report findings.

---

## Experiment Directory Structure

Each experiment lives under `experiments/<NN>_<name>/` in the project repo:

```
experiments/<NN>_<name>/
├── claude_code.md              ← experiment prompt (paste into Claude Code to run)
├── adapter/                    ← data → task generation (if using Harbor)
│   ├── adapter.py
│   ├── template/               ← Dockerfile, task.toml, test.sh, solve.sh
│   └── single_call_agent.py    ← custom agent (if needed)
├── tasks/                      ← generated task dirs (one per task)
├── collect_scores.py           ← parse job dirs → CSV
├── compute_correlations.py     ← correlation analysis
├── generate_plots.py           ← scatter plots + histograms
├── push_to_wandb.py            ← W&B logging
├── results_summary/            ← verified, committed summaries
│   ├── results_summary_YYYY-MM-DD__HH-MM-SS.md
│   └── temporary_results/      ← unverified intermediates
└── expt_results/               ← CSVs, JSONs, plots/
```

---

## Results Storage

- **Timestamped summaries:** Every results summary file is timestamped (`YYYY-MM-DD__HH-MM-SS`). Never overwrite — create a new file per run.
- **Temporary results:** Unverified intermediates go in `results_summary/temporary_results/`. Never promoted; kept for audit trail.
- **Verification before commit:** Always run the verification checklist (in the experiment's `claude_code.md`) before committing results to the repo.

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
