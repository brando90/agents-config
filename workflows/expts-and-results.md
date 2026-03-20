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

## W&B Logging

- **Entity:** `brando-su`
- **Project:** depends on experiment (e.g., `vb-thm-eq` for judge correlation, `veribench-e3-agents` for agent benchmarks).
- Log all key metrics, plots, and config as artifacts.

---

## Prompt Templates

Each experiment keeps its own prompts under its folder — not in a shared top-level `prompts/` directory. This keeps prompts versioned with the experiment they belong to.
