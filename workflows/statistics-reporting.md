# Workflow: Statistics reporting (agreement, uncertainty, variability)

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/statistics-reporting.md>

**TLDR:** This file lists what to report beside results, and why, in two tiers. The first is Hard Rule 11's minimum, which is cheap and applies to every project: training, reinforcement learning (RL), benchmarks and judges. The second is a fuller checklist for validating an LLM judge or proxy against human labels. Everything is computed from data the experiment already has; costly items count only when the experiment's budget already provides them.

## Global minimum (Hard Rule 11, every project)

| What | Why |
|---|---|
| Measured numbers beside every verdict, with counts, the split and uncertainty when available | "Passed" alone hides how good the result is |
| For correlations: Pearson, Spearman and Kendall, individually | Each captures something different: linear tracking, ranking, pairwise order |
| One absolute-agreement statistic (ICC(A,1), or mean absolute error with mean bias) **only when a score's value is interpreted**: a level, a threshold, "saturated", a mapped scale | Correlations are blind to a constant offset or rescaling (see the worked example below) |
| Repeated scoring: standard deviations and repetition counts, separating raw-repeat variability from repeatability of aggregated scores | Shows how noisy the scorer is, and what was averaged |
| **Computed from data the experiment already has.** The rule never requires extra runs, seeds, model calls or human labels; otherwise write "single run" or "unavailable" | Keeps the rule free for training, RL and API-funded work |
| Prefer cheap, honest reuse of that data for uncertainty and variance: a bootstrap or permutation test over the independent unit (tasks or seeds, not correlated items within them), or statistics over repeats already made; name the method | Uncertainty at no extra cost; resampling the independent unit prevents falsely narrow intervals |
| Thresholds shown with their source (user, protocol or agent-suggested); missing statistics marked "unavailable" | Honest provenance; nothing invented |

## Judge-human agreement checklist

Use this when validating an LLM judge, proxy metric or other scorer against human labels or ground truth. **Free** rows are post-processing on scores already collected (seconds of CPU, no model calls): compute them. **Costly** rows need extra scorer calls or raters: include them only when the protocol and budget already provide them, otherwise write "not measured". Never add calls, repeats or raters just to fill the table; propose them as a budgeted protocol change.

| Question | Report | Cost | Why |
|---|---|---|---|
| Same ordering? | Spearman ρ; Kendall τ-b | Free | Ranking claims ("A ranks above B"). (1 + τ)/2 is about the chance that a random pair is ordered like the reference; τ-b handles ties and small samples |
| Linear tracking? | Pearson r (r² optional) | Free | Linear association; blind to offset and scale |
| Right level? Needed when a value is read on its own | ICC(A,1) with ICC(C,1) beside it, or mean absolute error with mean bias (score − reference); weighted Cohen's κ for ordinal labels | Free | The only statistics that see the level; the gap between ICC(C,1) and ICC(A,1) is the offset |
| Binary or categorical labels? | Cell counts, accuracy, precision, recall, Cohen's κ; AUROC (area under the ROC curve) for a score against binary labels; base rates | Free | Categorical judges; base rates make accuracy interpretable |
| How sure? | 95% bootstrap interval resampling the independent unit; item and cluster counts; draws and seed | Free | Items within a task are correlated; resampling them overstates precision |
| Is a difference real? | Paired difference on the shared units, with its interval (and p-value) | Free | Pairing removes shared noise; two separate means hide it |
| How noisy is the scorer? | Repetition count; SD across raw repeats; repeatability of the aggregate (test–retest ICC or SD of aggregated scores) | Costly: k× scorer calls | Only when the repeats are already part of the protocol |
| What is achievable? | The same statistics between human raters (inter-rater, leave-one-rater-out) | Costly: at least two raters on the same items | The ceiling any judge can reach; only when the raters already exist |

**ICC notation.** Use ICC(A,1) for one judge or proxy score against the reference. Shrout and Fleiss call the same statistic ICC(2,1). ICC(C,1) is their ICC(3,1). ICC(A,k), their ICC(2,k), measures the reliability of an average of k ratings. Use it for an averaged human reference, such as the mean of three experts, and never for judge-versus-reference agreement, where it overstates agreement: 0.842 against ICC(A,1) 0.727 in the worked example below.

**Reuse existing data cheaply and honestly** to measure uncertainty and variance:

- bootstrap intervals and permutation tests that resample the independent unit (tasks, seeds or raters, not correlated items within them): free;
- statistics over repeats already made, such as per-pass agreement and its SD, or test–retest ICC: free;
- paired comparisons on the same units: free;
- pooling held-out sets, or cross-validating over all labels, only when prespecified. Cross-validation is free when selection outputs are cached and costs calls when selection must be rerun in each fold;
- controlled perturbations with a known answer (for example deleting half of a reference's obligations): costs scorer calls, no raters.

Never treat correlated items as independent, present model-generated labels as human, tune on test data, or report the best of several analyses without saying so.

**Discipline.**

- **Prespecify** the headline statistic, thresholds and subsets (for example excluding degenerate items) before seeing results. Report every prespecified statistic even when unflattering; label later additions post hoc and never swap them in.
- **Keep splits apart.** Numbers used for selection (train, validation) are not test evidence.
- **Match the claim to the evidence.** Rank statistics support "A ranks above B". A level claim ("0.96 coverage", "saturated") needs absolute agreement on data like the evaluated data, or an explicitly fitted mapping reported with its range limits.

## Keep papers and experiment records consistent

The experiment's committed receipts and Markdown report (`results.md`, `RESULTS_<topic>.md`) are the source of truth. The paper reports the same numbers and cites their source in a `% Provenance:` comment beside them. When a receipt changes or is superseded, update the paper in the same change, and the other way round; the two must never disagree. See the [ML research writing guide](../writing/ml_research/ml_research_writing.md) § Scientific Rigor, items 1, 10 and 11.

## Worked example: VeriBench's formal-specification-coverage judge (09-30-2026)

The judge was selected by validation Spearman and then tested once on 30 held-out items from 10 tasks:

| Statistic | Value | Reading |
|---|---:|---|
| Spearman ρ [95% task bootstrap] | 0.826 [0.316, 0.966] | Ranks outputs like experts, with a wide interval (10 tasks) |
| Kendall τ-b | 0.698 | About 85% of pairs ordered like the experts |
| Pearson r | 0.858 | Tracks experts along a line |
| ICC(C,1) | 0.852 | High consistency, ignoring offset |
| **ICC(A,1)** | **0.727** | Lower: the level is off |
| Mean absolute error / mean bias | 0.201 / +0.181 | The judge reads about 0.18 above the experts |
| ICC(A,2), for contrast | 0.842 | Overstates agreement; not the right statistic here |

Pearson, Spearman and Kendall alone would have shown a strong judge. Only the absolute-agreement statistics showed that its raw scores run about 0.18 high. The paper therefore claims that the judge's rankings are validated, and reports levels beside a fitted expert-scale mapping with its range limit. Every statistic above was computed from scores already collected; none needed a new call.

## Canonical example of a results summary item (Brando, 10-02-2026)

Every results summary Brando reads (weekly updates, experiment `results.md` headlines, chat replies about a result) is written at this level of detail and in this shape: the project tag in bold; one line stating the hypothesis being de-risked as a question plus "Measured via <metric>"; then bold-labelled bullets in this order where they apply: the old or baseline result with the instrument named; the judge or measuring instrument with its agreement on the train, val and test splits, each with n and `x [lo, hi]` intervals; the new results, one line per system; a "Saturated?" (or "Verdict?") bullet that reads the numbers against the pre-declared threshold and names what the instrument has not been shown to do; and a "Next step" bullet. Remarks go as numbered sub-items under the bullet they qualify. Every interval is `x [lo, hi]` with `p-val=Z` naming the test, or `p-val=n/a`; mean bias is judge minus human with the split named. Brando's own final version of the first item, kept as the reference:

> 1. **vbv1 (public paper)**. Hypothesis being de-risked: when the models create the trust artifacts (tests & formal specs/unproved thms), are they "correct" i.e. the intended f-specs? Measured via Formal Spec Coverage (FSC with an AI judge, prev TE1/TC) score:
>    - **May Result**: the "unsaturated" FSC coverage reported in May was 0.102 with a ("unvalidated") Claude Sonnet 4.6. The r=0.7 codex isotonic judge that was validated to humans was not used to score unfortunately.
>      1. remark: Amy's detected sorry bug did not affect old FSC coverage: the FSC judge seems proof-invariant (shift +0.002 [-0.021, +0.027], p-val=1.00, Wilcoxon).
>    - **New Judge**: GPT-6 Sol + Claude Opus 5.5 ensemble with human's rating instructions, validated/correlated against human ratings on the test split (30 rated candidate files, 10 problems = 3x10).
>      1. Train (n=30=3x10): Spearman 0.64 [0.25, 0.91], Pearson 0.66 [0.16, 0.92], ICC(A,1) 0.64 [0.14, 0.89]. 95% task-bootstrap CIs
>      2. Val (n=15=3x5, used to select the judge): Spearman 0.87 [0.70, 1.00] (0.88 with ties preserved), Pearson 0.86 [0.77, 1.00], ICC(A,1) 0.82 [0.48, 0.92]
>      3. Test (n=30=3x10): Spearman 0.83 [0.32, 0.97], Pearson 0.86 [0.71, 0.94], ICC(A,1) 0.73 [0.39, 0.89], repeat SD 0.02; p-val=n/a (the pre-registered gate was the CI lower bound, not a test)
>    - **New Sept Results** (fixed setting: agents must attempt every proof, sorry earns zero in IC_proofs):
>      1. Claude Code (Opus 5) FSC 0.956 [0.946, 0.964],
>      2. Codex (GPT-5.6 Sol) 0.897 [0.881, 0.913];
>      3. tests-pass and theorems-proved 0.98 to 1.00; overall SCSC 0.970 vs 0.963, a tie (difference +0.007 [-0.003, +0.015], p-val=0.15, paired task bootstrap). CIs are task bootstraps (10,000 draws) over this one run.
>    - **Saturated?** Arguably yes on the judge's scale (both FSC CIs lie above the 0.8 line, one-sided p-val<0.025); but this judge has not been shown to generalize to unseen agents or at least be trustworthy/validated on frontier models (the two above being reported)
>      1. remarks: the judge has a mean bias (= judge - human) of +0.18 on the test split (means 0.65 vs 0.47) and +0.10 on the val split, so it's more lenient than our human pool.
>    - **Next step**: A fresh human rating round on 2026 agents (Claude Code + Fable 5.1, Codex + GPT-6 Astra, Qwen 3.8 Max) needed cuz the judge hasn't been shown to work on that case formally or generalize (either minimum for paper but generalize would be nicer).

A multi-item summary ends with one `TLDR:` line holding one clause per item, in Brando's words for this one: "TLDR: (1) vbv1 seems saturated by the new frontier models (Opus 5, GPT-5.6 Sol) on the formal spec/unproved thm (FSC) metric, but to be sure we need a judge that is trustworthy on such outputs (which we don't have yet); (2) vbv2 is too small to call (7 harder tasks built, 0 accepted yet), and most of its 'low coverage' was the old judge; (3) certjudge: the label-free index predicts judge-human agreement on held-out judges (Spearman 0.56), the paper's old index doesn't, and every judge can be test-stuffed."

Sources for the numbers: VeriBench `experiments/100_karpathy_recipe_tc_judge_search_human_train_val_test/results/ensembles/{train,val,test}_H2_sol_plus_H2_opus.json`, `experiments/102_rescore_vbv1_paper_fsc_with_validated_judge_rewrite_tmlr_icml/results.md`, `experiments/105_fsc_judge_proof_invariance_same_statements_with_vs_without_proofs/results.md`.
