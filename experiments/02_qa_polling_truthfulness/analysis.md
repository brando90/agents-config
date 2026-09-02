# Experiment 02 — Analysis: Paper Setting vs Our QA

**TLDR:** This document maps "Consensus is Not Verification" (arXiv 2603.06612)
onto our mega-QA workflow, lists where the paper's findings transfer cleanly
(markdown/config/prose PRs with no verifier) and where they don't (code PRs
with a runnable test suite), and specifies the experiments that would tell us
whether to keep, retire, or route around the current 3-judge chain.

---

## 1. What the paper actually shows

Five aggregation methods (majority vote, highest confidence, confidence-weighted,
prediction-weighted, Surprisingly Popular) tested across HLE, BoolQ, Com2Sense,
and a new forecasting benchmark (Predict-the-Future). Five open-source models,
4B–235B params. At 25× the inference cost of one sample, no method consistently
beats single-sample baselines on truthfulness. On forecasting where outcomes
postdate the cutoff, all methods are at chance.

**Mechanism (the structural part):**

1. Wisdom-of-crowds requires roughly independent errors. LLMs share training
   data, objectives, and post-training incentives — errors are highly
   correlated. On 53% of MATH questions where multiple models err, they
   converge on the *same* wrong answer. Temperature variation (0.7 vs 1.0)
   only flipped plurality answers in 2.9% of cases.

2. The "no-signal" experiment is the cleanest demonstration: 10k random
   32-character ASCII strings, forced multiple-choice A/B/C/D. Zero ground
   truth signal. Inter-model κ as high as 0.35, structure stable across
   temperatures. So the correlation is *prior*, not *knowledge*.

3. Confidence tracks the crowd, not the truth. Surprisingly Popular requires
   an "expert minority" structure that LLM populations don't reliably have;
   the diagnostic inverse-SP hits 80% on HLE but is at chance elsewhere — so
   the signal flips sign across tasks and can't function as a verifier.

**Boundary the paper draws (verbatim summary):** scaling truthfulness via
inference-time methods helps only when an external verifier exists (proof
checkers, code execution, etc.). In verifier-absent domains, the levers are:
external grounding (retrieval, tools, human feedback), genuinely diverse
training, or explicit verifiers trained on labeled evidence.

**Constructive use of consensus:** not as a *selector*, as a *warning sign* —
high agreement on hard questions flags shared blind spots and should trigger
deferral / retrieval.

---

## 2. What our QA actually does

Defined in `~/agents-config/workflows/qa-correctness.md` (Hard Rule 3) and
mega QA in `~/agents-config/INDEX_RULES.md` Trigger Rule 10:

- **Default:** A1 builds → dispatch one cross-agent reviewer A2 (Codex / CC /
  Gemini), reviewer fixes what it finds, returns single verdict.
- **Mega QA:** sequential 3-stage chain (Codex → CC → Gemini if CC built; or
  CC → Codex → Gemini if Codex built). Each stage reads the prior stage's
  improved code and adds its own fixes. Last verdict wins.

Important: it is **sequential with fix authority**, not parallel-then-vote.
That matters.

---

## 3. Where the paper's findings transfer to us

### 3a. Markdown / config / prose PRs (no verifier) — paper applies

Most of our agents-config PRs touch only markdown (rules, workflows, machine
docs, README, blog drafts). There is no test suite. Reviewers cannot execute
anything. The signal each reviewer produces is "this seems right" — exactly
the verifier-absent regime the paper analyzes.

Predicted failure mode: stages 2 and 3 mostly co-sign stage 1. Where stage 1
embedded a confident-but-wrong claim ("RAMP says X"), stages 2/3 are *more
likely* to ratify it than to challenge it, because the confident framing
matches the priors all three were trained on. Inter-stage κ on judgment
questions about prose is plausibly close to the paper's 0.35 floor even on
random text.

**This is where the paper most clearly indicts our mega-QA.** An overconfident
single-model verdict that has been ratified twice will look more authoritative
than the same verdict from a single model — but the marginal ratifications add
no real verification, just compute.

### 3b. Source-code PRs *if* tests are run — paper does not directly apply

If the reviewer actually runs the test suite on each fix, tests are an
external verifier. The reviewer is then doing what the paper allows
("verifier-anchored scaling"): generate candidates, filter by verifier. The
3-stage chain becomes 3 independent attempts to find regressions/missing
edges, each gated by `pytest` etc. Sequential improvement is preserved.

Predicted behavior: mega-QA usefully catches more real issues than single QA,
because each stage's *fix attempts* are gated by the verifier. The
ratification problem from §3a is largely defanged by the fact that "looks
good to me" is replaced by "tests pass."

**Caveat:** in practice, our reviewers often skip running the test suite on
agents-config-style repos because there's nothing to run, or skip on code
repos because the tests are slow / require GPU / require auth. When tests are
skipped, the stage degrades to the §3a regime — pure judgment.

### 3c. Source-code PRs without tests — paper applies

Same as §3a in effect: judgment-only, no verifier. The paper's argument
applies in full. This is also the regime where structural-QA
(`workflows/qa-structural.md`) operates without a clear verifier — though
metrics like CC, erosion, verbosity are partial verifiers because they're
deterministic measurements rather than judgment.

---

## 4. Where our setup *differs* from the paper (and might still help)

| Difference | Likely effect on the paper's conclusion |
|---|---|
| Sequential, not parallel | Reduces correlated-vote problem, since later stages SEE earlier outputs and might disagree explicitly. But also introduces anchoring: stage 2/3 read stage 1's framing first. |
| Each reviewer FIXES, not votes | Real fixes are real progress regardless of correlation. One reviewer correctly catching a logic bug is a win. |
| Cross-vendor (OpenAI/Anthropic/Google) | Paper's open-source family showed κ≈0.35 on no-signal. Cross-vendor agreement is plausibly lower but unmeasured for our models specifically. |
| Reviewer can read tests/lint/CI output | Adds verifier, when used. |
| Single-model fallback already specified | Workflow already degrades gracefully when only one CLI is logged in. |

The honest summary: mega-QA *is not* the parallel-vote setup the paper
disproves, but it shares enough mechanism (correlated priors, judgment-only
verdicts on prose) that we should not assume it inherits the benefits of true
verification just because it costs 3× more.

---

## 5. Constructive use of the paper

The paper's final-section suggestion — high consensus on hard questions as a
**deferral signal** — fits our workflow naturally. Concrete uses:

1. **Inter-stage agreement metric.** When all 3 mega-QA stages return PASS on
   a non-trivial diff with no fixes applied, that should *not* shorten Brando's
   review — it should flag "high agreement on a non-trivial diff: possible
   shared blind spot, please double-check yourself or pull a human reviewer."

2. **Anti-anchoring stage.** Add a stage 0 "naive" pass that does not see the
   diff's commit message or PR title, only the raw `git diff`. Compare its
   verdict to stage 3's. Wide divergence → likely framing-driven; converged
   pass → either truly clean or shared bias.

3. **Cite-or-die for prose changes.** For markdown/config-only diffs, require
   the reviewer to produce at least one citation (file:line or external URL)
   per claim it ratifies. No citation → flag as "judgment only — bias risk."

---

## 6. Proposed experiments

### Tier 1: AC-self-audit (cheap, repo-specific, fast)

**What:** Sample N = 10–30 recent merged agents-config PRs. For each PR's diff:

- Run **V1 (current mega-QA, Codex→CC→Gemini sequential)** → record verdict + fixes + tokens.
- Run **V2 (single best model, Opus 4.7 with extended thinking, mandatory
  verifier-first prompt)** → record verdict + fixes + tokens.
- Run **V3 (verifier-routed: code+tests → V1, else → V2 + grounding)** → record.

Output per PR:
- `flagged_issues_v1`, `flagged_issues_v2`, `flagged_issues_v3` (lists)
- `fixes_applied_v{1,2,3}` (diffs)
- `tokens_v{1,2,3}` (cost)
- `wall_time_v{1,2,3}` (latency)

**Then:** vibe-check script picks 5 best examples (where V1 and V2 most
disagree, ranked by fix-diff size) and writes them to a file with side-by-side
flagged issues, awaiting Brando's blind rating "which set is more useful: A,
B, or tie." Brando's rating is then compared to a per-PR auto-rating produced
by an extra Opus-4.7 judge — agreement between Brando and the judge is
recorded so future rounds can be auto-scored.

**Falsifies:** H2 (markdown/config: V1 ≈ V2 in usefulness) and H4 (high
agreement = blind spot, not pass).

**Cost:** ~10 PRs × 3 setups × ~50k tokens ≈ 1.5M tokens. Cheap.

### Tier 2: SWE-bench Verified slice (medium, public benchmark)

**What:** Run a **20-instance slice** of SWE-bench Verified end-to-end with
each QA setup wrapping a single CC builder. Measure %resolved + tokens +
wall-clock.

- Setup A: CC builder, no QA gate (pure baseline).
- Setup B: CC builder + V1 mega-QA gate before patch submit.
- Setup C: CC builder + V2 single-judge gate.
- Setup D: CC builder + V3 routed gate.

**Metric:** SWE-bench Verified `resolved_rate`, plus token cost ratio and
wall-clock ratio vs Setup A.

**Falsifies:** H1 (V1 ≈ V2 on verifier-anchored code).

**Cost:** ~20 instances × 4 setups, several hours each, several million
tokens. This is the expensive one — only worth running once we've justified it
with Tier 1.

**Why a 20-instance slice and not full SWE-bench Verified:** the cost of full
500-instance SWE-bench Verified would be tens of thousands of dollars across
4 setups. A 20-instance stratified slice (5 easy / 10 medium / 5 hard by
resolved-rate decile) is enough to spot a 15+ percentage-point difference at
80% power, which is the size of effect that would actually change our
behavior. If the slice shows a meaningful gap, we expand.

### Tier 3: Bug-injection (validates H3)

**What:** Take 20 already-reviewed `agents-config` PRs that previously passed
mega-QA. Inject one of these planted issues into each:

- Subtle factual error in a rule ("rerun every 5h" → "every 50h")
- Off-by-one in a path (`scratch0` → `scratch1`)
- Inverted boolean in a script (`if not foo` → `if foo`)
- Broken markdown link
- Plausible-but-wrong citation

Run V1 and V2 on each modified PR. Measure:
- Detection rate per setup
- Detection rate of *the planted issue specifically* (not just "any flag")
- Inter-stage agreement on the missed cases

**Falsifies:** H3 (≥30% of planted issues missed by all 3 reviewers in the
mega-QA chain).

**Cost:** Cheaper than Tier 2 — same per-PR cost as Tier 1, no SWE-bench env.

---

## 7. Threats to validity

1. **Sample is our own past PRs.** If past PRs were already filtered through
   mega-QA, the "missed issues" rate underestimates true mega-QA misses
   (selection effect). Mitigation: also include unmerged drafts and PRs from
   feature branches that never made it.

2. **Vibe-check rater is the same human who designed the prompts.** Brando is
   not blind to which arm is V1 vs V2. Mitigation: the vibe-check script
   randomizes which arm is labeled "A" vs "B" per example and stores the
   mapping separately so the rating is at least order-blind.

3. **Single-model V2 still has the same correlated-prior problem internally.**
   Replacing 3 Anthropic-flavored verdicts with 1 Anthropic-flavored verdict
   doesn't escape the priors; it just stops paying for the ratifications.
   That's the *point* — we want to know whether the extra ratifications are
   worth the cost, not whether the single verdict is unbiased.

4. **SWE-bench Verified is leaky.** Recent reports of test-set contamination
   in some training data mean the absolute resolved-rates may be inflated.
   Mitigation: we only care about the *relative* difference between QA
   setups, not absolute SWE-bench scores.

5. **Mega-QA value may live in long-running iterative work, not single PRs.**
   The paper studies single-question truthfulness; SlopCodeBench (sibling
   experiment 00) studies long-horizon degradation. Single-PR benchmarks may
   miss the compounding case where mega-QA prevents downstream rot. Tier 3
   bug-injection only partially captures this.

---

## 8. Decision criteria (what we'd actually do with the result)

| Outcome | Action |
|---|---|
| Tier 1 shows V2 ≥ V1 usefulness on markdown/config PRs (Brando's blind rating + auto-judge agree) | Switch markdown/config QA to V2; keep mega-QA only for code with tests. |
| Tier 1 shows V1 noticeably better on prose | Keep V1 but add the deferral / cite-or-die / anti-anchoring stages from §5. |
| Tier 2 shows Setup B/D > Setup C on SWE-bench slice | Mega-QA pays for itself on verifier-anchored code; keep it there. |
| Tier 2 shows Setup C ≈ Setup B/D | Even on verifier-anchored code, single best-model + tests is enough; downgrade default. |
| Tier 3 shows ≥30% planted-issue miss-rate by all 3 reviewers | Add bug-injection regression to CI; treat mega-QA PASS on non-trivial diffs as deferral signal not pass signal. |

---

## 9. References

- Paper: "Consensus is Not Verification: Why Crowd Wisdom Strategies Fail for
  LLM Truthfulness," arXiv:2603.06612.
- Current QA: `~/agents-config/workflows/qa-correctness.md`.
- Current structural QA: `~/agents-config/workflows/qa-structural.md`.
- Sibling experiment 00 (degradation): `~/agents-config/experiments/00_refactor_qa_gate/`.
- SWE-bench Verified: https://www.swebench.com/.
