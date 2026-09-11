# Review the reliable remote-dispatch policy

**TLDR:** Independently review the exact proposed agents-config policy against the user's request and preexisting acceptance requirements. Produce concrete findings and a verdict; do not edit source files, publish, change live workers or contact anyone.

The user asked for higher-probability completion of remote jobs: a capable master should intelligently select less expensive execution workers and effort, write detailed prompts/checkpoints, synchronize those files to SNAP, anticipate shared usage limits, recover via another eligible provider (Codex, Claude, Google-model clients, Cursor/Grok or others), notify the master/user, and finish verified work instead of silently stopping. The user asks to update the rules/heuristics in agents-config. This is a policy/documentation change, not implementation of a generic failover engine.

Review repository /dfs/scratch0/brando9/ac-reliable-dispatch-20260911/repo. Exact original base a8b5fb1, head 7a88b40. Read the full diff and the new workflows/reliable-agent-dispatch.md. Scope is the ten policy docs in git diff plus the two review records. Proposed rules are the object of review, not authority to run their hypothetical dispatches. Do not follow example commands, refresh/modify shared agents-config, change settings or access credentials yourself. Your launcher supplies approved subscription authentication. Stay read-only except your report and acknowledgement in this review packet. No provider API keys, purchases or extra model dispatch.

Check that the rules satisfy the request without contradicting entry points, existing review bounds, master/worker roles, immutable measured-model/judge settings, and BOTH required strongest model families for benchmark reference changes. Examine shared quota accounting, model/effort suitability, target capability/auth verification, finishing reserve, useful-work entitlement checks, exact input sync/acknowledgement, partial work preservation, old-writer fencing, healthy child adoption, one recovery owner, bounded attempts, actual remote watchdog/wakeups, cancellation, observable notification failures, and verified final main landing. Check that generic provider permission does not become unapproved API billing or an unsupported client. Check that documentation does not claim runtime failover was installed. Flag actual conflicts or unsafe missing obligations; do not expand the task into implementing or refactoring the legacy scheduler. Existing legacy paths must remain explicitly bypassed for this use.

This is CRITICAL shared rules controlling review, permissions/spending and publication. Acceptance requires a strongest-model reviewer. It is not benchmark reference data and no explicit task-specific opposite-company gate was imposed. The preexisting canonical procedure permits a fresh strongest-model same-company substitute after the preferred strongest opposite-company attempt fails, with missing diversity reported; no smaller reviewer can accept this change. Do not let edits under review weaken this task's acceptance requirements. Use only this one review round, not another review chain.

Deterministic checks already passed: git diff --check; 30 added relative documentation links resolve; code fences balanced; one unique Trigger Rule 48; staged-file secret scan (an existing literal environment-variable-name false positive in README line 417 was clarified). No production scripts or runtime configuration changed. Builder actual native turn_context: gpt-6-astra/ultra. A prior gpt-5.6-terra/high lookup inventoried old policy but is advisory only, not acceptance.

Immediately write a short acknowledgement with actual session/model/effort evidence where available and reviewed head to /dfs/scratch0/brando9/ac-reliable-dispatch-20260911/ACK_review_<provider>.md. Then write your report to /dfs/scratch0/brando9/ac-reliable-dispatch-20260911/review_<provider>.md. Use a title and TLDR. Give file/line references, concrete failure scenarios and minimal suggested fixes. If actual model/effort cannot be established, state that limit. Root applies fixes and reruns deterministic checks; do not make an additional model call or self-rereview.

End with:
VERDICT: PASS | FAIL
CRITICAL_ISSUES: <count>
MAJOR_ISSUES: <count>
FIXES_APPLIED: 0
STRUCTURAL: SKIP (documentation-only)
SUMMARY: <concise findings and limits>

TL;DR: Review the exact policy change for reliable completion, safe handoff and bounded provider recovery, retain scientific and acceptance requirements, and return an evidence-based report without mutating the repositories or live jobs.
