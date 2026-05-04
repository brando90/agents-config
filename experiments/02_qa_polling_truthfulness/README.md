# Experiment 02 — QA Polling vs Truthfulness

**TLDR:** Paper "Consensus is Not Verification" (arXiv 2603.06612) shows that polling
multiple LLM samples does not improve truthfulness in verifier-absent domains
because LLM errors are structurally correlated. Our mega-QA (Codex → CC → Gemini
sequential chain with fix authority) overlaps with that failure mode for
markdown/config/prose changes (no verifier) but diverges for source-code changes
(tests act as verifier). This experiment quantifies whether mega-QA is actually
adding value over a single best-model reviewer in our workflow, both on a public
benchmark (SWE-bench Verified slice) and on our own past PRs (ac-self-audit),
with a paired vibe-check so the quantitative number can be cross-checked against
Brando's own qualitative judgment.

---

## Why this exists

Today's gate (`~/agents-config/workflows/qa-correctness.md` Hard Rule 3 + mega
QA Trigger Rule 10) defaults to:

- **Default QA:** dispatch one independent reviewer (cross-model).
- **Mega QA:** sequential 3-stage chain (Codex → CC → Gemini), each reviewer
  reads the prior reviewer's fixes and applies its own.

The paper's argument: aggregation over correlated samples does not produce a
verifier. Even on 10,000 random ASCII strings (zero ground-truth signal),
inter-model agreement was κ ≈ 0.35 — correlated *priors*, not correlated
*knowledge*. Confidence tracks the crowd, not the truth. Surprisingly Popular
flips sign across tasks. The boundary the paper draws: scaling helps only when
an external verifier exists.

So the natural question for our workflow: which of our QA invocations actually
pass through a verifier, and which are pure cross-model voting under another
name?

---

## Hypotheses

| ID | Statement | Falsifiable? |
|----|-----------|---|
| H1 | On code-only diffs with a runnable test suite, mega-QA's PR pass-rate ≈ single-best-model + tests at lower cost. | Yes — measure on SWE-bench Verified slice. |
| H2 | On markdown/config-only diffs, mega-QA's "issues caught" ≈ single best model; the extra 2 reviewers mostly co-sign. | Yes — ac-self-audit on past markdown-only PRs. |
| H3 | On a manufactured set of subtly-bad PRs (planted bugs / planted bad rule edits), all 3 reviewers miss the same ≥30% of cases. | Yes — bug-injection variant of ac-self-audit. |
| H4 | High inter-reviewer agreement on hard questions correlates with shared blind spots, not correctness — usable as a *defer signal*, not a *pass signal*. | Yes — measure agreement vs ground-truth when ground truth exists. |

If H1+H2 hold, we should keep cross-agent QA only when the diff touches
verifiable code, and fall back to single-best-model + grounding (links/tests)
otherwise.

---

## Paper setting vs ours (one-glance)

| Axis | Paper | Our mega-QA |
|------|-------|---|
| Aggregation | Parallel, K=5–25 samples | Sequential, K=3 stages |
| Decision rule | Vote / pick most-confident | Each reviewer fixes; last verdict wins |
| Models | Same/similar family, same prompt | Cross-vendor (OpenAI/Anthropic/Google) |
| Verifier | None (HLE / BoolQ / Com2Sense / forecasting) | Test suite *when run* — often skipped on docs/config |
| Outcome predicted by paper | Aggregation ≈ single sample, sometimes worse | Open question — depends on whether tests run |

**Where paper most clearly applies to us:** markdown/config-only PRs in
agents-config itself (no tests, no verifier, all judgment). That is a *lot* of
our PRs.

**Where paper least clearly applies:** source-code PRs in `~/veribench/`,
`~/ultimate-utils/` etc. where tests/lint/type-check provide an external
verifier *if the reviewer actually runs them*.

See `analysis.md` for full breakdown.

---

## What's in this directory

- `analysis.md` — full paper-vs-ours diff, design decisions, threats to validity.
- `prompts/qa_v1_polling_baseline.md` — current mega-QA, restated as the control arm.
- `prompts/qa_v2_verifier_first.md` — single best-model + mandatory verifier; treatment arm.
- `prompts/qa_v3_verifier_routed.md` — adaptive: code+tests → ensemble OK, otherwise → single+grounding.
- `bench/README.md` — how to run.
- `bench/run_swe_slice.sh` — SWE-bench Verified slice runner (default 20 instances). Tier 2.
- `bench/run_ac_self_audit.py` — replays N past `agents-config` PRs through V1 vs V2 vs V3. Tier 1.
- `bench/run_bug_injection.py` — plants known bugs in past PRs to measure the H3 miss-rate. Tier 3.
- `bench/vibe_check.py` — selects K best/worst examples for Brando's eyeball pass + auto-agreement.

---

## Quick-start

```bash
# Cheap, repo-specific (~30 min, ~1.5M tokens total = ~150k/PR across V1+V2+V3):
python ~/agents-config/experiments/02_qa_polling_truthfulness/bench/run_ac_self_audit.py \
    --n 10 --out ~/dfs/qa-polling-results/ac-self/

# Vibe check (writes 5 best/worst examples for human inspection):
python ~/agents-config/experiments/02_qa_polling_truthfulness/bench/vibe_check.py \
    --in ~/dfs/qa-polling-results/ac-self/ --out ~/dfs/qa-polling-results/vibe/

# Adversarial: plant known bugs in past PRs and see what V1 / V2 catch (Tier 3):
python ~/agents-config/experiments/02_qa_polling_truthfulness/bench/run_bug_injection.py \
    --n 20 --out ~/dfs/qa-polling-results/bug-injection/

# Public benchmark (slower, ~2-4h, requires SWE-bench-Verified env):
bash ~/agents-config/experiments/02_qa_polling_truthfulness/bench/run_swe_slice.sh \
    --n 20 --out ~/dfs/qa-polling-results/swe-slice/
```

---

## References

- Paper (this experiment's motivator): "Consensus is Not Verification: Why
  Crowd Wisdom Strategies Fail for LLM Truthfulness," arXiv:2603.06612.
- Existing QA workflow: `~/agents-config/workflows/qa-correctness.md`.
- Existing structural QA: `~/agents-config/workflows/qa-structural.md`.
- Sibling experiment: `~/agents-config/experiments/00_refactor_qa_gate/`
  (SlopCodeBench + RAMP — degradation gate, complementary motivation).
