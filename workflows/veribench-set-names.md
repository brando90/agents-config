# VeriBench set names

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/veribench-set-names.md>

**TLDR:** Use these names, and only these, for VeriBench task sets in prompts, reports and run labels. "Small" is not a name of any set; say Tiny256 or the full set.

| Name | What it is | Size | Where the task list lives |
|---|---|---|---|
| **VeriBench** (full, V1) | Release `veribench@1.3` = Core + Industry | 896 | Harbor registry `veribench@1.3`; `brando90/veribench` |
| **VB-Core** | The canonical 614-task core | 614 | `experiments/116_tiny_vbv1_subset_selection_and_frontier_validation/expt_v1/manifests/core_614.json` |
| **VB-Industry** | The IndustrySet | 282 | `.../expt_v1/manifests/industry_282.json` |
| **Tiny256** | Stratified probability sample of VB-Core (five source categories x two AST-size halves, seed 20261015, chosen from public metadata only, no scores). Nested inside the 614. Experiment 116, tinyBenchmarks-style subset study; status "pilot, not frontier validated" | 256 | `.../expt_v1/manifests/core_256.json` |
| **Tiny96** | The earlier 96-task nested pilot of Tiny256 (same design) | 96 | `.../expt_v1/manifests/core_96.json` |
| **VB-Infinity** | VBV3 / `brando90/veribench-dt`: 24 source tasks x correct/incorrect Python, three agent stages | 24 pairs | branch `paper/current-iclr-2027-20260925` of `brando90/veribench-dt` (not on main) |
| **VB private** | Vals/BMG held-out set; target 180 accepted tasks, separate from the public set | 180 target | `brando90/vb-priv-bmg` (not public) |

Rules of use:

- Write the name and the denominator together: "Tiny256 (256 of 896)", "VeriBench (896)".
- Tiny256 and Tiny96 contain Core tasks only; they say nothing about VB-Industry. A Tiny256 result does not establish a full-set result.
- IRT (item response theory) was compared against stratified sampling in experiment 116; Tiny256 itself was not selected by IRT.
- For new API-served runs use Tiny256 first (VeriBench Rule, experiment 116); all 896 on an API model need Brando's explicit go. Free local open-weight runs may use either.
- Saturation and bucket reporting: [Guideline 25](../rules/research.md#guideline-rule-25).
