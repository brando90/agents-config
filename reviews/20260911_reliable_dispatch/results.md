# Reliable-dispatch policy review

**TLDR-start:** The policy requires proportionate execution, capacity reserved for finishing, verified remote handoffs and bounded recovery across eligible providers. Independent strongest-model review passed; the minor wording finding is fixed, and publication is in progress.

**Status:** RUNNING — publication and remote synchronization
**Last updated:** 2026-09-11 12:34 PDT

| Phase | State | Evidence |
|---|---|---|
| Policy inventory and draft | DONE | Trigger Rule 48; workflows/reliable-agent-dispatch.md; synchronized entry points |
| Deterministic documentation checks | DONE | Added relative links resolve; code fences balanced; unique Rule 48; git diff --check passes; staged secret scan passes |
| Independent acceptance review | DONE | gpt-6-astra/ultra; PASS; 0 critical, 0 major, 1 minor wording finding fixed |
| Main publication and remote synchronization | IN PROGRESS | Pull request https://github.com/brando90/agents-config/pull/55; preserve unrelated shared-checkout changes |

## Acceptance evidence and reconciliation

- Original base: a8b5fb1e06aa4a63ebc5061857d12865a8b12f1d. Reviewed policy head: 7a88b4085792aa12e3f8d5bdabb3e0f64b558b42. Ten policy documents, no runtime configuration or launcher implementation change.
- Builder actual model/effort: gpt-6-astra/ultra, native turn metadata. A short gpt-5.6-terra/high inventory was advisory only.
- Preferred Claude Fable 5.1/max attempt failed on usage credits, exit 1, no model usage or review. Its structured result misleadingly had subtype `success`, but `is_error: true`. See [attempt receipt](claude_attempt.json).
- A fresh strongest Codex substitute is permitted by the preexisting critical-review fallback for this shared-policy change; no mandatory opposite-family gate applies. Opposite-company diversity is missing and disclosed. A smaller reviewer was not used for acceptance.
- Actual replacement reviewer: gpt-6-astra/ultra; session 01a091ef-bc61-7dd1-868e-e563bf902992; exit 0 with substantive report. See [independent report](review_codex.md) and [native identity acknowledgement](ACK_review_codex.md). All 12 remote source hashes matched the committed draft: [manifest](input_manifest.json). Both attempts used the same [review prompt](review_prompt.md).
- One minor finding: contradictory “ONLY preferred” wording in Trigger Rule 10. Fixed to “preferred Claude/Codex chain”; existing eligibility and mandatory family gates remain intact.
- Also clarified that the restriction on borrowed credentials does not prohibit existing authorized use of the user’s own subscription across their own machines. This is wording clarification, not new account or payment authorization.
- One review round; fixes checked deterministically. Final reconciled verdict: FIXED; CRITICAL_ISSUES: 0; MAJOR_ISSUES: 0.

## Runtime and limits

- Primary session: ac-reliable-dispatch-claude-review-20260911, created 12:25:35 Pacific daylight time; ended on allowance error. Replacement session: ac-reliable-dispatch-codex-review-20260911, created 12:26:40; ended after review. Review packet: /dfs/scratch0/brando9/ac-reliable-dispatch-20260911.
- The master actively supervised recovery. This was not an unattended failover demonstration. No automatic recovery engine was installed or certified for existing research jobs.
- Account snapshot at review planning: Codex 26% weekly used, 74% remaining, shared with other jobs. No reset or credit purchase used.
- Health: shared storage had 13,882 gibibytes free. The node-local scratch threshold failed, so the owned review checkout, logs and temporary files used healthy shared storage. No graphics-processing-unit work.
- New policy requires a tested remote recovery mechanism before future unattended dispatch. Existing scientific inputs and benchmark-reference acceptance requirements remain fixed.

**TLDR-end:** Independent strongest-model acceptance is complete with the wording fix applied. Verified main publication and delivery remain separate from review, and a policy document is not an installed recovery service.
