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
- Log all key metrics, plots, and config as artifacts.
- **Generate a W&B Report** after logging is complete — not just runs/artifacts. A Report is a shareable dashboard with a permanent URL. Use the W&B Reports API: https://docs.wandb.ai/models/reports
- **Include the Report URL** in the results summary file and in the final response to the user. This is the primary deliverable — the user needs a clickable link to the Report, not just confirmation that metrics were logged.
- **Dependency:** Reports require `pip install wandb[workspaces]` (not just `wandb`). Ensure this is installed before calling the Reports API.
- **Reference test:** See `~/agent-config/tests/dummy_experiment/train.py` for a working example of training + W&B logging + Report creation.

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
4. **Only ask the user if there is a critical ambiguity** — e.g., the process is shared across experiments, a multi-stage pipeline has unclear state, or the exit status is unclear. This follows the same escalation rule as QA gating: autonomous unless critical.

---

## Prompt Templates

Each experiment keeps its own prompts under its folder — not in a shared top-level `prompts/` directory. This keeps prompts versioned with the experiment they belong to.
