# Claude review and deterministic reconciliation

**Doc link:** <https://github.com/brando90/agents-config/blob/main/docs/instruction-audit/review.md>

**TLDR:** One requested Opus 5.5 review found three major summary regressions; the builder fixed them and reconciled the minor findings with deterministic checks, without another review round. The original verdict is retained below.

## Review identity and scope

- Reviewed commit: `2a99acfb2ed3bf7e57a8209e3886745fd28508a9`, base `2b5334965c23e6a0396d2c47078d68b1b127bc22`.
- Builder: Codex desktop; configured local command-line default `gpt-6-astra` / `ultra`, but the builder's backend identity is not independently exposed by this task.
- Required models: the user expressly allowed Claude Fable 5.1 max **or** Opus 5.5 max. Primary Fable attempt returned an out-of-credits error before any review tool use. Recovery used the explicitly permitted Opus alternative on the same cached subscription; no provider keys, purchases, account switching or billing changes.
- Actual reviewer: initialization and assistant messages report `claude-opus-5-5`; launcher explicitly set `--effort max`. The reviewer could not inspect its own effort; the builder subsequently verified the saved client transcript records `effort=max` and `perTurnEffort=max`. Runtime usage also reports an internal Haiku helper; it was not the acceptance reviewer or a separate review round.
- Role: acceptance review of critical shared instructions. Original result: FAIL, zero critical and three major findings. The user-authorized light-review process is one round, builder fixes, then deterministic verification; the original FAIL is not rewritten as a second reviewer PASS.
- Private raw transcripts/authentication receipts remain outside the public repository. This is the public findings and reconciliation record, not an account-access receipt.

## Reconciliation

| Finding | Resolution and evidence |
|---|---|
| 1: provider-key script approval summary | Fixed in both identical entry bodies: disclose path, spend and experiments, pause and wait for explicit confirmation; narrowly retain the original scoped SNAP exception. |
| 2: review opt-in ambiguity and detail loading | Fixed in both entries and index: current-work tier opt-in only; hooks, project files and old required-review wording are excluded; Hard Rule Details are explicitly mandatory before their governed actions. |
| 3: missing source-integrity rule | Restored explicit never-fabricate wording to both entries and index; the complete old Claude paragraph is migrated to broad-investigation.md and checked by the receipt. |
| 4: stale anticipated reviewer | Replaced pending Fable text with actual Opus identity, failed first attempt and the verified launch and saved per-turn effort metadata. |
| 5: connector cross-check route | Rule 62 now explicitly triggers on connector use/host setup; its linked broad-investigation workflow retains the complete old connector paragraph and mandatory workflow link. |
| 6: guard gaps | Added wrong-number/wrong-anchor detection and missing-index handling with regression cases; migration checks designated rule sections and two entry-only paragraphs. Lowered index budget to 22,528 bytes and explicitly forbade eager index imports. |
| 7: old SNAP verification heading | Replaced removed-heading expectations with the actual compact headings and instruction checker. |
| 8: overly narrow autonomy summary | Broadened summary to scope, routing, reversible design choices and approval-menu escalations, preserving real authorization boundaries. |
| 9: stale rule/cross references | Conditionalized remote email's review verdict, corrected weekly-update rule IDs, and linked the relocated required-symlinks section explicitly. All precise body changes are in the manifest. |
| 10: native Claude user-file setup | README creates a regular pointer only when missing; host setup and guide verify the native user file separately from the ancestor compatibility link. Three isolated fixtures confirm creation and preservation of an existing regular file and dangling link. No live profile deployment performed. |
| 11: citation/disclosure nits | Cited official Codex Remote; clarified the launcher-specific process check; identified Grok trust as a local observation; disclosed the removed PR one-line phrasing. |
| Pre-existing secret-printing examples | Changed relocated environment diagnostics and the touched SNAP guide to report set/unset or exit status, never values. |

Post-fix status: all findings above resolved in source and verified deterministically; no unresolved publication gate. Limits: no claim of new-session instruction-following accuracy, remote-host deployment, universal client deduplication or unexposed service internals. The preserved source and explicit routing are the verification target.

## Original reviewer output

The following is the review of the pre-fix commit, retained verbatim as evidence:

**Verdict: FAIL as committed.** There are 0 critical and 3 major issues, and the builder can fix all of them in this round. I reviewed exactly commit `2a99acf` against `2b53349` in the agents-config (ac) repository, read-only.

No new authorization was introduced, and nothing in the patch can be read as loosening permissions in a dangerous way. All 81 rule bodies survive word for word, apart from 7 disclosed wording changes ("clarifications"). Each of those is either safety-neutral or a tightening. The failures are all in the auto-loaded layer: one policy was dropped without a record, and two summaries of critical rules (spending and review) are looser than the old entry points.

## Findings, ranked by predicted priority (`[p N/10]`, per Trigger Rule 41)

1. **[p 8/10] Major: the spend control for scripts that load provider keys is vaguer in the auto-loaded entry point.**
   - **Where:** `CLAUDE.md:25` / `AGENTS.md:25` now say "require path/spend disclosure and the governing approval". The parent version (`CLAUDE.md:65`, plus a dedicated section in `AGENTS.md`) said "pause … surface path + estimated spend, then wait for explicit confirmation".
   - **Counterexample:** off the Stanford Network Analysis Project (SNAP) cluster, Brando says "run `score.py`", which loads `~/keys/anthropic_*`. The entry point only requires reading the index for "non-trivial" tasks, so an agent working from the entry alone can disclose the cost and treat the request itself as "the governing approval". That skips the wait, which is the $17,752.98 failure mode.
   - `INDEX_RULES.md:33` is still explicit, so only the summary regressed.
   - **Fix:** "…then wait for Brando's explicit confirmation; only SNAP work under Trigger Rule 51 replaces the wait (record the estimate in the checkpoint) within existing budgets."

2. **[p 7/10] Major: the quality assurance (QA) opt-in summary lost its exclusions.**
   - **Where:** `INDEX_RULES.md:21` says "his saved opt-in" and `CLAUDE.md:26` says "explicit opt-in". The rule that hooks, project files and older rule text calling QA "required" do not count now survives only in `rules/safety-and-models.md:13`.
   - **Why the detail may go unread:** `INDEX_RULES.md:11` makes only "numbered links" mandatory, and Hard Rules use `[Details]` links.
   - **Counterexample:** an old project `CLAUDE.md` says "run light QA before pushing to main". It reads as a saved opt-in, so a reviewer runs on every push.
   - The same gap lets `INDEX_RULES.md:13` ("explicit user instructions retain their normal precedence") skip Hard Rule 1's step of pushing back and confirming twice when someone says "just commit it".
   - **Fix:** define opt-in as "a tier he requests, or names for this work in a runbook, `[qa]`/`[light-qa]`/`[mega-qa]` commit tag or environment flag; hooks, project files and older rule text do not count". Also make Hard Rule details mandatory reading before the action they govern.

3. **[p 7/10] Major: the anti-fabrication rule was dropped without a record.**
   - **What:** parent `CLAUDE.md:14` said "When external fetches fail … **never fabricate the missing content**" (rule from #52 on 05-26-2026, current wording from 09-24-2026). It appears nowhere in the new tree, in the migration manifest, or in the audit.
   - `workflows/broad-investigation.md` covers retries and reporting blockers, but not fabrication.
   - **Counterexample:** a transcript fetch fails, and the agent writes "takeaways" from its prior knowledge without breaking any rule it was routed to.
   - **Fix:** add "never fabricate content you could not retrieve; mark it unresolved" to the Evidence bullet (`CLAUDE.md:30` / `AGENTS.md:30`). Restore the full sentences at `workflows/broad-investigation.md:45` and log the migration.

4. **[p 6/10] Minor: the audit records the wrong reviewer in advance.** `docs/instruction-audit/README.md:95` says "`claude-fable-5-1` / `max`". The actual reviewer is `claude-opus-5-5`, with effort unverified (see metadata below).

5. **[p 5/10] Minor: the connector cross-check workflow (`workflows/codex-connector-tandem.md`) lost its mandatory route.**
   - The parent linked it from the index, both entry points and the README. Now only `CATALOG.md:31` links it, and the catalog is optional lookup.
   - That buries a privacy rule: "transfer only authorized source data … keep private receipts out of this public repo".
   - **Fix:** link it from Trigger Rule 62 (`INDEX_RULES.md:101`) or from `workflows/broad-investigation.md:33`.

6. **[p 5/10] Minor: the guard checks miss misroutes and entry-point content.**
   - `scripts/check_instruction_docs.py:79` only checks that each rule's anchor is linked somewhere. My probe swapped the `[46]` and `[51]` link targets in a scratch copy and still got `PASS: 0 errors`.
   - `verify_migration.py:24` covers only the index rule blocks, matched as a substring anywhere in the destination file. That is how findings 3 and 5 got through.
   - The index size budget (24,576 bytes, `:14`) is above Antigravity's documented 24,000-byte per-file truncation limit. If a host imported both files, entry plus index would have only 566 bytes of headroom.
   - **Fix:** assert that each link's number matches its anchor, add a one-time receipt for the old entry-point paragraphs, and lower the cap or document "never import the index".

7. **[p 4/10] Minor: stale SNAP setup check.** `machine/snap-init.md:54,88` expect a "Mandatory Response Protocol" section in both entry points. It no longer exists, so a correctly refreshed node reports a false failure, and an agent may "repair" it by re-growing the entry points.

8. **[p 4/10] Minor: Rule 57 now triggers too narrowly.** `INDEX_RULES.md:96` and `CLAUDE.md:27` say "routine reversible choice". The parent covered any gating question, approval menu or escalation. A non-routine but reversible design choice would now get escalated to Brando.

9. **[p 3/10] Minor: stale references inside the word-for-word rule bodies.**
   - `rules/hosts.md:13`: the landing email body still lists "QA verdict" unconditionally, a leftover conflict with Hard Rule 3.
   - `rules/research.md:57`: "Hard Rule 1" and "(Hard Rule 4)" only made sense under the removed entry-point numbering; they should be Hard Rule 4 and Trigger Rule 8.
   - `CATALOG.md:47`: "see SNAP Required Symlinks above" points at a section that now lives in `rules/hosts.md`.

10. **[p 3/10] Minor: the setup pointers for the Claude user file now disagree.**
    - `README.md:38-45` creates `~/.claude/CLAUDE.md`, which is correct per Claude's docs.
    - `rules/hosts.md:61`, `machine/snap_setup.sh:48` and the SNAP setup guide still create only `~/CLAUDE.md`. That file loads only for sessions started under the home directory, so SNAP sessions working under `/dfs` never see it. This gap predates the patch, but the docs now contradict each other.
    - Claude Code's desktop Cowork mode also skips a symlinked `~/.claude/CLAUDE.md`.
    - The four script edits themselves are safe: `write_if_needed` keeps existing files unless `--force` is passed.

11. **[p 2/10] Nits: citations and disclosure.**
    - `docs/setup-reference.md:228` retires the claim that Codex has no Remote Control without citing a source. The retirement is correct (official docs list "Codex Remote" at learn.chatgpt.com/docs/remote.md), but `rules/workers.md:23` still says Codex has none.
    - The Grok "trusted-project" remark at `docs/instruction-audit/README.md:62` isn't on the cited Grok page.
    - The audit's description of the Trigger Rule 7 change omits that "(one line each)" was also removed.

Pre-existing, not introduced by this patch: `docs/setup-reference.md:261-262` echoes the values of `CLAUDE_CODE_OAUTH_TOKEN` and `ANTHROPIC_API_KEY`, which conflicts with Hard Rule 1's "do not print secret values".

## Representative routes

| Route | Constraints and path | Reachable |
|---|---|---|
| Ordinary edit | Hard Rules 2 and 3; Trigger Rules 17 and 8 (plus 6 for agents-config edits): deterministic checks only, no reviewer, QA not mentioned | ✓ |
| Explicit light QA | Hard Rule 3: one opposite-company round, builder fixes and verifies, no re-review. Hard Rule 8 detail plus the fallback procedure in `qa-correctness.md`. Critical changes need strongest-model acceptance (`rules/safety-and-models.md:21`) | ✓ |
| Benchmark reference edit | Stated in the entry point, plus row 43 to its word-for-word detail: both model families at the strongest tier | ✓ |
| Key-loading script | Off SNAP: Hard Rule 9 (pause, disclose, wait). On SNAP: Trigger Rule 51 replaces the wait for budgeted, authorized work; never covers writing provider calls (`INDEX_RULES.md:13`) | ✓ (finding 1) |
| Full-set evaluation | Row 61 to its detail to the anchors in `expts-and-results.md`, plus Trigger Rules 55, 48, 42, 44 and 37 | ✓ |
| Browser final submission | Row 34 and the sign-in section: the human keeps the final Submit/pay/send click | ✓ (finding 5) |
| Weekly update | Row 64 word-for-word, Guideline 20 (Brando's voice), and never editing his Google Docs | ✓ (finding 9) |

## What I checked
- **All requested checks pass:**
  - `check_instruction_docs.py`: 0 errors, 81 rules routed, 252 links.
  - `test_instruction_docs.py`: 7/7.
  - `verify_migration.py`: 81/81 rule bodies plus the 7 changes.
  - `bash -n`: exit 0 on all 4 scripts.
  - `git diff --check`: clean.
- **My own block-by-block diff, done before reading the audit:** 0 rules missing. Exactly 5 rule blocks changed, which are the 7 recorded edits. 0 lines lost from the relocated abbreviations, contact roster, SNAP sections and catalogs.
- **Index links:** all 59 trigger, 11 hard-rule and 11 guideline links point at the matching rule number. No inbound links from other files into the rewritten files are broken.
- **Audit numbers reproduce exactly:** byte reductions of 81.08%, 82.08% and 90.13%; entry plus index went from 216,339 to 23,434 bytes; 223/223 tracked files inventoried.
- **Client claims against official docs (10-04-2026):** Claude, Codex, the Cursor command-line interface (CLI), Antigravity and Grok all match, except the two remarks in finding 11.

## Limitations and metadata
- Read-only: nothing was edited, installed, dispatched or published, and the worktree is unchanged. I didn't launch fresh client sessions to observe what actually loads. The unchanged workflow guides got only targeted searches, and the route analysis is reasoning, not simulation.
- **Reviewer:** `claude-opus-5-5` (Opus 5.5), per the runtime identity. Effort can't be observed from inside the session, so record it as unverified.
- **Role and classification:** this is the requested review of a critical change. Hard Rule 8 names `claude-fable-5-1` as Claude's strongest tier; your brief explicitly allowed Opus 5.5 max, so record that with the review. I didn't observe the builder's model.

```
VERDICT: FAIL
CRITICAL_ISSUES: 0
MAJOR_ISSUES: 3
FIXES_APPLIED: 0
STRUCTURAL: SKIP
SUMMARY: All 81 rule bodies are preserved and every sampled route is reachable, but the auto-loaded layer drops the anti-fabrication rule and loosens the key-script and QA opt-in summaries; fix those 3 (plus minors) and re-run the deterministic checks.
```

**TLDR-end:** [ac: compaction-review] FAIL as committed (0 critical, 3 major): every rule body and all 7 disclosed changes check out and every sampled route is reachable, but the auto-loaded entry drops the anti-fabrication rule and loosens the key-script and QA opt-in wording. Fixing those three plus the minor items and re-running the deterministic checks should make it landable without another review round.

**Snapshot:**
```
check_instruction_docs.py   → PASS: 0 errors (81 rules routed, 252 links)
verify_migration.py         → PASS: 81 of 81 … 7 recorded wording clarifications
own block diff              → missing=0; changed=[G21, HR6, TR7, TR29, TR46] (= the 7 edits)
probe: swap [46]/[51] links → checker still "PASS: 0 errors"
parent CLAUDE.md:14 "never fabricate the missing content" → 0 matches at 2a99acf
CLAUDE.md:25      "…require path/spend disclosure and the governing approval…"
INDEX_RULES.md:21 "…explicit tier request or his saved opt-in starts a model reviewer"
machine/snap-init.md:54 "…should show the Mandatory Response Protocol"
git status --short → 0 changes (read-only review)
```
