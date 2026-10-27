# Independent review of local catch-up and preservation policy

**TLDR:** The fixed change needs two substantive fixes: maintain exclusive access throughout a shared-checkout update, and give each scheduled run concrete execution bounds. The preservation and activation work remains explicitly pending; this review does not certify the archive, editor checkout, or live recovery mechanism.

Reviewed: 2026-09-11T22:18:17Z.
Provider/client: OpenAI / Codex command-line interface (CLI), version 0.154.0.
Role: independent acceptance reviewer for critical shared publication guidance; one read-only review round.
Repository: /dfs/scratch0/brando9/ac-local-sync-review-20260911/repo.
Original base: `892b3f9ed019c63be9c7efd970c04b0375bc4c5d`.
Reviewed head: `2151f7c119c3b859e31711123fc4d161986a78ef`.
Reviewed branch: `codex/remote-sync-watch-20260911`.

**Model and acceptance evidence.** Actual model `gpt-6-astra`, actual reasoning effort `ultra`. Native session `/lfs/skampere1/0/brando9/.codex/sessions/2026/09/11/rollout-2026-09-11T15-14-11-01a09289-1292-7f11-8d7a-ce86f8a5afdf.jsonl`, line 1, identifies provider `openai`, originator `codex_exec`, client version, session identifier and this review's working directory. Line 8 records `model: gpt-6-astra` and `effort: ultra`; its collaboration settings independently carry the same values. The session identifier also matches the native `thread.started` event in the review directory's `codex.jsonl`. These are session records, not a model inferred from the branch name or global defaults. They satisfy the original base's specified Codex model/effort floor; they do not provide separate server-side attestation.

The governing acceptance requirements were read from the original base: `INDEX_RULES.md:21–28` and `workflows/qa-correctness.md:13–39`. Shared publication rules are critical, and a smaller model cannot accept them. No mandatory second model family was specified for this policy-only change. The builder's actual model/effort and preceding fallback-attempt history were not independently established here; the master must retain that dispatch evidence. No other reviewer's conclusions were consulted, and no additional reviewers were launched. The proposed change was reviewed as source, not used to weaken its own acceptance requirements.

**Exact scope.** The complete base-to-head diff contains only these five files, with 52 added lines and no removals:

- `INDEX_RULES.md`: added local catch-up paragraph at line 142, reviewed with the existing landing and ownership rules.
- `workflows/remote-job-dispatch.md`: added editor catch-up section at lines 318–320, reviewed with dispatch context.
- `reviews/20260911_local_sync/CKPT_local_sync.md`: all 14 lines.
- `reviews/20260911_local_sync/results.md`: all 16 lines.
- `reviews/20260911_local_sync/schedule_prompt.md`: all 17 lines, including both summaries and the precise proposed merge command.

The exact prompt is bound to Git blob `f44a07347dc7e508ea416d2a0cf0aa52dee766f1` and Secure Hash Algorithm 256-bit (SHA-256) digest `c8ce6f86957bc506af60cf1a84a674fdd0a536176626ba60959d003896664ad0`. All five working files matched the reviewed head byte for byte.

Finding tags use `p` for predicted priority, scored out of 10.

**Finding 1 — MAJOR. [p 8/10] Preserve exclusive access from inspection through verification, because another writer can invalidate the new permission to update shared main.**

Location: `reviews/20260911_local_sync/schedule_prompt.md:9`; corresponding permission in `INDEX_RULES.md:142` and `workflows/remote-job-dispatch.md:320`.

The prompt inspects processes, checks dirty/staged/unpublished work and untracked/ignored collisions, then immediately rechecks before `git merge --ff-only origin/main`. Those are observations, not an exclusion mechanism held during the update. Another session can start writing after the last check. In particular, an ignored file created in that interval can be overwritten: the installed Git help explicitly identifies updating ignored files as the merge default. A background fetch can also advance the shared `origin/main` reference after the incoming-path check, causing the command to merge a different revision whose paths were never checked. Verifying afterward can detect a mismatch but cannot undo lost local-only bytes. The remote landing lock mentioned at prompt line 13 protects a different operation; it does not establish exclusive access to the editor checkout.

Minimal fix: require a brief exclusive update window, established with the checkout's known writers and maintained through preflight, merge and post-check; a lock counts only if those writers honor it. If this cannot be established, keep the existing isolated-checkout fallback. Resolve the fetched main revision once to an immutable commit identifier, use that same identifier for ancestry/collision checks, merge and final comparison, and make the command `git merge --ff-only --no-autostash --no-overwrite-ignore <checked-commit>`. These options reinforce the stated prohibitions; they do not replace the writer exclusion. Apply the same ownership discipline when reusing the coordinator's existing isolated checkout.

Deterministic verification for the master: exercise a writer appearing after preflight, an ignored incoming-path collision, and a fetch advancing `origin/main` between inspection and merge. The shared update must be refused or remain protected, and only the inspected commit may be installed. Existing tracked/staged changes, unpublished commits and parent/child path collisions must still leave the editor checkout untouched.

**Finding 2 — MAJOR. [p 7/10] Bound the entire scheduled run, because a stalled remote check can prevent periodic catch-up.**

Location: `reviews/20260911_local_sync/schedule_prompt.md:5–9,13–15`.

Only the fetch paragraph says to use “bounded operations.” The preceding remote process/checkpoint inspections, any owner coordination, lock acquisition and meaningful checkpoint publication have no per-operation timeout, retry limit or total run deadline. The eventual stop condition concerns completed research, not the duration of one poll. A stalled remote command can therefore consume a run before it reaches local catch-up; repeated transient-error handling or waiting for an owner can likewise turn a poll into an ongoing recovery session. There is also no stated non-overlap guard for executions using the same receipt and isolated checkout. One configured schedule does not, by itself, document that invocation overlap is prevented.

Minimal fix: specify one finite pass per trigger, a total deadline shorter than the normal 30-minute interval, bounded remote/network/lock operations and a finite retry budget. Record unknown/stale remote evidence and a deduplicated error on failure; continue independent safe local checks where possible, then leave further recovery to the named owner and next scheduled run. Before mutating receipts or checkouts, verify scheduler-provided non-overlap or acquire one coordinator-run guard; skip a concurrent invocation without taking over its lock. Give the chosen concrete limits in the prompt or an exact referenced execution contract. For example, a 10-minute total budget, 60-second external-operation limits and at most one retry per failed read would be a reviewable bounded policy, subject to the master's operational choice.

Deterministic verification for the master: a nonresponsive remote read must return within the declared bound, preserve an explicit unknown state and cause no job restart; a second trigger while the first is active must not become a second writer. A timeout must not mark unfinished jobs complete or pause their recovery owner.

**Minor consistency finding. [p 3/10] Use the scheduled-prompt summary format already required at the original base.**

Location: `reviews/20260911_local_sync/schedule_prompt.md:3,17`. Original-base `INDEX_RULES.md:88` requires tagged `**TLDR-start:**` and `**TLDR-end:**` summaries for saved schedules, with the closing summary naming the update destination. The proposed file instead uses `**TLDR:**` and `TL;DR:` and omits the destination from its closing summary. Rename those two labels, add the project/task tags, and specify updates to this master conversation. Preserve the body, notification behavior and stopping condition. This is a minor formatting correction, not an additional major issue.

**Preservation and state-reporting assessment.** The prompt correctly prohibits automatic duplicate-folder deletion or movement, preserves scientific model/effort requirements, separates an open pull request from a verified landing, and distinguishes an updated isolated checkout from a stale editor checkout. Its explicit prohibition on restarting completed proof jobs and changing the experiment is appropriate. The shared-checkout prohibitions on stash, reset, clean, rebase and branch switching are clear. A blocked unfinished job does not meet its stop condition, and cancellation is expressly supported. The general paragraph and workflow summary should retain that same canceled-job interpretation. No changed source claims that a local schedule implements remote recovery.

`results.md:11–14` records the audit as done but preservation/initial synchronization as in progress and activation as pending. The supplied counts are arithmetically consistent: 22,935 + 1,191 = 24,126. Their content-level truth, absence of dependencies/open handles, full external backup and archive integrity were not independently checked: the relevant VeriBench data and live state are outside this source review. No reference-data acceptance is granted to the 1,191 extra versions. Keeping those bytes as explicitly inactive archival material is consistent with the supplied scope; promoting any of them into accepted benchmark inputs would require the original reference-data gates.

Before the initial guarded fast-forward or legacy-folder relocation, the master still must verify the archive and manifest, preserve and verify the full external local backup, and record their concrete paths, integrity evidence and original-path mapping. Bind the deduplication evidence to VeriBench main `be62b6bc4959eb2f233399340944f6582b30e261`, label the 1,191 versions as inactive archival bytes, and verify the single canonical active experiment-71 path afterward. Preserve the unrelated untracked experiment-83 material as well. These are outstanding operational prerequisites already identified as pending, not claims that this review tested or that bytes have been lost.

Likewise, source approval cannot establish that exactly one active schedule exists. Before activation, the master must inspect and reconcile the actual schedule records, preserve unrelated manually paused schedules, record the chosen identifier/owner/cadence/targets, and verify the initial run. Verify an actual remote recovery mechanism separately; configuration, a terminal, or a heartbeat alone is insufficient evidence. No live experiment, schedule, process or remote recovery state was inspected or changed by this review.

**Verification and limits.** Base ancestry passed. The scoped `git diff --check` passed. The added Markdown link resolves. All scoped files match the fixed head, and the source checkout was clean. Native model/effort evidence was checked. `git merge -h` was used only to inspect options; its help exit code was 129, and it performed no merge. No dynamic Git scenarios were executed because this assignment permits writes only to the report and acknowledgment. Structural code analysis is skipped for this Markdown-only change; prose consistency was reviewed. No source fixes were applied. The explicit read-only instruction superseded the usual configuration pull/settings/publication instructions, so no fetch, pull, commit, push, settings change, live-worker command or contact was performed.

The master can reconcile these findings and verify minimal fixes within this one round; this report does not request another review round.

VERDICT: FAIL
CRITICAL_ISSUES: 0
MAJOR_ISSUES: 2
FIXES_APPLIED: 0
STRUCTURAL: SKIP
SUMMARY: Shared-checkout updates need maintained writer exclusion and an immutable checked merge target; scheduled runs need concrete time/retry bounds and non-overlap. Preservation, first synchronization and actual schedule/recovery verification remain pending operational gates.
