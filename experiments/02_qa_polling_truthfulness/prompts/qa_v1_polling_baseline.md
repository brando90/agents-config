# QA Prompt v1 — Polling Baseline (Control Arm)

**TLDR:** This is the current mega-QA chain (Codex → CC → Gemini sequential,
each with fix authority), restated verbatim as the **control arm** for
experiment 02. Identical to `~/agents-config/workflows/qa-correctness.md`
mega-QA so any change in measured usefulness can only be attributed to V2/V3,
not to a prompt difference inside V1.

---

## When this is used

V1 is the baseline that V2 (single-judge + verifier) and V3 (verifier-routed)
are compared against. Do **not** edit V1 to "fix" issues you find — V1 must
match production mega-QA exactly so the comparison is fair. If production
mega-QA changes, copy the new version here and bump to v1.1.

## Pinned source-of-truth references

- Reviewer dispatch: `~/agents-config/workflows/qa-correctness.md`
- Mega-QA chain: `~/agents-config/INDEX_RULES.md` Trigger Rule 10
- Verdict format (must match exactly): see "Verdict Format" below.

---

## V1 chain (production mega-QA, restated)

Three sequential stages. Each stage runs the same prompt on the code as
improved by the previous stage. Last verdict wins.

| Stage | Reviewer | Role |
|---|---|---|
| 1 | Codex (or CC if Codex built) | First independent reviewer |
| 2 | The builder (CC or Codex) | Knows intent best, verifies stage 1's fixes |
| 3 | Gemini | Clean-eyes final pass |

If a reviewer CLI is unavailable, fall back per `qa-correctness.md` § Single-model
fallback: re-dispatch with the next available CLI; never use API keys.

---

## Per-stage prompt (verbatim)

```
Review all changes in this directory since the last commit on main.

CORRECTNESS: Flag and fix critical and major issues — logic errors, missing
edge cases, incorrect behavior, inconsistencies with project agent docs (for
example ~/your-project/docs/agent-docs/, if present).

STRUCTURAL (skip for markdown-only repos): Check for god functions (CC > 10
or >60 lines), structural duplication, verbose anti-patterns (single-use vars,
identity wrappers, defensive checks for impossible states, 3+ nesting,
if/elif ladders, dead code). Fix what you find. Preserve public interfaces.
Run tests after each change — revert and skip if tests break.

You are empowered to fix issues directly. Apply minimal fixes only.

End with exactly:
VERDICT: PASS | FAIL | FIXED
CRITICAL_ISSUES: [count]
MAJOR_ISSUES: [count]
FIXES_APPLIED: [count]
STRUCTURAL: PASS | IMPROVED | SKIP
SUMMARY: [1-2 sentences]
If everything looks correct, use PASS with all counts 0.
```

---

## Logging requirements (for experiment 02)

Each stage must additionally emit, to `stderr` or a sidecar JSON, the
following so the bench scripts can parse:

```json
{
  "stage": 1 | 2 | 3,
  "reviewer": "codex" | "cc" | "gemini",
  "verdict": "PASS" | "FAIL" | "FIXED",
  "critical_issues": <int>,
  "major_issues": <int>,
  "fixes_applied": <int>,
  "structural": "PASS" | "IMPROVED" | "SKIP",
  "summary": "<string>",
  "flagged_issues": [{"file": "<path>", "line": <int|null>, "claim": "<str>"}],
  "applied_fix_diff": "<unified diff or null>",
  "tokens_in": <int>,
  "tokens_out": <int>,
  "wall_time_s": <float>
}
```

This shape is what `bench/run_ac_self_audit.py` expects. The verdict block in
plain text remains unchanged so production behavior is unaffected.

---

## Notes for experimenters

- **Do not patch V1 to fix prompt bugs you spot here.** Open a separate PR
  against `workflows/qa-correctness.md` if you want to change production. V1
  exists as a fixed reference point.
- **V1 may print "STRUCTURAL: SKIP" on markdown repos.** That's expected and
  is not a bug.
- **Budget:** typical V1 run on a small markdown-only PR is ~20-30k tokens
  per stage = ~60-90k total. Code PRs with substantial diff can run ~150-300k
  total.
