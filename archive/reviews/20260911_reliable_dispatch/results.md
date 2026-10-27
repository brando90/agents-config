# Reliable-dispatch policy review

**TLDR-start:** The policy requires proportionate execution, capacity reserved for finishing, verified remote handoffs and bounded recovery across eligible providers. Independent strongest-model review passed, its minor wording finding is fixed, and the policy is merged to main and synchronized locally and on the remote cluster.

**Status:** DONE — policy published and delivered
**Last updated:** 2026-09-11 12:38 PDT

| Phase | State | Evidence |
|---|---|---|
| Policy inventory and draft | DONE | Trigger Rule 48; workflows/reliable-agent-dispatch.md; synchronized entry points |
| Deterministic documentation checks | DONE | Added relative links resolve; code fences balanced; unique Rule 48; git diff --check passes; staged secret scan passes |
| Independent acceptance review | DONE | gpt-6-astra/ultra; PASS; 0 critical, 0 major, 1 minor wording finding fixed |
| Main publication and remote synchronization | DONE | Pull request https://github.com/brando90/agents-config/pull/55 verified MERGED at 8506eaa24df33aa990361cfcd1e6c3e692920232; local and remote policy hashes match |

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

## Verified publication and delivery

- Pull request https://github.com/brando90/agents-config/pull/55 is MERGED, verified through GitHub; merged commit 8506eaa24df33aa990361cfcd1e6c3e692920232. Verified source branch head bb81533c0ea6ba565f22d3450d3b83a01181dee4 matched the merge request; policy contents equal the merged revision.
- Local /Users/sanmikoyejo-mba-1/agents-config and remote /dfs/scratch0/brando9/agents-config safely fast-forwarded to that main revision. The unrelated local claude-code-settings.json bytes and remote deleted harbor_snap.sh / untracked health-check backup were preserved.
- Both workflow files have SHA256 8d9d20f2a179354882902bfeab148f8a9acb6fddae641ba1ee6997fe36ad755b. Final validation: 17 changed files scanned, 35 added relative links valid, diff whitespace/fences/unique rule checks pass, staged secret scan clear.
- Existing remote supervisor 01a08e0e-8d58-73a2-81bf-7468b328a8e9 received queued update 01a091f9-bf84-74e2-a377-b4dcb9bd61c4, including exact revision, workflow hash and adoption instructions. Queue acceptance is verified; in-memory acknowledgement and actual recovery deployment are not certified by this policy task.
- Research-job completion is a separate ongoing responsibility. This DONE status covers the requested agents-config policy update and delivery only.

**TLDR-end:** The reviewed rules are on main and their exact contents are available on the laptop and shared remote config checkout. Future dispatches must verify their own recovery mechanism; neither this document nor the queued supervisor update proves existing experiments finished.
