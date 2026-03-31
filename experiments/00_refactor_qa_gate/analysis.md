# Experiment 00: Refactoring QA Gate — Analysis

## Motivation

SlopCodeBench (Orlanski et al., 2026, arXiv:2603.24755) demonstrates that when
coding agents iteratively extend their own prior code, structural quality degrades
monotonically:

- **Erosion** (complexity concentration in high-CC functions) rises in 80% of trajectories
- **Verbosity** (redundant/duplicated code) rises in 89.8%
- Agent code is **2.2x more verbose** and markedly more eroded than 48 maintained human repos
- **Human code stays flat** over the same trajectory length; agent code worsens every iteration
- No agent solves any of the 20 problems end-to-end; the best strict solve rate is 17.2% (Opus 4.6)

The paper's most actionable finding: **prompt-side interventions (anti_slop, plan_first)
lower the initial quality intercept by ~34% but do not change the degradation slope**
(Section 4.3, Figure 5). Degradation resumes at the same rate once iteration begins.

The paper concludes: "interventions that enforce structural discipline across
checkpoints, whether at training time or through tooling, remain untested."

This experiment designs a tooling-side intervention: a refactoring QA gate that
runs between implementation iterations, hypothesized to reduce (not necessarily
arrest) the degradation slope. Whether it actually bends the slope is untested.

### RAMP: Why committed config is the highest-ROI intervention

RAMP (Denisov-Blanch, Agarwal, Azaletskiy, He, Schaeffer, Miranda, Vasilescu,
Koyejo, ASE 2026) provides complementary evidence from 508 repos in a staggered
difference-in-differences study of coding agent adoption:

- Repos **without** committed AI config (Level 1) see **~3.3x more** complexity
  growth and **~3.4x more** warning increases than repos with config (Level 2+)
- Duplication: ~33% increase at L1 vs. near-zero at L2+
- Velocity gains (~26% more commits) are **identical** regardless of config level
- **80% of AI config is set-and-forget** — committed once, never modified
- The **L1→L2 gap** (nothing vs. basic rules+standards) is larger than L2→L3→L4

This means the single highest-ROI action is ensuring the repo has committed
rules and coding standards *before* any code refactoring. The v3 prompt adds
a Phase -1 (Configuration Audit) to check this first.

## Relevance to agents-config

Our agents-config workflow (~/agent-config/) uses cross-agent QA gating
(`~/agent-config/workflows/qa-correctness.md`) but that gate focuses on
**correctness** — logic errors,
missing edge cases, broken behavior. It does not measure or address **structural
quality degradation**, which is the compounding problem the paper identifies.

The concern is that as CC and Codex agents iteratively extend code in our managed
repos (~/vb/, etc.), the exact pattern documented in SlopCodeBench is occurring:
god functions accumulate branches, duplication grows, and each iteration makes the
next one harder. The correctness gate doesn't catch this because the code still
passes tests.

## What the v2 prompt changes (vs. v1)

| Issue in v1 | Paper evidence | Fix in v2 |
|---|---|---|
| Estimates CC ("likely above 10") | Paper uses CC > 10 threshold following Radon's established bounds (Section 2.3) | Phase 0: run radon, compute exact scores |
| No quantitative before/after | Paper defines erosion (Eq. 3) and verbosity (Eq. 4) precisely | Phase 0 baseline + Phase 4 recompute with comparison table |
| Only local cleanup, no architectural review | Early architectural decisions compound (Section 2.2, 4.1: main() goes 84→1099 lines) | Phase 1 item 4: flag architectural dead-ends for human decision |
| "Extract helpers" without guard | Paper's anti_slop warns against "a ton of helper methods" | Explicit "don't over-extract" and "no new abstractions for single-use cases" constraints |
| No triggering guidance | Paper shows degradation is monotonic (Figure 3) | Header: "run after every non-trivial feature addition" |
| Missing clone detection | Verbosity = |AST-grep violations UNION clone lines| / LOC with dedup (Eq. 4); paper uses 137 targeted rules | Phase 0: explicit clone detection step (SlopCodeBench-inspired proxy, not exact replication) |
| No diff budget | Unbounded refactoring can introduce churn | Phase 2: ~100 line diff budget per item, prioritize by mass |
| No priority ordering | Erosion (complexity concentration) is the dominant signal | Phase 1 orders by mass(f); Phase 3 says work highest-mass first |
| "Structurduplication" typo | — | Fixed |

## Key design decisions

1. **Phase 0 (Measure Baseline) is new and critical.** Without quantitative
   measurement, you can't tell if the gate is working across iterations. This
   is the difference between "we feel like the code is cleaner" and "erosion
   dropped from 0.74 to 0.52."

2. **Architectural dead-ends are flagged but not fixed.** The paper shows that
   the deepest degradation comes from early structural decisions (e.g.,
   hardcoding language dispatch at C1 forces rewrites at C2 and C5). A
   refactoring agent shouldn't unilaterally redesign the architecture, but it
   should surface the problem so a human can decide.

3. **Diff budget prevents the gate itself from introducing slop.** A refactoring
   pass that touches 500 lines is itself a source of future complexity. The
   budget forces the agent to prioritize high-impact, low-churn changes.

4. **Priority by mass, not line count.** The paper's mass formula
   (CC * sqrt(SLOC)) correctly weights a 40-line function with CC=25 higher
   than a 100-line function with CC=5. The prompt follows this.

## Evaluation plan (proposed)

To validate whether this gate actually bends the degradation slope (not just
the intercept), we need a controlled experiment:

**Design:** A/B across agent-driven implementation iterations on the same tasks.
- **Control:** Agent extends code iteratively with the existing QA gate (correctness only).
- **Treatment:** Same, but the refactoring QA gate runs between each iteration.

**Repos/tasks:** Select 2-3 repos with substantial Python source code (not
agents-config itself, which is markdown-heavy). Ideal candidates: repos where
agents have already performed multi-iteration feature work so we have a baseline
trajectory to compare against.

**Metrics per iteration:**
1. Erosion (Eq. 3) — primary outcome
2. Verbosity proxy (Eq. 4 approximation) — secondary outcome
3. Test pass rate — safety check (must not degrade)
4. Diff size of the refactoring pass — cost measure
5. Wall-clock time / token cost — practical cost

**Iteration horizon:** Minimum 5 iterations per condition to see slope effects
(the paper uses 3-8 checkpoints per problem, with degradation visible by Mid).

**Success criteria:**
- The treatment group's erosion slope (erosion increase per iteration) is
  statistically lower than the control group's (paired t-test or Wilcoxon, p < 0.05).
- Test pass rates do not differ between groups (non-inferiority).
- Refactoring gate cost per iteration stays below 50% of the implementation cost.

**Acceptable tradeoff:** If the gate reduces erosion slope by >= 30% relative
to control, it's worth the cost even if verbosity improvement is smaller.

---

## Open questions

1. **Frequency:** How often should the gate run? After every commit? Every N
   features? The paper doesn't test intermediate frequencies — only the
   endpoints (no gate vs. prompt-only). Empirically determining the optimal
   frequency for our workflow is future work.

2. **Language coverage:** The prompt assumes Python-centric tooling (radon,
   ast-grep). For markdown-heavy repos like agents-config itself, we may need
   different quality signals (e.g., structural consistency, cross-reference
   accuracy, rule redundancy).

3. **Does it actually bend the slope?** The paper shows prompts don't. Tooling
   might. But we won't know until we measure erosion/verbosity across multiple
   iterations with and without the gate. This is the experiment to run.

4. **Integration with existing QA gating:** Resolved — implemented as a separate
   workflow (`~/agent-config/workflows/qa-structural.md`) forming step 2 of the
   QA chain after `~/agent-config/workflows/qa-correctness.md`. Kept separate
   because it has a different purpose (structural quality vs. correctness) and
   different skip conditions.

## References

- Orlanski, G., Roy, D., Yun, A., Shin, C., Gu, A., Ge, A., Adila, D., Sala, F.,
  & Albarghouthi, A. (2026). SlopCodeBench: Benchmarking How Coding Agents Degrade
  Over Long-Horizon Iterative Tasks. arXiv:2603.24755.
- Denisov-Blanch, Y., Agarwal, S., Azaletskiy, P., He, H., Schaeffer, R.,
  Miranda, B., Vasilescu, B., & Koyejo, S. (2026). Repository AI Configuration Is
  Associated with Three-Fold Differences in Code Quality After Agent Adoption. ASE 2026.
- Existing correctness QA workflow: `~/agent-config/workflows/qa-correctness.md`
- Refactoring QA gate prompt v1: `~/agent-config/experiments/00_refactor_qa_gate/cc_prompt.md`
- Refactoring QA gate prompt v2: `~/agent-config/experiments/00_refactor_qa_gate/refactor_qa_gate_prompt_v2.md`
- Refactoring QA gate prompt v3 (consolidated): `~/agent-config/experiments/00_refactor_qa_gate/refactor_qa_gate_prompt_v3.md`
