# Expanded review: model fallback policy

**TLDR-start:** Three explicitly requested, sequential quality assurance (QA) stages completed: FIXED → PASS → PASS. All completed reviewers used GPT-6 Astra at verified `ultra` effort; Claude Fable's usage-credit failures required strongest-model same-company substitutions for stages 1 and 3, so this is not a completed cross-company review.

**Status:** REVIEW COMPLETE — zero unresolved critical or major findings
**Created:** 2026-09-10 17:40 PDT
**Last updated:** 2026-09-10 18:01 PDT

## Scope and acceptance

The review covered the complete policy change from original base `878458fa66c7d50f8849cc9a58cf2690b0b7a709` through [implementation commit `4a1aab4`](https://github.com/brando90/agents-config/commit/4a1aab49fcac94f89fcc569dfa11a6025bb96e90), including each preceding stage's uncommitted fixes. Eight policy documents were in scope; the [earlier implementation review](review-fallback-policy-2026-09-10.md) remains historical evidence and was not rewritten.

This is a critical shared policy change. The user requested three review stages, and each required a strongest-model acceptance review. The actual desktop builder was `gpt-6-astra` / `xhigh`; the explicitly dispatched design advice and all three completed stages used `gpt-6-astra` / `ultra`. The earlier incomplete smaller-Claude critique does not count as acceptance. No weaker reviewer, raw provider key, or additional review round was used in this expanded review.

## Completed stages

| Stage | Requested reviewer | Actual acceptance reviewer | Result |
|---|---|---|---|
| 1: initial independent review | `claude-fable-5-1`, `max` | `gpt-6-astra`, `ultra` | FIXED: 3 fixes; 0 unresolved critical/major findings |
| 2: builder-side review | `gpt-6-astra`, `ultra` | `gpt-6-astra`, `ultra` | PASS: 0 findings or edits |
| 3: final fresh review | `claude-fable-5-1`, `max` | `gpt-6-astra`, `ultra` | PASS: 0 findings or edits |

Fable returned “You're out of usage credits” in both attempts, with an empty model-usage record and no partial policy edits. This establishes failure of the attempted Fable calls, not exhaustion of every Claude model. Each affected stage then completed with a fresh strongest-model Codex substitute, within its original three-invocation ceiling. The completed chain was Astra → Astra → Astra; fresh contexts provide separate examinations, but do not establish cross-company independence.

The coordinator verified actual model and effort from local `turn_context` metadata rather than inferring them from the requested command. All three completed command-line processes exited 0. Session identifiers:

| Stage | Codex session identifier | Verified model / effort |
|---|---|---|
| 1 | `01a08de8-9a7a-7553-957a-32250cdb2269` | `gpt-6-astra` / `ultra` |
| 2 | `01a08dee-af3d-7a62-8c23-dd4b94f0939c` | `gpt-6-astra` / `ultra` |
| 3 | `01a08df5-e1b9-78e2-9666-3d27f3faf1c1` | `gpt-6-astra` / `ultra` |

## Findings and fixes

All three fixes are in [the canonical review workflow](../qa-correctness.md#review-fallback-and-acceptance):

1. **Reassess risk after findings or fixes.** A smaller review becomes advisory when the change becomes critical. Obtain eligible acceptance within the remaining original attempt budget or leave acceptance pending.
2. **Verify required effort as well as model identity.** Missing, unverifiable, or inadequate actual settings leave the corresponding acceptance requirement unmet. Explicit user requirements remain binding.
3. **Preserve the original review base.** Every stage reviews the complete owned change, including committed, uncommitted, and new files. A review after publication must not collapse to an empty comparison against the latest `HEAD` or `main`.

Stages 2 and 3 reviewed these fixes and changed no policy source. No finding was rejected or left unresolved. The final policy diff exactly matches the stage-1 and stage-2 saved diffs.

## Verification and limits

- `git diff --check` against both the implementation commit and original task base: passed.
- Added local policy links: 16 distinct references checked, no broken targets or anchors; all eight scoped Markdown documents have balanced code fences.
- Original Hard Rule 3 (proportionate QA), Hard Rule 9 (command-line-only model use), and Trigger Rule 43 (both strongest model families for benchmark reference data): byte-for-byte unchanged.
- Targeted source checks cover bounded attempts, model-only versus provider-wide failure evidence, partial edits, adverse verdicts, risk changes, explicit settings, reference-data requirements, advisory roles, and sequential expanded review.
- The prompt example's shell syntax and original-base substitution were checked. No automated model-routing system was implemented, and no runtime simulation of every quota or authentication failure was performed.
- Code-structure metrics: SKIP, because the scoped changes are policy documentation. The existing unrelated `claude-code-settings.json` edit in the shared checkout was preserved and excluded.

Final original-base-to-current policy diff SHA-256 (content fingerprint), across the eight scoped paths, excluding review reports:

```text
a330e4d505c7e13d3ef29f8ac4511bbe6f8bc4d68184b136316d8ae50b6fa170
```

The coordinator owns the final deterministic checks, commit and push, and one completion email to `brando.science@gmail.com` after verifying the published commit. Publication and email delivery are reported in the task's final message; this record does not claim an email was sent before that step occurred. Raw prompts, outputs, settings evidence, and saved diffs are retained locally at `/tmp/ac-review-fallback-mega-artifacts-20260910/`; that temporary directory is not a durable cross-machine record.

```text
VERDICT: FIXED
CRITICAL_ISSUES: 0
MAJOR_ISSUES: 0
FIXES_APPLIED: 3
STRUCTURAL: SKIP
SUMMARY: Three sequential strongest-model stages completed; all findings resolved and deterministically verified. Claude substitutions are explicit.
```

**TLDR-end:** The smaller-reviewer path remains available for ordinary changes, while critical, explicit-model, and benchmark-reference requirements remain binding. Three policy defects were fixed and checked by two later fresh Astra ultra stages; the review is complete with no unresolved findings.
