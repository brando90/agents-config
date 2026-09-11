# Reliable-dispatch policy review

**TLDR:** The proposed policy separates master reasoning from routine execution and requires capacity planning, synchronized recovery files, remote failure detection and bounded provider handoff. Publication is pending independent acceptance review.

**Status:** RUNNING
**Last updated:** 2026-09-11 12:22 PDT

| Phase | State | Evidence |
|---|---|---|
| Policy inventory and draft | DONE | Trigger Rule 48; workflows/reliable-agent-dispatch.md; synchronized entry points |
| Deterministic documentation checks | DONE | 30 new relative links resolve; code fences balanced; unique Rule 48; git diff --check passes |
| Independent acceptance review | PENDING | Critical shared rules: strongest reviewer required; normal single review round |
| Main publication and remote synchronization | PENDING | Shared local and remote config checkouts have unrelated changes; use isolated copies |

## Review scope and runtime

- Original base: a8b5fb1 (resolved full commit in Git). Ten policy/documentation files; no runtime configuration or launcher implementation change.
- Bounded read-only inventory used gpt-5.6-terra/high; it is not acceptance review.
- Primary acceptance attempt: Claude Fable 5.1/max, subscription credentials, private binary on skampere1. Recent same-tier failures make a quota denial likely; one fresh bounded review attempt will establish this task's outcome.
- If that attempt is unavailable: fresh Codex gpt-6-astra/ultra acceptance review, permitted by the preexisting critical-review fallback because this policy is not benchmark reference data and does not have an explicit required-family acceptance gate. Report missing company diversity. No smaller reviewer may accept this change.
- Latest account snapshot: Codex 26% weekly used, 74% remaining; shared with other jobs. No credit purchase or reset requested or used.
- Health: shared storage has 13,882 gibibytes free; node-local scratch is below its broad threshold, so the review checkout, logs and temporary files use shared storage. No graphics-processing-unit work.
- This is an actively supervised review, not an unattended job. Named terminal and exact process/log records are preserved; no claim of automatic failover for the older research jobs.

**TLDR-end:** Acceptance and main publication remain pending; the new policy is not proof that any existing launcher has automatic recovery.
