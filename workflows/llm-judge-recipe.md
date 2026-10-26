# llm-judge-recipe.md — Karpathy's recipe for building and validating an LLM judge

**TLDR:** Build an LLM judge (automatic grader, rubric scorer, reward model) the way Karpathy trains a neural net. Become one with the human labels, then earn trust in the end-to-end pipeline through sanity checks *before* tuning: a byte-level input audit, the untuned judge's score distribution, a label-reproduction test, controls, and human and dumb baselines. Only then overfit the training split, regularize, test once and apply. The worked example is the VeriBench coverage-judge search. Weeks of failed studies there came down to one skipped check: the judge never saw the files the raters saw. The "overfit" step never approached the human ceiling on the training labels, and nobody tested whether it could.

## References (origin)

- Andrej Karpathy, "A Recipe for Training Neural Networks", 04-25-2019: <https://karpathy.github.io/2019/04/25/recipe/>. The quotes below are short excerpts; read the original.
- VeriBench (`brando90/veribench`) judge search:
  - `experiments/100_karpathy_recipe_tc_judge_search_human_train_val_test/` (`README.md`, `PROTOCOL.md`, `REPORT.md`, `results.md`, `JUDGE_EXPLAINER.md`, `results/sanity/TRAIN_TEST_GAP.md`);
  - `experiments/104_fsc_judge_5fold_cross_validation_all_75_expert_labels/` (cross-validating the recipe; created as 103 and renumbered);
  - `experiments/101_neurips_te1_judge_validation_audit/` (the NeurIPS-era judge);
  - earlier negative studies 75, 76, 83, 92 and 92c.
- Sibling skill: [`ml-research-practice.md`](ml-research-practice.md) (expect-then-verify; Rylan Schaeffer's CS229 lessons).

## When to use this skill

Load it whenever you build, select, validate, deploy or re-validate an LLM judge, automatic grader, reward model, or rubric-based LLM-as-a-judge metric. Also load it when you collect human labels for one, or before you write that a judge "agrees with humans", "is validated" or "passes".

## Why judges need the recipe: Karpathy's two facts, translated

1. **"Neural net training is a leaky abstraction."** A judge is not a black-box metric. Its number depends on:
   - which files it sees;
   - how the prompt is assembled;
   - the output parser and the scale mapping (0–5 vs 0–10);
   - aggregation over repeats (median, mean);
   - the target (whose ratings, which mean);
   - the split.
2. **"Neural net training fails silently."** Karpathy: "Everything could be correct syntactically, but the whole thing isn't arranged properly, and it's really hard to tell." A judge pipeline produces plausible numbers when it is broken: a stale reference snapshot, a parser that turns prose into "1/10", a cache keyed by the wrong input, degenerate items everyone gets right, truncated prompts.

Karpathy's process "builds from simple to complex and at every step of the way we make concrete hypotheses about what will happen and then either validate them with an experiment or investigate until we find some issue." Every check below states its expected result first.

## The recipe

### 1. Become one with the human labels (before writing any judge prompt)

Karpathy: "The first step to training a neural net is to not touch any neural net code at all and instead begin by thoroughly inspecting your data."
- Read every rated item beside the rater instructions, and rate a few yourself.
- Histogram the labels. Find degenerate items (for example references with nothing to cover, where every candidate deserves full marks), duplicates, and items whose inputs changed during rating.
- Compute rater agreement and the **human ceiling** per split: one rater held out against the others, Karpathy's "annotate the test data twice and for each example treat one annotation as prediction and the second as ground truth". That ceiling is the achievable bar, not 1.0.
- Study how the raters disagree, and choose the target deliberately.

**VeriBench:**
- 15 of the 75 items (5 tasks) had `True`-only placeholder references.
- Experts rated bundled correctness theorems 1–3 where lenient raters gave 4–5.
- The human ceilings were 0.794 / 0.899 / 0.733 on train / validation / test.

All of this was established systematically only in experiment 100, after four earlier judge studies.

### 2. Build the end-to-end skeleton and earn trust in it with sanity checks

Karpathy: "set up a full training + evaluation skeleton and gain trust in its correctness via a series of experiments."

**2.1 "Visualize just before the net" → a byte-level input audit.** Karpathy: "visualize exactly what goes into your network … This is the only 'source of truth'." Dump the exact rendered judge prompt for several items, and hash-compare every embedded file (source, reference, candidate) with what the raters saw.
- **VeriBench skipped this for weeks.** Experiments 75, 83, 92 and 92c fed their judges a 09-03-2026 reference snapshot, while the raters had rated against April–May references. Nine of the 25 tasks' theorem statements differed, and five had been placeholders at rating time.
- Re-analyzing one saved judge (R4, Sonnet 5) split by whether its reference matched gives Spearman 0.469 on matched items and 0.095 on mismatched ones. One diff would have saved the studies.

**2.2 "Verify loss @ init" → the untuned judge's score distribution.** Before any tuning, run the plain judge and look at its histogram, entropy, modal share and a handful of rationales.
- **VeriBench:** the NeurIPS-era coverage judge put 85–87% of task scores at exactly 0.1. Replaying its loose parser on 1,185 logged responses mapped 94.3% of them to 0.1. A histogram shows this in seconds.

**2.3 "Overfit one batch" → a label-reproduction test.** Karpathy: "Overfit a single batch of only a few examples … verify that we can reach the lowest achievable loss (e.g. zero) … If they do not, there is a bug somewhere and we cannot continue to the next stage." Two judge versions:
- **Label in the prompt.** Give the judge each item's expert score, and optionally the rationale, and ask it to return that score. Agreement must be about 1.0. Anything less is a pipeline bug: parsing, scale mapping, item–label misalignment, truncation.
- **Unconstrained fit on 2–3 items.** Iterate the prompt freely, item-specific hints allowed, until the judge matches the experts on those items. If it can't, inspect the item. You will find either a label–input mismatch (the rater saw different files) or a construct the prompt cannot express. In VeriBench this would have exposed the reference mismatch on the first affected item.
- **VeriBench never ran either test.** Its "overfit" gate was training Spearman ≥ 0.60, a bar to clear rather than a reproduction test.

**2.4 "Input-independent baseline" → controls with predicted values.** Karpathy: "This should perform worse than when you actually plug in your data without zeroing it out."
- Blank candidate, vacuous claim and a shuffled candidate from another task should score about 0. The oracle (reference judged against itself) should score about the maximum. A minimal reference should score partially.
- Write the expected values down first, and check the controls themselves. VeriBench's "half-deleted reference" control was mis-specified: a redundant reference keeps full coverage, so the judge was logically right. It was replaced prospectively.

**2.5 "Human baseline."** Karpathy: "Whenever possible evaluate your own (human) accuracy and compare to it." Use the leave-one-rater-out ceiling from step 1. "Human level" means matching that ceiling.

**2.6 Dumb baselines.** Length, theorem count, placeholder count, always predicting the mean. The judge must beat them on the non-degenerate items. If a dumb baseline beats your judge, stop and find out why before tuning anything.
- **VeriBench:** a one-line baseline, min(1, candidate theorems ÷ reference theorems), reaches Spearman 0.543 on the full 75-item pool with the references the raters saw. That beats every earlier LLM judge (0.17–0.28). Fed the 09-03 snapshot the earlier judges used, the same baseline falls to 0.273. It would have exposed both the weak judges and the reference mismatch at zero cost.

**2.7 "Fix random seed" → repeat stability.** LLM judges are stochastic. Run k ≥ 3 repeats, report per-item repeat SD and test–retest ICC, and pin model IDs, configurations and prompt fingerprints by hash. VeriBench's selected judge has repeat SD 0.02.

**2.8 "Add significant digits to your eval."**
- Report task-bootstrap intervals, on all items and on the non-degenerate items separately.
- Use several agreement statistics: Spearman, Kendall, Pearson, plus ICC(A,1), which penalizes level, beside ICC(C,1), which does not.
- Never rely on a single small split alone.

**2.9 "Generalize a special case."** Get one task's items right end to end before running the whole pool.

### 3. Overfit the training split, and expect to approach the human ceiling

- **"Don't be a hero."** Start from the raters' own instructions (a human-mirror judge), not an invented rubric. In VeriBench's held-out ablations, matched inputs and the rater-derived conventions carried most of the gain.
- **"Complexify only one at a time,"** with a changelog line per change. VeriBench went H0 human mirror (training Spearman 0.460) → H1, adding four conventions written from training disagreements (0.562) → H2, adding four leave-task-out rated examples (0.591) → H2 on Claude Opus 5.5 max (0.663).
- **Read the worst training items after every iteration.** The plain human-mirror judge ordered candidates *within* a task opposite to the experts (within-task correlation −0.38 on training); the conventions fixed it.
- **Expect training agreement near the human ceiling.** If it stays well below, stop and investigate before moving on. Karpathy: "if we are not able to reach a low error rate with any model at all that may again indicate some issues, bugs, or misconfiguration."

> **Why wasn't VeriBench's training agreement close to 1.0?** The selected ensemble reached 0.641 on train against a human ceiling of 0.794.
> 1. **Almost no capacity to memorize.** Training labels entered the judge only as four written conventions and four rated examples. An item's own label never appears in its prompt, because the examples are leave-task-out. A prompt-level judge is closer to a fixed model with a few hints than to a network fit to its labels. "Overfitting" in Karpathy's sense, driving training error to zero, was never attempted; the gate was a bar at 0.60.
> 2. **Noisy labels.** The target is a three-expert mean on a 0–5 scale, and one expert agrees with the other two at 0.794 on train. A judge of true coverage cannot correlate perfectly with a noisy mean.
> 3. **Label–input mismatches on training items.** Five tasks' references changed while raters were rating, so the judge may have scored different bytes than the raters saw. Convention 2 ("restating the code earns 0–1") also misfired on one placeholder item the experts rated 5/5 (`5_unsafeFormatString_safe__agent2`). Without that item and those tasks, train reaches 0.891 (validation 0.883, test 0.885). That is a post-hoc diagnostic, not a claim.
> 4. **Coarse outputs.** Integer scores, the median of 3 per member averaged across two members, produce many ties, which cap rank correlations.
> 5. **Small splits.** Random 10/5/10 re-splits of the 25 tasks produce a train–test gap at least this large 18.9% of the time; a 10-task Spearman has SD about 0.12.
>
> The label-reproduction test (2.3) separates reasons 1–2 (capacity and noise, acceptable) from bugs (not acceptable). Run it, and "why isn't train 100%?" has a measured answer instead of a guess.

### 4. Regularize and generalize

- Keep rules general and rated examples leave-task-out. Select among at most three frozen finalists, on validation only.
- **"Get more data."** Karpathy: "the by far best and preferred way to regularize a model in any practical setting is to add more real training data." For judges that means more human ratings.
- **When ratings are scarce, cross-validate the whole recipe.** Rebuild the judge in each fold from the other folds' labels, including rules written automatically from those folds' errors, and score the held-out fold. Every rating then becomes evaluation data exactly once; this is VeriBench experiment 104.
- **Expect the honest number to be lower, and report it.** VeriBench's cross-validated recipe scored Spearman 0.602 [0.286, 0.834] and ICC(A,1) 0.593 over all 75 items. That is below the frozen judge's 0.826 on its 30-item test and 0.756 on the whole pool, of which 30 items had shaped its rules. It also showed how little the tuning bought: the raters'-instructions judge with no tuning was within 0.002 (Claude Opus 5.5) to 0.087 (GPT-6 Sol) of the recipe, both intervals including zero. The five 15-item folds ranged from 0.35 to 0.86, another reminder that one small split is a noisy estimate.
- You cannot relabel already-used ratings as a "test set" for a judge designed after reading them.

### 5. Test once, with a receipt

- Freeze the judge by hash before any test call, run the test once, and write a receipt.
- Report every agreement statistic with intervals, the non-degenerate items separately, and the human ceiling. Disclose earlier looks at the same test labels.
- **VeriBench:** test Spearman 0.826 [0.32, 0.97], Kendall 0.698, Pearson 0.858, ICC(A,1) 0.727 against a ceiling of 0.733, which passed the prespecified gate. On the 24 ordinary test items the Spearman is 0.652 [−0.17, 0.92]: placeholder items carried part of the pass, and 8 ordinary tasks cannot establish rank agreement on their own.

### 6. Squeeze out the juice

Karpathy: "Model ensembles are a pretty much guaranteed way to gain 2% of accuracy on anything." For judges, average members from different model families. That adds accuracy and dilutes self-preference, such as a Claude judge scoring Claude agents. VeriBench uses GPT-6 Sol high plus Claude Opus 5.5 max, the mean of the two members' medians.

### 7. Apply carefully, and re-validate on the new distribution

- **Transfer is an assumption.** A judge validated on one population of outputs (VeriBench: 05-2026 Claude 3.7 Sonnet candidates) is unvalidated on another (frontier agents). Re-validate with fresh human ratings drawn from the population it will score. Spend them mostly on evaluation: the judge needs few labels to build.
- **Check level, not only order.** High correlation can coexist with leniency.
  - VeriBench's judge effectively uses three levels (about 0.1, 0.8 and 1.0). Items the experts rated as partial coverage (0.3–0.6, mean 0.44) came out at about 0.78.
  - Report ICC(A,1) beside ICC(C,1), and a band table (expert band → judge mean).
  - If you fit a monotone score mapping to the experts' scale, label it as a separately fitted procedure, evaluated on held-out ratings.
- **Controls travel with the judge.** Re-run them on every new population.
- **Re-audit inputs whenever references change.** Any edit after rating breaks the judge–rater correspondence, so version the references and re-check hashes.

## What skipping the sanity checks cost: the VeriBench timeline

| When (2026) | Study | Outcome | Skipped check |
|---|---|---|---|
| 04–05 | NeurIPS coverage judge (Sonnet 4.6, symmetric equivalence rubric) | 85–87% of task scores at 0.1; published without validation | 2.2 score distribution; parser trace |
| 09-03 to 09-12 | Experiment 75 judge search, locked 10/5/10 split | No winner; finalist test Spearman 0.271 | 2.1 byte-level input audit (judges saw 09-03 references) |
| 09 | Experiments 83, 92, 92c (frontier directional judges, open-weight and Gemini judges) | All below the 0.45 gate; best expert Spearman 0.17–0.28 on the full pool | 2.1 again; 2.6 (a theorem-count ratio scored 0.543) |
| 09-28 | Experiment 100 Phase 0, zero calls | Found the mismatch; with matched inputs a judge passed a held-out test | — |
| 09-28 | Experiment 100 "overfit" step | Training 0.641, below the human ceiling; explained only by a later audit | 2.3 label-reproduction test |

## Checklist (paste into a judge study's protocol)

- [ ] Labels read; degenerate items flagged; human ceiling per split computed; target chosen deliberately.
- [ ] The exact judge inputs hash-match what the raters saw, for every item.
- [ ] The untuned judge's score distribution inspected (entropy, modal share, rationales).
- [ ] Label-in-prompt reproduction ≈ 1.0; an unconstrained fit on 2–3 items succeeds, or the failure is explained.
- [ ] Controls with predicted values (oracle, vacuous, shuffled, blank, partial) pass; the controls themselves were checked.
- [ ] Dumb baselines beaten on non-degenerate items.
- [ ] k ≥ 3 repeats; repeat SD reported; model IDs, configurations and prompt fingerprints pinned.
- [ ] One change per training iteration, with a changelog; training agreement near the human ceiling, or the gap explained.
- [ ] Finalists frozen before validation; test run once with a receipt; earlier looks disclosed.
- [ ] Order and level both reported (Spearman, Kendall, Pearson, ICC(A,1) and ICC(C,1), band table), with intervals and non-degenerate subsets.
- [ ] Re-validated on the population it will score, with fresh ratings spent on evaluation.

TL;DR: Treat a judge like a network you are training: inspect the labels, prove the pipeline can reproduce them and sees exactly what the raters saw, then overfit, generalize and test once. In VeriBench, a one-line input diff and a label-reproduction test would have prevented weeks of confounded judge studies and answered "why isn't train 100%?"
