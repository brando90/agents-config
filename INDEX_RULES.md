# INDEX_RULES.md — Global Rules & Doc Routing

**Doc link:** <https://github.com/brando90/agents-config/blob/main/INDEX_RULES.md>

**TLDR:** Read this compact contract at task start, then read only the detailed rule sections whose triggers apply. All agents use the same policy; client-specific loading differs.

## How to load these rules

Refresh `~/agents-config` with `git -C ~/agents-config pull --ff-only` at each new non-trivial task and after an hour; preserve dirty/concurrent work and use the local copy if offline. Reread this index and relevant changed rules. When editing agents-config in an isolated checkout, use that checkout's index and detail files after refreshing the home checkout.

All Hard Rule **Details** links and matching Trigger Rule/Guideline links are mandatory routing: **before the action they govern, read that detail section and its applicable workflow**, including secret overrides, spending and review decisions. Do not read every topic file. Rule numbers are stable; paths below resolve beneath `~/agents-config/` (or the active agents-config checkout). If files are unavailable locally, fetch the same path under `https://raw.githubusercontent.com/brando90/agents-config/main/`. A Markdown link is a reading instruction, not proof the client loaded it. Never eagerly import this index or the detail collection into an entry file; read them as task files.

Hard rules govern conflicts with older wording in a triggered procedure. Explicit user instructions and platform/tool constraints retain their normal precedence. The existing task-specific SNAP pre-approval in Trigger Rule 51 is scoped to authorized work and existing budgets; it never permits authoring provider API calls. Detail pages retain the procedures, examples and exceptions; the catalog is optional lookup.

## Hard Rules (every response, never skip)

1. **Protect secrets.** Never commit credentials; inspect the exact staged diff and filenames before committing or pushing. Do not print secret values. Stop on a suspected leak and rotate exposed credentials; references/env vars replace embedded secrets. [Details](rules/safety-and-models.md#hard-rule-1)

2. **Verify before pushing.** Never fabricate unavailable source content; mark it unresolved. Inspect the diff and run the relevant deterministic checks. Report actual evidence and limitations, not an untested success claim. [Details](rules/maintenance.md#hard-rule-2)

3. **Quality assurance (QA) is opt-in.** Only a tier Brando explicitly requests or sets for this work in a runbook, `[qa]`/`[light-qa]`/`[mega-qa]` commit tag or environment flag starts a model reviewer. Hooks, project files and older “QA required” text are not opt-in. “Do QA”/“light QA” means one opposite-company round; apply findings and verify without automatic re-review. Mega QA follows Trigger Rule 10. Hooks cannot impose unsolicited QA; do not mention QA when unrequested. Benchmark-reference acceptance (43) remains separate. [Details](rules/safety-and-models.md#hard-rule-3)

4. **Response ending and titles.** Compact results: 1–2 sentences plus `.md`/`gdoc` links. End `**TLDR-end:** [proj: task]` with 1–2 sentences (`[proj]` without a task); never open `TLDR-start`. Emails/status reports also end `TLDR-end:` before any signature; include real decisions/deadlines only. Name and restate the core deliverable, not a micro-step (optional `›` suffix). Research updates open with a copy-ready status sentence; results also include a 1–2 sentence collaborator message in Brando’s voice. Match owned titles to verified summaries, identifier first. [Details](rules/responses.md#hard-rule-4)

5. **Snapshot.** In chat, immediately after the closing summary, show `**Snapshot:**` with the smallest real artifact sample (normally 5–15 lines, at most 25), or say why nothing tangible exists. [Details](rules/responses.md#hard-rule-5)

6. **Refresh configuration.** Follow the task-start/hourly refresh above, reread relevant changes, and preserve other owners’ work. Shared edits belong in both entry points. Review remains opt-in under Hard Rule 3. [Details](rules/maintenance.md#hard-rule-6)

7. **Keep clients current.** Use the installed package manager and the supported update hook; never assume npm. Do not install/use the deprecated Gemini CLI. [Details](rules/maintenance.md#hard-rule-7)

8. **Models, budgets and acceptance.** Masters: Codex `gpt-6-astra` / `ultra`; Claude `claude-fable-5-1` / `max`. Keep configured defaults; explicitly select proportionate execution workers (experiment selection: Guideline 19). Verify actual models/efforts and approved subscription billing. Never buy credits, enable new charges or weaken acceptance to recover. Required models/families and scientific pins remain binding. Before dispatch/review, read this detail and Rule 48. [Details](rules/safety-and-models.md#hard-rule-8)

9. **Command-line interface (CLI) only for language-model work.** Use approved authenticated `clauded`, `codex exec`, `antigravity`, or verified eligible clients. Never author direct provider application programming interface (API) calls or load provider keys as a fallback. Before executing an existing key-loading script, surface path, estimated spend and experiments and obtain the required explicit approval (the scoped existing SNAP exception is in Rule 51). Brando-authored calls still require the spend disclosure. Agent-authored direct calls block merge. [Details](rules/safety-and-models.md#hard-rule-9)

10. **Explain terminology.** Expand every acronym, metric symbol and project-specific term on first use in each response, including ordinary chat; use descriptive names instead of opaque internal labels. For Brando, a code may lead if a short gloss follows on first use. [Details](rules/responses.md#hard-rule-10)

11. **Numbers with verdicts.** Compact entries link full statistics (Rule 4). Give measured values, scales, denominators/splits, threshold sources and missing measurements. Statistical headlines need 95% intervals with resampling unit/limits and `x [lo, hi] p-val=Z` (named test/null or `p-val=n/a`). Report correlations individually; when interpreting score levels, also report absolute agreement and mean bias (judge minus human, positive = lenient), with both means. Give repeated-score variability/counts. Use existing data only; read the statistics workflow before reporting results. [Details](rules/responses.md#hard-rule-11)

## Trigger Rules (mandatory when triggered)

Read the linked rule **before** its action. Multiple rows may apply. Stanford Network Analysis Project (SNAP) is the remote cluster; a pull request (PR) is a proposed Git change. PDF means Portable Document Format.

| Rule | When → required action |
|---|---|
| [6](rules/maintenance.md#trigger-rule-6) | Edit agents-config → keep shared entries/routes consistent; reread, verify, commit and push the owned change. |
| [7](rules/maintenance.md#trigger-rule-7) | Create a PR → concise Summary and Test plan, relevant report/doc links; no unsolicited dashboard. |
| [8](rules/maintenance.md#trigger-rule-8) | Checks and requested review pass → commit/push; unresolved critical findings or failed review block landing. |
| [9](rules/research.md#trigger-rule-9) | Launch graphics-processor work → estimate resources, assign devices, respect allocation approval/SNAP pre-approval, verify and clean up. |
| [10](rules/safety-and-models.md#trigger-rule-10) | Explicit Mega QA → three sequential review stages; preserve required model/family gates. |
| [11](rules/maintenance.md#trigger-rule-11) | Requested QA passes and ultimate-utils reaches master → version, build and publish the package. |
| [12](rules/workers.md#trigger-rule-12) | New session/background work → inspect existing workers; clean only >24-hour processes confirmed idle. |
| [13](rules/writing.md#trigger-rule-13) | Research paper work or validity question → load research-writing guide; preserve evidence and source format. |
| [14](rules/services.md#trigger-rule-14) | Explicitly tracked completion/substantial review or authorized recovery event → verified, deduplicated notification; ordinary edits/light QA do not trigger email. |
| [15](rules/responses.md#trigger-rule-15) | Substantive question → answer in chat; email only when explicitly requested. |
| [16](rules/responses.md#trigger-rule-16) | Create/edit documents or save knowledge → headers; Google companion for findings; separate dated daily audience decks; verify. |
| [17](rules/maintenance.md#trigger-rule-17) | Authorized task → finish relevant end-to-end work, verification and authorized publication; no smoke-only stopping. |
| [18](rules/maintenance.md#trigger-rule-18) | Appendix/results-consistency/polish-only branch → inspect scope and land; substantive claims retain authorization requirements. |
| [19](rules/maintenance.md#trigger-rule-19) | Create/finish checkouts or merge branches → keep one canonical project and remove completed temporary copies. |
| [20](rules/research.md#trigger-rule-20) | Lean proof/type-check task → discover pinned toolchain and actually compile; report observed output. |
| [21](rules/writing.md#trigger-rule-21) | Paper introduction → load introduction and general research-writing guides. |
| [22](rules/writing.md#trigger-rule-22) | Paper abstract → load abstract and general guides; preserve structural source comments. |
| [23](rules/responses.md#trigger-rule-23) | Reader-facing prose → omit internal course/lab planning jargon. |
| [24](rules/responses.md#trigger-rule-24) | Reader outside a subfield → translate ambiguous jargon and explain concepts first. |
| [25](rules/writing.md#trigger-rule-25) | Personal blog → load personal-blog guides and reference posts; lab blogs use their separate route. |
| [26](rules/services.md#trigger-rule-26) | Authorized email → always BCC all four Brando inboxes, including sender and To addresses; follow signature. |
| [27](rules/responses.md#trigger-rule-27) | Substantive answer/explainer → lead with `**A (TLDR):**` and a direct answer; retain closing protocol. |
| [28](rules/research.md#trigger-rule-28) | Attached image/transcription → preserve original and provenance in the canonical project/experiment location. |
| [29](rules/writing.md#trigger-rule-29) | Exact “Q go” plus screenshots → numbered question packet, original images, issue, verification and publication; review still follows Hard Rule 3. |
| [30](rules/writing.md#trigger-rule-30) | Conference poster → load poster/research guides, compile and inspect rendering. |
| [31](rules/writing.md#trigger-rule-31) | Lab paper blog/roundup → load lab-blog guide; draft in paper repo and obtain coauthor sign-off before publication. |
| [32](rules/writing.md#trigger-rule-32) | Paper/release X thread → load thread guide; verify lengths, supported numbers and privacy gates. |
| [33](rules/writing.md#trigger-rule-33) | Paper/release LinkedIn post → load LinkedIn guide; preserve numbers, author/privacy policies and review delivery. |
| [34](rules/services.md#trigger-rule-34) | Browser/account/form task → finish mechanical work, verify account/files and sign in as authorized; preserve human-only and final-action boundaries. |
| [35](rules/writing.md#trigger-rule-35) | Semantic paper-source edit → compile and commit fresh PDFs beside active paper sources; verify build and references. |
| [36](rules/workers.md#trigger-rule-36) | Handoff/reusable/scheduled prompt → use the appropriate summary format; selection advice stays outside, execution facts inside; preserve schedule settings. |
| [37](rules/research.md#trigger-rule-37) | Long/dispatched run → maintain and publish live canonical results.md from launch; Markdown record + Google findings (Rule 16); dashboards opt-in. |
| [38](rules/hosts.md#trigger-rule-38) | SNAP connection or dispatch → check the official gateway (never flood it) before Cisco/Duo escalation; run health preflight, fix relevant failures, use owned checkout; token-spending checks remain opt-in. |
| [39](rules/research.md#trigger-rule-39) | Start/continue/finish experiment → canonical setup-named home/index, colocated artifacts, results tables in git, frozen evidence, lifecycle. |
| [40](rules/writing.md#trigger-rule-40) | Commit slide deck → fresh PDF, applicable text sibling and hash manifest in the same commit. |
| [41](rules/responses.md#trigger-rule-41) | End substantive replies with a ranked `[p N/10]` list; start 9-10 items without spending or rule violations. |
| [42](rules/workers.md#trigger-rule-42) | Dispatch beyond short lookup → owned checkout, named persistent session, verified launch/live records and completion watch; an agent in a numbered/stale session renames it to `<client>-<project>-<role>-<task>`. |
| [43](rules/safety-and-models.md#trigger-rule-43) | Benchmark reference edit → strongest-tier Claude AND Codex acceptance for every landed change; preserve attribution. |
| [44](rules/workers.md#trigger-rule-44) | Long run, account/context/turn limit, or end of any session in an experiment folder → durable timestamped `CKPT_<task>.md`; update only on events: edit the ≤30-line state block, append one dated log line, never rewrite; exact continuation and verified handoff. |
| [45](rules/workers.md#trigger-rule-45) | Ongoing coordinator → stable uniquely identified master checkpoint linking owned workers, watches and next commands. |
| [46](rules/hosts.md#trigger-rule-46) | Remote publishable phase → PR, exact-revision verification, requested review, immediate authorized merge, receipt and safe synchronization. |
| [47](rules/services.md#trigger-rule-47) | Question about another agent → read its task context; distinguish chat activity, schedule and actual execution/results. |
| [48](rules/workers.md#trigger-rule-48) | Dispatch or account/provider/context/turn limit → inventory authorized existing accounts; bound and verify handoff, preserving one writer and scientific limits. “ac-scheduler” → host watch, master check-in, authorized notifications. |
| [49](rules/research.md#trigger-rule-49) | Research root layout/tidy → four content buckets and root allowlist; inventory live consumers before moves. |
| [50](rules/research.md#trigger-rule-50) | Uncertain research/design → choose consequential uncertainty and cheapest valid test; record criterion before measuring. |
| [51](rules/hosts.md#trigger-rule-51) | Launch/resume/supervise any agent → verify effective full access/no routine approvals and first useful action; queued approval is not recovery; preserve task/platform/budget limits and exact SNAP pre-approval. |
| [52](rules/workers.md#trigger-rule-52) | Board-visible job → run-bound fresh receipts, ordinary-code liveness and verified board row; separate coordinator and execution state. |
| [53](rules/responses.md#trigger-rule-53) | Human-facing dates/new dated names → MM-DD-YYYY; preserve machine formats, existing names and frozen records. |
| [54](rules/responses.md#trigger-rule-54) | Mention experiment → full canonical folder name on first section mention, each table row and closing summary. |
| [55](rules/hosts.md#trigger-rule-55) | Run experiment/batch/long job → execute on SNAP with named full-access worker; verify execution through owner. |
| [56](rules/services.md#trigger-rule-56) | New day/planning/pasted task list → read weekly-notes source when available, compare latest section, disclose gaps; edit it only when Brando asks, additively. |
| [57](rules/workers.md#trigger-rule-57), [74](rules/workers.md#trigger-rule-74) | Would stall on scope, routing, approval or a click → decide (no-human route), record it; no self-made gates; to-dos only Brando's own. Grade next steps /10; do ≥9 now. |
| [58](rules/workers.md#trigger-rule-58) | Capacity/tool gap → checkpoint and continue through eligible existing accounts/agents; one failed route is not all accounts exhausted. |
| [59](rules/services.md#trigger-rule-59) | Mac freeze/Chrome zombie leak → load diagnosis playbook and repair the responsible parent, preserving tripwire. |
| [60](rules/writing.md#trigger-rule-60) | Technical explainer/teaching → use explainer style; paper prose uses its separate research style. |
| [61](rules/research.md#trigger-rule-61) | Solver/agent evaluation → freeze and finish full declared set within fixed budgets; retain every failed/missing cell and distinguish recovery. |
| [62](rules/services.md#trigger-rule-62) | Connector use, host setup, or unfamiliar/failing tool/service → read the connector cross-check and verified-host routes; investigate evidence, never fabricate missing content, recover and verify. |
| [63](rules/services.md#trigger-rule-63) | “Text me” → WhatsApp self-chat via quiet verified route; confirm sent state and surface human-only linking. |
| [64](rules/research.md#trigger-rule-64) | Explicit weekly update → newest-first project folder, complete post plus appendix/images; publish and return full post/path; keep sealed data sealed; sync knowledge under Rule 16; preserve his task-list text. |
| [65](rules/services.md#trigger-rule-65) | Open files for Brando in an editor → one call `cursor -n <project root> <files…>` (new window for that project); never `-r` or per-file open prompts. |
| [66](rules/services.md#trigger-rule-66) | Brando's AI meeting notes (Fathom link/ID, "get my notes") → verbatim transcript first, then summary and action items; script-written byte-exact copies with provenance in the named folder; never retype or reconstruct. |
| [67](rules/workers.md#trigger-rule-67) | Brief a worker, write a prompt or describe what an agent may do → default to allowed; state only binding limits, no precautionary bans or reassurance. |
| [68](rules/services.md#trigger-rule-68) | Create or copy a Google Doc/Sheet/Slides/Drive file → share "Anyone with the link" at creation: Viewer by default, Editor when readers fill it in; restricted only for secrets, sealed or private data. |
| [69](rules/workers.md#trigger-rule-69) | Dispatch or wait on a worker → watch for death too (`scripts/watch_worker.sh`: done, dead, credit/limit-blocked, idle, timeout); on failure recover at once on the next eligible account (Rule 58); never a success-file-only watch. |
| [70](rules/services.md#trigger-rule-70) | Launch or finish an experiment or long job (training/eval, cluster/background job, or >~15 min; never chat turns) → `[RUN START] <name>` then `[RUN DONE] <name>: <status>` email to brando.science, BCC all four inboxes. |
| [71](rules/services.md#trigger-rule-71) | Session start, or need email/calendar/people/a relay to Brando → read new `[FROM-UB9]` comments in agents-config issue #68 and act; ask there with `[TO-UB9]` plus a one-line email to brando.science. |
| [72](rules/services.md#trigger-rule-72) | Launch/resume a Vals-paid run → one large experiment at a time across projects (`valk` gate); queue, estimate cost; only Brando overrides. |
| [73](rules/workers.md#trigger-rule-73) | Desktop session pins → only active or awaiting-Brando ones, dated title; unpin when done. |

## Guidelines (best practices)

- [14](rules/maintenance.md#guideline-rule-14): Complete direct authorized requests; do not ask again for already-authorized actions.
- [15](rules/maintenance.md#guideline-rule-15): Read only task-relevant referenced docs.
- [16](rules/maintenance.md#guideline-rule-16): Keep index, README and paths accurate; mirror shared entry bodies; verify actual host instruction files and reload state.
- [17](rules/responses.md#guideline-rule-17): Use anchored paths in prose and commands.
- [18](rules/maintenance.md#guideline-rule-18): Use `ls -la` for configuration/credential directories.
- [19](rules/research.md#guideline-rule-19): Select experiment models/judges by capability, total cost and validation; preserve pins.
- [20](rules/responses.md#guideline-rule-20): Messages/drafts as Brando use his concise first-person voice; email includes required routing/signature.
- [21](rules/maintenance.md#guideline-rule-21): Check approved non-model credential storage before asking; exclude model-provider keys and keep values transient.
- [22](rules/maintenance.md#guideline-rule-22): Let the Node version manager control its path; avoid hardcoded versioned PATH entries.
- [23](rules/maintenance.md#guideline-rule-23): Authorized email: Brando's signed-in account (mail connector, else uutils SMTP); BCC all four inboxes, sender and To included; visible CC only if he asks; `drafted with <agent>` sign-off; “send” means send.
- [24](rules/maintenance.md#guideline-rule-24): Paper PDFs follow mandatory Rule 35.
- [25](rules/research.md#guideline-rule-25): VeriBench/VB private: >0.98 saturated; ≤0.9 good, ≤0.5 great, 0 best.
- [26](rules/research.md#guideline-rule-26): Any higher-is-better metric: best-model score ≥~0.98–0.99 means saturated, smooth or harsh (heuristic, not a hard rule).

## Authorized sign-in and verification codes

For an authorized account task, read [Rule 34](rules/services.md#trigger-rule-34): verify account, existing session or matching saved login and current challenge codes; keep credentials transient. Sign-in does not authorize unrelated transactions or messages.

## Machine Configs

Host routes: [catalog](CATALOG.md#machine-configs): [Mac](machine/mac.md), [SNAP](machine/snap.md), [Sherlock](machine/sherlock-agent-access.md), [other agent clients](machine/agent-clis.md). Do not load unrelated hosts.

## Workflows

Use matching trigger links first. The [workflow catalog](CATALOG.md#workflows) indexes detailed procedures; [instruction maintenance](docs/instruction-audit/README.md) records the size budgets and client compatibility.

## Writing

The [writing catalog](CATALOG.md#writing) routes paper, blog and announcement work. Colocate all artifacts for a project/event; do not split them into top-level directories by file type.

## Abbreviations

`ac` = agents-config; `cc` = Claude Code. [Launcher/profile aliases](rules/services.md#abbreviations) are labels, not proof of account access or independent budget.

## Collaborators / Contact roster

Before addressing/assigning a person, resolve identity through [contacts](contacts.md) and the [roster route](rules/services.md#collaborators--contact-roster).

## SNAP watcher reauth & reboot persistence (2026-04)

[Watcher reference](rules/hosts.md#snap-watcher-reauth--reboot-persistence-2026-04).

## ⚠ SNAP Slurm-gated access (audited 2026-09-03)

[Allocation and access reference](rules/hosts.md#-snap-slurm-gated-access-audited-2026-09-03).

## SNAP Required Symlinks (every node)

[Required paths and verification](rules/hosts.md#snap-required-symlinks-every-node).
