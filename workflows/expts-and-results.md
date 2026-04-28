# Workflow: Experiments & Results

**TLDR:** The canonical experiment-folder convention for this account:
`experiments/<NN>_<name>/` with mandatory `README.md`, versioned
sub-experiments, results storage, W&B reporting, GPU rules, and the
**MANDATORY** end-of-experiment email. Includes the canonical templates
for the agent prompt (`cc.md` — must open with `**TLDR:**`) and
`PROTOCOL.md` (must open with `## Scientific question (locked)`).
Read end-to-end before starting, opening, or reviewing any experiment dir.

---

## Requirements Checklist (quick reference)

Every experiment **must** have:

- [ ] **Numbered directory** — `experiments/<NN>_<name>/` (sequential numbering, descriptive name)
- [ ] **README.md at root** — goal, structure tree, method, dependencies, status table
- [ ] **Versioned sub-experiments** — `expt_v1/`, `expt_v2/`, … each self-contained with own agent prompt, scripts, and `results/` dir
- [ ] **Agent prompt per version** — `cc.md` or `agents_vN.md` (paste-into-agent runnable prompt)
- [ ] **W&B Report** — every completed experiment version must produce a W&B Report with permanent URL (not just logged runs)
- [ ] **Local results summary** — timestamped markdown in `expt_vN/results/results_summary_<YYYY-MM-DD__HH-MM-SS>.md` with TL;DR, config, metrics, plots, W&B link
- [ ] **QA review** — cross-agent correctness review before committing results (per `qa-correctness.md`)
- [ ] **GPU cleanup** — if the run used GPUs: kill zombie processes, verify GPUs freed, report `nvidia-smi` state after completion

Paper-bound experiments **must also** have:
- [ ] **Writing draft** — `writing.tex` at experiment root (mark `% Status: DRAFT`)

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
│   └── results/                ← outputs: JSONs, CSVs, plots, results_summary_<YYYY-MM-DD__HH-MM-SS>.md
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
├── push_to_wandb.py            ← optional shared W&B logging helper used by one or more versions
├── results_summary/            ← optional top-level rollup summaries across versions (or legacy location)
│   ├── results_summary_YYYY-MM-DD__HH-MM-SS.md
│   └── temporary_results/      ← unverified intermediates
└── expt_results/               ← optional shared/aggregated CSVs, JSONs, plots across versions
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

### Agent Prompt (`cc.md`) format — MANDATORY

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
   pass/fail thresholds, primary-vs-ablation split.
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
   full run.
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
- Follow `~/agents-config/writing/ml_research_writing.md` for writing style.

---

## Results Storage

- **Results live inside the version dir:** `expt_v1/results/`, `expt_v2/results/`, etc. This keeps each iteration self-contained and reproducible.
- **Timestamped summaries:** Every results summary file is timestamped (`YYYY-MM-DD` or `YYYY-MM-DD__HH-MM-SS`). Never overwrite — create a new file per run.
- **Temporary results:** Unverified intermediates go in `results/temporary_results/` within the version dir. Never promoted; kept for audit trail.
- **Verification before commit:** Always run the verification checklist (in the active version's agent prompt) and QA review before committing results to the repo.
- **Top-level rollups (optional):** Use `results_summary/` and `expt_results/` at the experiment root only for cross-version summaries or shared aggregates. New experiment runs should keep per-run outputs in `expt_vN/results/`.

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

Every completed experiment version must produce a W&B Report — a shareable interactive document with a permanent URL. A logged run alone is NOT sufficient. Ref: https://docs.wandb.ai/models/reports

After any experiment version completes:

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

In addition to W&B, **always save a local markdown report** in the active version's `results/` folder (for example, `expt_v2/results/`). Use the experiment-root `results_summary/` folder only for cross-version rollups.

The local report must include:
- **TL;DR** — 1-3 sentence summary of results at the top
- **Config table** — all hyperparameters
- **Results table** — final metrics
- **Plots** — saved as PNGs in `results/plots/`, referenced via relative paths (e.g., `![Loss](plots/loss_<timestamp>.png)`)
- **W&B link** — Report URL if available, otherwise "N/A (offline or no API key)"

File naming: `expt_vN/results/results_summary_<YYYY-MM-DD__HH-MM-SS>.md` for per-version reports, or `results_summary/results_summary_<YYYY-MM-DD__HH-MM-SS>.md` for experiment-level rollups.

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

## Email Notification on Experiment Completion (MANDATORY)

**This is non-negotiable. When an experiment finishes — PASS or FAIL — you MUST send an email to `brando.science@gmail.com` with the results.** Do not skip this. Do not ask whether to send it. Do not create a draft. **Send the email.** Use the project's `SMTPNotifier` or the Gmail MCP tool — whichever is available. If neither works, use `scripts/send_pending_emails.py` as fallback.

**Why this matters:** Brando needs to know experiment outcomes immediately — he may be away from the terminal, on his phone, or asleep. The email is how he tracks progress across all running experiments. A completed experiment with no email is invisible work.

### Email Template

Use this structure for every experiment completion email. Adapt the sections to fit the experiment — not every experiment has a comparison — but always include Results Summary, per-item breakdown, Config, and links.

```
To: brando.science@gmail.com
CC: brando9@stanford.edu
Subject: [Experiment <NN>] <experiment name> — <X/Y PASS> (<key takeaway>)

Hi Brando,

Here are the results from Experiment <NN>: <experiment description>.

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

== CONFIG ==

Model: <exact model ID, e.g., claude-opus-4-6, gpt-5-pro>
Backend: <backend used>
Max attempts: <N>
Lean: <version>
Mathlib: <branch> (<N> cached oleans)
Runtime: ~<duration>

== LINKS ==

W&B Report: <permanent W&B Report URL, e.g., https://wandb.ai/brando-su/<project>/reports/<slug>>
Full results at: experiments/<NN>_<name>/results_summary/<file>.md
Experiment plan at: experiments/<NN>_<name>/experiment_plan.md

<email signature from ~/agents-config/email-signature.md>
```

### Rules

1. **Send immediately** when the experiment finishes. Do not batch emails across experiments — one email per experiment completion.
2. **Always CC** `brando9@stanford.edu` (per `email-signature.md`).
3. **Subject line** must include the experiment number, name, pass rate, and a short takeaway. Keep it scannable from a phone notification.
4. **[PASS]/[FAIL] tags** on every individual item — Brando skims these first.
5. **Exact model IDs** in the Config section — never "Claude" or "GPT", always the full ID.
6. **Include the W&B Report URL.** Every completed experiment version already requires a W&B Report with a permanent URL (see Requirements Checklist). That URL **must** appear in the email under `== LINKS ==`. If the report has not been generated yet, generate it before sending the email — do not send the email first and promise the report later. Example format: `https://wandb.ai/brando-su/<project>/reports/<slug>`.
7. **Include file paths** to the full results and experiment plan so Brando can jump straight to the details.
8. **Append the signature** from `~/agents-config/email-signature.md`.
9. **If the experiment failed entirely** (0 passes, infrastructure error, etc.), still send the email. Subject: `[Experiment <NN>] <name> — FAILED (<reason>)`. Include the error details and what you think went wrong. If a partial W&B Report exists, include its URL anyway.

---

## Big-Task Notification (MANDATORY for non-experiment "big" tasks)

Per INDEX_RULES Trigger Rule 14, email `brando.science@gmail.com` (CC `brando9@stanford.edu`) when a "big" user-assigned task finishes — not just experiments. Use the same send mechanics as experiment emails: send immediately via the project's `SMTPNotifier` or the Gmail MCP tool; if neither works, use `scripts/send_pending_emails.py` as fallback. Do not draft it. Send it.

### What counts as a "big" task

Send the email if any of these apply:
- Multi-file edits to shared config (`~/agents-config/`, cluster-level `CLAUDE.md`, etc.)
- Adding or meaningfully modifying a workflow doc or Hard/Trigger Rule
- Drafting a blog post, paper section, or other writing artifact
- Repo migration, CI change, auth/infra change
- Any task that went through the QA chain
- Any task that took more than ~5 tool calls AND produced durable artifacts (commits, pushed files, new docs)

Do NOT send for: single-line edits, read-only questions, exploratory searches, trivial refactors the user didn't ask to be notified about.

**When in doubt, send.** A false-positive email is cheap; a missed completion is expensive.

### Big-Task Email Template

```
To: brando.science@gmail.com
CC: brando9@stanford.edu
Subject: [Task] <one-line task description> — DONE (<key outcome>)

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

<QA verdict: PASS / FIXED / FAIL. One line on what was checked and by whom (Codex / CC / Gemini). Link or path to QA output if substantive.>

== NOTES == (optional — 1-3 bullets on anything surprising, partial, or needing follow-up)

- <note 1>
- <note 2>

Links:
- <repo URL(s) or PR link(s) if applicable>
- <doc path(s)>

<email signature from ~/agents-config/email-signature.md>
```

### Rules (big-task emails)

1. **Send immediately** when the task is done — after the final commit/push/QA, not before.
2. **Always CC** `brando9@stanford.edu`.
3. **Subject line** must be scannable from a phone lock screen — task in 5-8 words, outcome tag (DONE / PARTIAL / BLOCKED).
4. **List every touched file** under WHAT CHANGED with a one-liner. No walls of prose.
5. **Include commit SHAs and push status** so Brando can pull/verify from any machine.
6. **Append the signature** from `~/agents-config/email-signature.md`.
7. **If the task is BLOCKED or PARTIAL**, still send the email. Subject: `[Task] <desc> — BLOCKED (<reason>)` or `— PARTIAL`. Explain what's done, what's not, what's needed to unblock.

---

## Prompt Templates

Each experiment keeps its own prompts under its versioned sub-experiment folders — not in a shared top-level `prompts/` directory. This keeps prompts versioned with the experiment iteration they belong to.
