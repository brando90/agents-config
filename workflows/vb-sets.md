# VeriBench set names

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/vb-sets.md>

**TLDR:** Use these names, and only these, for VeriBench task sets in prompts, reports and run labels. "Small" is not a name of any set; say TinyVeriBench-256 or the full set. VeriBench has no "Core" split (see below).

| Name | What it is | Size | Where the task list lives |
|---|---|---|---|
| **VeriBench** (full, V1) | Release `veribench@1.3`: six splits, EasySet 41, CSSet 25, HumanEval 56, RealCodeSet 32, SecuritySet 460, IndustrySet 282 | 896 | Harbor registry `veribench@1.3`; `brando90/veribench` |
| **IndustrySet** | One of the six splits (not a second half of the benchmark) | 282 | `experiments/116_tiny_vbv1_subset_selection_and_frontier_validation/expt_v1/manifests/industry_282.json` |
| **TinyVeriBench-256** (named by Brando 10-22-2026; formerly "Tiny256") | A stratified 256 of the 614 tasks outside IndustrySet (experiment 116; re-validation against all 896 tasks and every split is in progress, 11-2026): five source categories x two AST-size halves, seed 20261015, chosen from public metadata only, no scores; not a new sample. tinyBenchmarks-style subset study; status "pilot, not frontier validated" | 256 | `.../expt_v1/manifests/core_256.json` |
| **Tiny96** | The earlier 96-task nested pilot of TinyVeriBench-256 (same design) | 96 | `.../expt_v1/manifests/core_96.json` |
| **VeriBench-Infinity** (VB-Inf, VBV3) | Differential proving against curated Lean references for correct and deliberately incorrect Python variants | 24 pairs | [Current task packages on main](https://github.com/brando90/veribench-inf/tree/main/tasks) |
| **VB private** | Vals/BMG held-out set; target 180 accepted tasks, separate from the public set | 180 target | `brando90/vb-priv-bmg` (not public) |

The GitHub repository is `brando90/veribench-inf` (previous GitHub names: `veribench-dt` and `veribench-infinity`). VeriBench-DT refers to the earlier differential-testing work. Differential testing is planned for V1 and VeriBench Private. There is currently no private differential-proving edition (`vb-priv-inf`).

Rules of use:

- **No "Core" split, ever (Brando, 10-24-2026; restated 11-18-2026: "I don't want there to be a core vs other split every again on this. ... Idk why I keep seeing from my agents that a core exists. That's not something I ever approved.").** Never write "Core", "VB-Core", "core 614", "614-task core", "core vs other", "core vs Industry" or "non-core". Report per split plus the 896 total; a smaller set is named exactly ("the 614 tasks outside IndustrySet; IndustrySet not run", TinyVeriBench-256) and never presented as the benchmark. Old file and run ids (`core_614.json`, `core_256.json`, pack `core_614`, experiments 144 to 154 `*_core614_*`) stay as identifiers only; new names never copy them.
- Write the name and the denominator together: "TinyVeriBench-256 (256 of 896)", "VeriBench (896)".
- TinyVeriBench-256 and Tiny96 contain no IndustrySet tasks; they say nothing about IndustrySet. A TinyVeriBench-256 result does not establish a full-set result.
- IRT (item response theory) was compared against stratified sampling in experiment 116; TinyVeriBench-256 itself was not selected by IRT.
- For new API-served runs use TinyVeriBench-256 first (VeriBench Rule, experiment 116); all 896 on an API model need Brando's explicit go. Free local open-weight runs may use either.
- Saturation and bucket reporting: [Guideline 25](../rules/research.md#guideline-rule-25).
