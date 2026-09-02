# QA Prompt v2 — Single Best-Model + Verifier-First (Treatment Arm)

**TLDR:** One reviewer (best-available model with extended thinking), required
to either run an external verifier (tests / lint / type-check / build) **or**
produce explicit citations (file:line, URL) for every claim it ratifies.
Removes the cross-model ratification step the paper suggests is mostly
correlated noise.

---

## Why this exists

Per `analysis.md` §1–§3, the paper's failure mode is "verifier-absent +
correlated priors." V2's design rule: never ratify a verdict by stacking
correlated judgments. Either the verdict is anchored to a verifier (tests,
lint, type-check, build, deterministic measurement), or it is anchored to a
citation (a specific file:line or URL the human can check). If neither is
possible, the verdict is downgraded from PASS/FIXED to **DEFER** — explicit
flag for human review.

---

## Reviewer dispatch

- **Single reviewer:** best available CLI in current environment.
  - Preference: `clauded -p` with Opus 4.7 + extended thinking enabled.
  - Fallback: `codex exec --full-auto` on best Codex model.
  - Last resort: `gemini -p`.
- **No second or third stage.** That's the entire point of the treatment.
- **Cost target:** roughly 2× a single V1 stage (extended thinking + verifier
  invocation) but still ~⅔ to ½ the cost of full V1 mega-QA.

---

## Per-run prompt (verbatim)

```
Review all changes in this directory since the last commit on main.

You are the SOLE reviewer for this diff. There is no second pass. Your verdict
is final. Adjust your standards accordingly: do not assume someone else will
catch what you miss.

GROUND RULES:

1. VERIFIER FIRST. Before forming any verdict on correctness, identify what
   external verifier(s) are applicable to this diff and run them:
     - Source code: tests (pytest / npm test / cargo test), linter, type
       checker, build. Run what exists. Do not skip because slow — set a
       timeout and report partial results if needed.
     - Markdown / config: link checker, schema validator, structural metrics
       (radon for any .py touched), `git grep` for cross-references that the
       diff might have broken.
     - If NO external verifier is applicable, say so explicitly in the
       SUMMARY.
   Record verifier output in your report.

2. CITE OR DEFER. For every CRITICAL or MAJOR issue you flag, include either:
     (a) a verifier output excerpt that demonstrates the issue, or
     (b) a file:line citation that the human can open and read.
   For every PASS verdict you give on a non-trivial diff, include either:
     (a) verifier output showing the relevant tests/checks pass, or
     (b) at least one file:line citation showing you actually read the
         changed code (not just the commit message).
   If you cannot produce either for a major question, escalate the verdict
   to DEFER with a one-line "what would resolve this" note.

3. ANTI-ANCHORING. Read the raw `git diff` BEFORE reading the commit message,
   PR title, or any TLDR the author wrote. If after reading the diff your
   independent read disagrees with the author's framing, say so. The crowd
   prior is what makes correlated reviewers ratify wrong things — your job is
   to disagree when warranted.

4. CONSENSUS-AS-DEFERRAL. If you find yourself agreeing with the diff on
   every non-trivial point with high confidence and you did not run any
   verifier (e.g., markdown-only PR), append a "consensus warning" to your
   SUMMARY: "high agreement, no verifier — please double-check." This is not
   a FAIL; it is honest signal that you are doing judgment-only review.

5. FIX, DON'T REWRITE. Same rules as V1: minimal fixes, preserve public
   interfaces, revert any fix that breaks tests.

STRUCTURAL (skip for markdown-only repos): Check for god functions (CC > 10
or >60 lines), structural duplication, verbose anti-patterns. Apply the same
"verifier or cite" rule — if you flag a god function, give file:line + the
exact CC number from radon, not "feels too long."

End with exactly:
VERDICT: PASS | FAIL | FIXED | DEFER
CRITICAL_ISSUES: [count]
MAJOR_ISSUES: [count]
FIXES_APPLIED: [count]
STRUCTURAL: PASS | IMPROVED | SKIP
VERIFIER_RAN: [list of tools actually invoked, or "none — judgment only"]
CONSENSUS_WARNING: [yes | no | n/a]
SUMMARY: [1-2 sentences. Include "judgment only" if VERIFIER_RAN is none.]
```

---

## What changed vs V1, in one column

- **One stage, not three.** Stops paying for ratification of correlated
  priors.
- **Verifier output is mandatory when applicable.** Closes the "tests
  skipped" loophole that collapses V1 to judgment-only.
- **Citations mandatory for every flag and every non-trivial PASS.** Forces
  the reviewer to look at code, not just the framing.
- **DEFER is a first-class verdict.** Honest acknowledgment that some PRs
  cannot be reviewed without a human.
- **CONSENSUS_WARNING flag.** Constructive use of the paper's "high agreement
  on hard questions = blind spot" finding.
- **VERIFIER_RAN is logged.** Lets the bench script slice results by "did
  the reviewer actually have a verifier."

---

## Logging requirements (for experiment 02)

Same JSON shape as V1's logging requirements, plus:

```json
{
  "verdict": "PASS" | "FAIL" | "FIXED" | "DEFER",
  "verifier_ran": ["pytest", "ruff", ...] | "none",
  "consensus_warning": true | false,
  "citations": [{"file": "<path>", "line": <int>, "claim": "<str>"}, ...]
}
```

The bench script uses `verifier_ran == "none"` as the key slicing variable —
those are the rows where the paper's argument applies most cleanly.
