# VeriBench set names

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/vb-sets.md>

**TLDR:** Use these names, and only these, for VeriBench task sets in prompts, reports and run labels. "Small" is not a name of any set; say VB256 or the full set. VeriBench has no "Core" split (see below).

| Name | What it is | Size | Where the task list lives |
|---|---|---|---|
| **VeriBench** (full, V1) | Release `veribench@1.3`: six splits, EasySet 41, CSSet 25, HumanEval 56, RealCodeSet 32, SecuritySet 460, IndustrySet 282 | 896 | Harbor registry `veribench@1.3`; `brando90/veribench` |
| **IndustrySet** | One of the six splits (not a second half of the benchmark) | 282 | `experiments/116_tiny_vbv1_subset_selection_and_frontier_validation/expt_v1/manifests/industry_282.json` |
| **VB256** (11-18-2026) | The 256-task subset for new work: a frozen stratified random sample of all 896 tasks that covers every split (EasySet 11, CSSet 6, HumanEval 16, RealCodeSet 8, SecuritySet 136, IndustrySet 79); experiment 116 `expt_v10`, frozen before validation, chosen from split, IndustrySet domain and program size only, no scores. Mean absolute error against the 896-task final smooth score on the 4 solver agents: 1.03 / 0.71 points (floor / high end, no DT) | 256 | `.../expt_v10_audit_and_heldout_validation_11-18-2026/manifests/vb256_all_splits.json` |
| **TinyVeriBench-256** (named by Brando 10-22-2026; formerly "Tiny256") | History: replaced by VB256 on 11-18-2026 because it holds no IndustrySet task and is 2.13 / 4.05 points from the 896-task score; kept only for results already measured on it. A stratified 256-task sample of five splits (experiment 116): five source categories x two AST-size halves, seed 20261015, chosen from public metadata only, no scores; not a new sample. tinyBenchmarks-style subset study; status "pilot, not frontier validated" | 256 | `.../expt_v1/manifests/core_256.json` |
| **Tiny96** | The earlier 96-task nested pilot of TinyVeriBench-256 (same design) | 96 | `.../expt_v1/manifests/core_96.json` |
| **VeriBench-Infinity** (VB-Inf, VBV3) | Differential proving against curated Lean references for correct and deliberately incorrect Python variants | 24 pairs | [Current task packages on main](https://github.com/brando90/veribench-inf/tree/main/tasks) |
| **VB private** | Vals/BMG held-out set; target 180 accepted tasks, separate from the public set | 180 target | `brando90/vb-priv-bmg` (not public) |

The GitHub repository is `brando90/veribench-inf` (previous GitHub names: `veribench-dt` and `veribench-infinity`). VeriBench-DT refers to the earlier differential-testing work. Differential testing is planned for V1 and VeriBench Private. There is currently no private differential-proving edition (`vb-priv-inf`).

Rules of use:

- **One VeriBench: 896 tasks, all six splits; no "Core" split and no 614-task view (Brando, 10-24-2026; restated 11-18-2026: "I don't want there to be a core vs other split every again on this. ... Idk why I keep seeing from my agents that a core exists. That's not something I ever approved."; "we only have 1 version of vb with all the splits").** Never write "Core", "VB-Core", "core 614", "614-task core", "core vs other", "core vs Industry" or "non-core", and never keep that subset alive under another name ("the 614 tasks outside IndustrySet", "non-IndustrySet tasks") as a table, a headline number or a comparison. Compute and report every number on all 896 tasks, per split plus the 896 total; when saved per-task scores cover all 896 tasks, a 614-task number is an error to recompute, never to relabel. Only when a system was truly not run on a split may a number cover fewer tasks: say so as missing coverage ("ran 614 of the 896 tasks; IndustrySet not run"), show unmeasured cells as unknown or a range, never zero, and list the missing runs. A subset is only an explicitly named, designed sample from the table above. Old file and run ids (`core_614.json`, `core_256.json`, pack `core_614`, experiments 144 to 154 `*_core614_*`) stay as identifiers only; new names never copy them. In `brando90/veribench`, `tests/test_no_core_split.py` enforces this on the paper, the rule files and new folder names.
- Write the name and the denominator together: "VB256 (256 of 896)", "VeriBench (896)".
- TinyVeriBench-256 and Tiny96 contain no IndustrySet tasks; they say nothing about IndustrySet. A TinyVeriBench-256 result does not establish a full-set result.
- IRT (item response theory) was compared against stratified sampling in experiment 116; neither VB256 nor TinyVeriBench-256 was selected by IRT, and no learned selector tested there beat a random sample.
- For new API-served runs use VB256 first (VeriBench Rule, experiment 116); all 896 on an API model need Brando's explicit go. Free local open-weight runs may use either.
- Saturation and bucket reporting: [Guideline 25](../rules/research.md#guideline-rule-25).
