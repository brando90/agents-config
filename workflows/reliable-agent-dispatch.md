# Reliable agent dispatch and quota recovery

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/reliable-agent-dispatch.md>

**TLDR:** Account, provider, context and turn limits require a durable checkpoint and verified continuation through an eligible existing account or agent. Inventory and bound that recovery without abandoning usable accounts, duplicating healthy work, resetting scientific budgets or weakening acceptance.

This is the operational procedure for `~/agents-config/INDEX_RULES.md` Trigger Rule 48, requested by Brando on September 11, 2026. It applies to every provider and to long local jobs as well as Stanford Network Analysis Project (SNAP) jobs. It improves the chance of completion; finite subscriptions and unavailable required reviewers cannot be made unlimited by a prompt.

**All-host full access (09-26-2026).** Every coordinator, worker and reviewer runs with the client's supported full access and routine approvals disabled on every host. Verify actual arguments/settings, not just wrapper names; put this requirement in every dispatch brief. Use `codex exec --dangerously-bypass-approvals-and-sandbox` or verified `clauded` wrappers; verify documented equivalents for other clients. Recover owned workers stalled on routine approvals with a checkpoint and one writer, then verify their next action. Platform restrictions, explicit user limits, spending caps and secret safety still apply. SNAP briefs additionally carry the Trigger Rule 51 pre-approval line verbatim.

**Measured solver/agent evaluations follow [Trigger Rule 61's full-set contract](expts-and-results.md#uninterrupted-evaluation-of-the-full-declared-set).** Budget and track every declared model × task × seed/repetition cell, include the completion reminder in every initial/continuation prompt, and let the fixed bounded procedure run under durable ownership. Coordinator failover must not terminate healthy measured work or alter its model, prompts, settings, budgets or continuation policy. The generic recovery below concerns eligible execution roles; it does not authorize an extra measured attempt. Keep incomplete/interrupted cells visible in the original denominator and freeze unplanned measured recovery as a separate prospective condition.

## 1. Name the master and divide the work

The **master** owns the objective, decomposition, model selection, recovery and final verification. `master agent:` is an optional user designation; accept it immediately and record it in the master checkpoint. Infer the role when already coordinating workers under Rule 45; do not ask merely to obtain that label. There is one recovery owner per job, even when several masters coordinate a project. Transfer that ownership explicitly.

Keep the strongest configured model for the master and reasoning-critical decisions: currently Codex `gpt-6-astra` with `ultra`, or Claude `claude-fable-5-1` with `max`. A master that itself must fail over records its replacement and capabilities; it does not silently abandon its jobs. Do not change global model defaults to select a worker.

| Phase | Selection heuristic |
|---|---|
| Proven command, polling, transfer, compilation, deterministic scoring | Run the command directly where possible; do not spend a model turn per item or poll. |
| Bounded implementation or research execution with clear inputs, examples and tests | Start with a capable regular reasoning worker, for example `gpt-5.6-terra` at `medium` or `high`, or `claude-sonnet-5` at a supported suitable effort. Verify target support before using these examples. |
| Tiny mechanical transformation with a decisive check | A smaller supported model at low effort can suffice; use the check as the acceptance criterion. |
| Ambiguous design, difficult proof, subtle diagnosis, critical decisions | Use the strongest suitable model, or send only this narrow decision back to the master. |
| Acceptance review | Apply the existing [review policy](qa-correctness.md#review-fallback-and-acceptance); critical acceptance retains its capability floor, and benchmark reference changes retain both required strongest families. |
| Model being measured, benchmark judge, or another scientific input | Preserve the specified model, effort and protocol. Executor failover does not authorize changing the experiment. |

Choose model and effort separately, with a short rationale for each. More detailed instructions can reduce ambiguity; they do not turn a weaker worker into an expert reviewer. Increase capability after a concrete failed check or newly discovered reasoning need, rather than repeatedly trying an inadequate model. Do not assign every worker `ultra` merely because its master is `ultra`.

The human-facing recommendation belongs outside the worker prompt (Rule 36). The dispatch manifest records the **actual chosen** provider, client, model, effort and command; these are execution facts, not hidden recommendations. Use a brief central instruction file with linked, verified supporting files instead of copying the full project transcript into every call.

## 2. Budget for finishing, including review and publication

Before launch, inspect the authenticated account's current usage information where exposed: timestamp, provider/account profile, applicable shared windows, remaining allowance, reset time, and evidence source. Missing data means **unknown**, not unlimited. Never print credentials. Local and remote agents using the same subscription may consume the same allowance; another machine, client, or login profile is not necessarily an independent budget. In particular, a model accessed through Cursor may still share the allowance or billing route of another candidate.

**Existing-account authorization (10-09-2026).** Brando authorizes continued work through all his existing eligible OpenAI work/Vals, personal and Stanford/school accounts, analogous Claude accounts, and supported Cursor, Grok, Antigravity or other installed clients on his Macs and SNAP. Do not ask again merely to select one of these accounts or restore its ordinary supported sign-in. Authorization is not evidence that an account exists, has independent allowance, meets the role's capability or funding rules, or can run on a particular host. Verify those facts below; this never authorizes new accounts, borrowed credentials, provider-key fallback, purchases or new charges.

**Existing credit authorization (September 13).** Brando permits his existing Codex and Cursor credits and approved Google/Antigravity plan to fund authorized tasks. Record the exact account and billing route, remaining included allowance separately from applicable prepaid credit, any spend-control/admin limit, and the task's bounded allocation and finishing reserve. A credit balance's units are not necessarily dollars. Exhausted included allowance does not by itself block use of an authorized existing balance; a positive balance does not prove the requested model or another provider can use it. Before consuming credits, verify that the route cannot create a new unapproved charge, including an already-enabled automatic recharge, on-demand usage or postpaid spillover. A positive balance alone is insufficient: account for recharge thresholds, concurrent consumers and the bounded next unit. If this protection cannot be verified, keep that route ineligible and use another verified route or surface the specific missing billing evidence; do not alter billing/admin settings automatically. Missing billing evidence stays unknown. Never purchase more credits, enable auto-top-ups or uncapped pay-as-you-go overages, raise limits, change plans, or use provider API keys under this standing authorization. A CLI's optional direct-provider-key mode is still prohibited by Hard Rule 9. Prefer a first useful bounded unit to a separate paid probe.

Estimate the next bounded phase from a small representative run or recent comparable work. Include prompt/context size, number of model calls, concurrency, expected retries, review, repair and publication. Record an interval or unknown estimate, not an invented completion percentage. Reserve room for the master, required reviewers and final integration. A read-only usage check is preferable to repeated token-spending probes; the first useful bounded unit can verify runtime entitlement.

**Default planning triggers, not provider guarantees:**

- At or below **25% remaining** in any relevant limiting window, or when the conservative next-phase estimate plus finishing reserve exceeds the remaining budget, checkpoint and reconsider model, effort, batch size and shared concurrency before admitting more work.
- At or below **10% remaining**, do not admit another expensive model batch on that allowance. Use an eligible preselected alternative, finish a small already-admitted unit if feasible, or wait with remote recovery armed. Never interrupt a healthy deterministic computation merely to switch its supervising model.
- With unknown usage, start with one bounded worker, establish observed consumption if possible, use small resumable batches, and keep a verified fallback and failure alert. Do not fan out an unmeasured overnight campaign.

The master can select different triggers for a measured workload; record why. Check at phase/batch boundaries and on usage warnings, not on every tool call. Reserve for **all** workers sharing a budget, not independently for each. A successful tiny probe proves access at that instant, not sufficient allowance for the night. If a mandatory reviewer is already unavailable, identify that acceptance dependency before spending on the run; do useful independently verifiable phases while keeping acceptance pending.

## 3. Transfer and verify the complete handoff

Put these files in the experiment directory (or the owned working directory for a non-experiment task):

1. `cc.md` or another descriptive runbook: original objective and scope, inputs, completed work, exact next commands, expected outputs, success checks, ownership, known failures, forbidden changes, acceptance and landing instructions. Include relevant policy text or verified local copies; do not rely on the remote agent being able to read laptop paths.
2. `CKPT_<task>.md`: actual creation/update timestamps, current phase, commits, completed checks, unresolved findings, active process/job identity, source/runtime locations and exact resume step. The checkpoint is the resume record; never discard earlier findings when a provider changes.
3. `results.md`: live results and phase states, with measured counts and explicit limits. Follow Rules 37 and 44; the master checkpoint links to these files.
4. A dispatch manifest: exact models/efforts and accepted substitutes by role, immutable experiment pins, input file hashes, policy and project revisions, target paths, budget evidence, recovery owner, watchdog, notifications, and the handoff fields below.

Commit and push the **scanned, task-owned** instructions and available work to the repository's permitted publication path before launch. On the target, fetch the exact published revision into an owned clone/worktree and verify the files and their hashes. A laptop path or successful local commit is not delivery. For large or uncommittable artifacts, use an approved durable transfer with a manifest and verify the remote bytes; do not transfer credentials or publish secrets. A failed push may use that verified durable transfer to preserve progress, but record pending Git publication and do not call the result landed.

The target writes an acknowledgement containing the input revision/hash, actual model/effort from runtime evidence, working directory, named session, process identity, phase and next step. The master verifies a real first action and durable output, not merely a terminal session or exit code zero. Preserve private runtime snapshots during later `main` changes; never pull, stash, reset or move another worker's dirty checkout. Reconcile task-owned changes in an owned clone before landing under Rule 46.

## 4. Prepare executable recovery before leaving the job

For unattended work, the master must establish a **remote recovery owner** plus a watchdog: a small process that observes failure without needing a language-model response. A laptop-only heartbeat, a shell containing a dead agent, or an agent promising to watch itself is insufficient. Use a named persistent session, or an already-installed scheduler with verified restart behavior. A terminal session survives disconnection, not necessarily a node reboot; record the actual reboot recovery mechanism or that limitation.

The dispatch manifest names the watchdog command, configuration, state file, notification command, cadence, progress timeout, stopping condition and recovery owner. Verify its heartbeat and a harmless simulated failure notification before unattended hand-back; do not kill a live experiment to test it. Use a simulation mode or disposable command and mark any delivered test notice clearly as a test. Include all child jobs and repositories it owns. Stop the watch when verified completion is recorded, the user cancels, or blocked state is durably recorded and the scheduled retry/notification has been handed off. Waiting for a known reset needs an actual surviving wake-up, not just a time written in a file.

**The existing `snap_dispatch.sh`, `deploy_cc.sh`, legacy smart wrappers and observation-only monitors do not automatically implement this policy.** Use an existing tested recovery mechanism or provide a small task-scoped wrapper before an unattended launch. Do not report automatic failover as installed merely because this document was updated. The [direct-dispatch transport](remote-job-dispatch.md) remains the recommended launch path; no generic provider-guessing shell loop is authorized.

A watchdog observes native process identity (host boot identifier plus process start identity), descendants, scheduler/driver status, fresh checkpoints, provider errors and task completion evidence. Exit zero, a model's final response, or an empty pending queue alone is not success. Distinguish subscription exhaustion, transient rate limiting, authentication failure, transport loss, context exhaustion and actual task failure; preserve the original error. Model-specific denial does not establish provider-wide exhaustion. No progress alone is not proof of death: check healthy long compiles, transfers and remote children before stopping anything.

## 5. Recover without duplicating or changing the experiment

### Classify the stopping condition before choosing a route

Preserve the native error and the scope actually evidenced; a failure on one account, model, profile or host is not evidence that every account at that provider is exhausted. Keep these limits separate in the checkpoint:

| Observed limit | Required response |
|---|---|
| Subscription window, account credit/admin limit, model entitlement or provider outage | Check the affected scope and reset evidence; select another eligible existing account/client. Do not repeatedly reauthenticate a funding failure or infer a provider-wide outage from one account. |
| Context window, compaction failure or coordinator turn cap | Save a compact continuation packet and hand off to a supported fresh/native continuation or another eligible agent. A fresh session on the same funded account can suffice; do not call this account exhaustion. |
| Authentication, transport, unavailable tool or insufficient executor capability | Perform bounded supported repair or select an eligible route with the required tools and intelligence; unknown access remains unverified. |
| Frozen scientific calls, retries, coordinator launches, elapsed/resource budget, measured turn cap, failed admission/acceptance gate or user stop | Preserve the terminal/blocked scientific record. Changing account or session cannot reset the bound, retry a failed study, waive a gate or make an extra measured call. Continue only independently authorized work that the bound still permits. |

A coordinator's operational turn cap and a measured solver's protocol turn cap are different. Record which applied. Plan checkpointing before context/turn exhaustion and retain an ordinary-code recovery owner for abrupt exits. A new recovery policy is not retroactive authorization to reopen an exhausted experiment.

### Authentication recovery

An authorized ongoing task includes routine restoration of its existing account/client access. Do not hand Brando a generic “go log in” task, ask whether the browser is signed in before checking, or treat the Codex/Claude desktop app's login as proof that a cluster CLI has working credentials. Do not promise that credentials can always be renewed without a human.

1. **Diagnose the actual layer.** Preserve a sanitized error and identify host, executable/version, intended account/profile, credential-store location (not its contents), owner, last successful action and affected phase. Distinguish machine/network access, expired or revoked sign-in, wrong account/model entitlement, included-allowance exhaustion, available prepaid credit and administrator spending limits. Check network reachability before accepting a generic “invalid key” message as authentication failure. A login-status command may only confirm cached credentials; it is not a model-entitlement or budget test.
2. **Reserve one recovery writer.** Use the job recovery lock and explicit ownership of the credential profile; check other consumers before changing shared stores. Preserve or adopt healthy children and keep old evidence. Prefer an independent job-owned login profile when supported. Never copy an active Mac/other-worker refresh credential to a different host, log out every client, overwrite a shared credential store, or kill healthy work to repair one failed coordinator. Use supported unattended grants where available and already authorized; renewal of a shared grant still requires coordinated ownership.
3. **Complete the supported flow.** First allow the client to use its supported cached refresh. On an actual unrecoverable sign-in error, start one vendor-supported login on the target and complete its browser/device or remote authorization steps on an available authorized Mac. Check the user's existing normal browser session; a signed-out isolated browser does not establish that all browser sessions are signed out. Before approving a grant, match the displayed account, organization/workspace, client and requested access to the intended authorized profile. Resolve a mismatch before submission; if an essential identity cannot be established, stop at that concrete uncertainty rather than guessing. Only enter a device code generated by this recovery's own CLI into the matching official service. Keep codes, callback URLs, tokens, cookies and credential contents out of git, checkpoints, notifications, command arguments and ordinary logs; use the client's protected credential store. Do not create a generic unattended browser-click loop or bypass a service/security prompt.
4. **Involve Brando only when necessary.** Complete all automatable steps first. Ask for the single concrete password, verification, CAPTCHA, required human approval or other action actually presented and required by the applicable safety rules. New accounts, materially expanded access, changed credentials or new spending require their own authorization. If the browser/Mac is unavailable, record `WAITING_FOR_BROWSER` and retain the remote recovery owner; use an eligible already-authenticated alternative for permissible work, or one bounded retry when the browser returns. Never report a laptop-dependent flow as cluster-autonomous or reboot-safe.
5. **Verify and resume the smallest missing unit.** Confirm login completion on the target with the selected account/store and protected permissions. When a new profile is used, migrate only the necessary noncredential conversation metadata through the supported mechanism, verify its identity and preserved bytes, and distinguish a real native resume from a new checkpoint-based session. Preserve measured models, inclusive call budgets, completed trials and mandatory review families. Verify actual model/effort, process identity and a useful action/receipt after restart; `login succeeded` alone is not `worker recovered` or `task done`.
6. **Bound and record recovery.** Default to one login flow per incident/profile and at most one justified transient retry within the existing recovery attempt/deadline budget; do not loop on invalidated tokens or duplicate browser requests. Rearm only on a relevant new fact or user instruction. Record timestamps, sanitized failure class, profile owner, verified login and continuation states, remaining blockers and a deduplication key. Report meaningful recovery/blockage to the master and through Rule 48's authorized notification path. Never erase the original failure or reset measured/review attempts merely because authentication changed.

Codex's supported headless-device flow is documented in [OpenAI authentication](https://learn.chatgpt.com/docs/auth). For Cursor, use the installed client's browser login/status commands from [Cursor CLI authentication](https://cursor.com/docs/cli/reference/authentication); command names differ by version. Antigravity supports local keyring sign-in and a remote browser/code exchange in its [installation and authentication guide](https://antigravity.google/docs/cli/install/). Inspect installed help before using a command. Claude Code's existing SNAP grant guidance is in [the cluster workflow](../machine/snap.md); do not replace a working shared grant with a copied interactive login.

### Consistent policy and verified clients across hosts

Use the same agents-config policy revision on the MacBook Air, MacBook Pro and reachable SNAP nodes, with host-specific executable paths and credential stores. Fetch and read that revision before setup/dispatch; preserve unrelated dirty changes and existing workers. Keep secrets local to protected stores, never in the configuration repository. Do not silently overwrite global model defaults or another session's configuration to select one worker.

Record a small per-host capability manifest beside the dispatch/checkpoint: host and reachability; verified policy revision; client path/version and installation source; intended account/profile; supported model/effort and noninteractive permissions; approved subscription/prepaid route and applicable budget; authentication state; exact useful verification with timestamp; worker result/checkpoint callback; and missing dependencies. Distinguish `NOT_INSTALLED`, `INSTALLED_UNVERIFIED`, `AUTH_REQUIRED`, `ACCESS_VERIFIED`, `BUDGET_BLOCKED` and `UNREACHABLE`. A model catalog alone is not a successful execution or funding check. Mark a client eligible only for the verified role; leave offline machines explicitly pending instead of claiming universal synchronization.

Inventory the existing account/profile routes before declaring recovery exhausted, including supported signed-in browser/account selectors, client login/status and usage views, known launcher/profile metadata, and host manifests. Read only nonsecret identity/status evidence; never dump credential stores, tokens or cookies. Deduplicate aliases and shared allowances by actual account/organization and billing scope. Each row records a nonsecret profile label, host/client, account/organization and payer scope, role/model/effort, effective full access with routine approvals disabled, available allowance/reset (or unknown), evidence timestamp, attempts and disposition. An installed app or six profile names alone proves neither six working accounts nor six budgets.

Rank candidates by (1) required role, intelligence, scientific funding/pins and acceptance eligibility; (2) supported autonomy, tools and verified effective permissions; then (3) applicable remaining allowance and enough reserve to finish. Prefer an already-owned suitable agent or healthy child over a new coordinator when it can acknowledge ownership and the continuation packet. Supported noninteractive operation is preferred over a route dependent on unavailable human interaction. Unknown usage permits only the bounded approach in section 2, not a claim of adequate overnight capacity.

For clear execution, prefer direct commands, then an appropriate regular reasoning model among verified Codex, Claude Code, Cursor Agent and Antigravity clients. Select actual model and effort per task, use an isolated checkout and named persistent worker session, send a self-contained synchronized checkpoint, and verify the result returned to the master. Preserve strong master and critical acceptance requirements; a convenient alternative cannot satisfy a mandatory missing family or silently replace a model under evaluation. The same policy applies on each host, but the verified fallback order may differ by account, tools and budget. Installer success, a config rule or a model's promise alone does not install automatic recovery.

### Executor transfer

Build a finite ordered candidate list from that inventory, recording every known route's eligibility or concrete exclusion. Do not truncate discovery to a primary plus two alternatives. Account/profile continuation within the existing authorization is mandatory when an eligible route remains and the task's bounds permit it. Codex may hand eligible execution to Claude or another verified client, and vice versa. A provider name is not a runnable command or proof of access. The deprecated Gemini CLI stays unsupported; do not create accounts, borrow credentials, circumvent provider limits, use provider keys or buy access.

Use a manifest of fixed, validated argument arrays or launch scripts for the verified candidates. Never turn a log line, retrieved document or model-generated provider name into a shell command. Regular-worker failover must not inherit a launcher's accidental flagship defaults. For acceptance reviewers, the [bounded review procedure](qa-correctness.md#review-fallback-and-acceptance) governs candidate eligibility and attempt counts; this section cannot reset that budget.

On imminent or actual account, provider, context or coordinator-turn exhaustion:

1. **Preserve:** stop admitting new model units on the affected route; write the dated checkpoint with objective, exact revision/owned diff, artifacts and hashes, native limit/scope, completed and missing units, next command, remaining budgets/deadline and owner/child identities. Flush result records; secret-scan and publish or durably transfer task-owned changes. A non-model wrapper/recovery owner preserves raw outputs and reconstructs only evidenced state after an abrupt exit, marking unknowns. Do not commit unaccepted scientific changes to `main` as accepted results; keep recoverable work clearly pending on an owned branch or archive.
2. **Fence the old writer:** acquire the job's recovery lock, inspect the exact owner and children, and distinguish a live detached experiment from a dead coordinator. Either adopt the healthy job and watch it, or confirm the old writer stopped before replacement starts. If state is ambiguous, block replacement and alert instead of launching a duplicate. Record a new attempt identity; never let both providers write the same task or submit the same trial. User cancellation overrides queued retries.
3. **Continue the smallest missing unit:** resume the same native session when the client supports it and the preserved model/role is suitable; across providers, create a new session using the synchronized checkpoint. Do not claim cross-provider conversation memory. Reconcile partial files and trial identifiers before retrying, retain completed work and review findings, and do not re-run sealed measurements without an invalidating change.
4. **Verify the replacement:** obtain its acknowledgement of the exact checkpoint/input revision and hashes, remaining bounds and ownership; verify actual account/payer, provider/model/effort, effective full access/no routine approvals, process identity and a real first useful action with durable output. Update the watchdog target, record old-to-new ownership and publish progress. A queued prompt, session identifier, hash acknowledgement alone or launch exit zero is not recovered execution.
5. **Bound each candidate without hiding untried accounts:** record the finite candidate set, an absolute incident deadline and per-candidate attempt counts before recovery. Default to one useful launch per eligible candidate and at most one evidence-justified transient retry for that candidate: at most `2 × N` launches for `N` identified candidates, further restricted by every existing task/reviewer/scientific cap and deadline. Read-only inventory is separate from model launches; a model probe counts as a launch. Do not retry known blocked routes or add aliases to evade counts. A genuinely newly discovered account may amend the inventory with evidence within the original allocation; never reset spent attempts or extend deadlines. Re-arm a blocked route only after a relevant new fact such as a verified reset or repaired login, still within all existing bounds.

Keep a durable recovery receipt distinct from task completion: `CHECKPOINTED` (verified packet preserved), `HANDOFF_PENDING` (candidate selected, continuation not yet verified), `RESUMED_VERIFIED` (hash acknowledgement, permissions and first useful output checked), `WAITING_RESET` (known reset plus actual bounded wake-up), `BLOCKED_NO_ELIGIBLE_ROUTE` (every known route has an evidenced exclusion), or `BLOCKED_TASK_BOUND` (task cap/deadline/gate forbids continuation). Preserve prior receipts and state why each untried candidate was skipped. Three failed probes among six or more known accounts do not establish account exhaustion; if a genuine frozen three-launch cap stopped discovery/execution, report that cap and the remaining unverified routes instead. Never convert `UNREACHABLE` or unknown allowance into “exhausted.”

At a real blocker, continue independent authorized deterministic work, preserve missing scientific cells, and report the exact unmet boundary through the authorized channel below. Arrange a retry only when an actual surviving wake-up and the original allocation permit it; otherwise retain the checkpoint with no invented schedule. A remote owner must preserve this outcome even when the laptop is asleep. No recovery receipt alone means the task is `DONE`.

**Preserve scientific identity and acceptance.** An evaluation's measured model, judge, effort, sample set, seeds, budgets and scoring rules remain pinned. Switching its supervising executor can be valid; substituting Claude outputs for an Astra experiment changes the experiment and requires a separately authorized, separately reported run. Preserve explicit user-selected models and benchmark-reference requirements (both strongest Claude and Codex under Rule 43). A smaller executor or third provider can finish eligible preparation; it cannot sign off a mandatory missing reviewer. Plan this dependency early and report `execution complete; acceptance pending` when that is the true state.

## 6. Notify once per meaningful change and verify landing

For an unattended dispatch, maintain a durable repository event and use the task's authorized master/user notification channels. Existing Rule 48 notification authorization applies unless the task restricts it; an explicit no-email instruction wins, and account handoff adds no new notification authorization. Where email is authorized, use `brando.science@gmail.com` without carbon copies. A switch notice can cover its preceding warning; deduplicate by job/incident/state and do not notify on unchanged polls. Include what stopped, actual old/new account/provider/model/effort, verified replacement state, completed/remaining work, checkpoint link and any required human action. A queued master message alone is not user delivery while the master sleeps.

Validate only the authorized delivery path before launch; record actual delivery success or failure. If it is unavailable, use another already-authorized user channel or keep a pending receipt; never add email to a task that forbids it. A failed notification never erases an otherwise verified landing. No collaborator messages are authorized here. Completion notices still follow Rule 46; do not send a second completion email for the documentation-only landing record.

`DONE` requires the requested outputs, relevant deterministic checks, required review, verified merge/publication to `main`, and its durable completion record. Report notification delivery separately. A completed agent turn, a submitted pull request, a launch receipt, a quota reset or a provider switch is not task completion. The master reconciles every strand and reports what finished, what continues and what is blocked, with evidence and freshness.

## Dispatch manifest fields

Store these beside the runbook/checkpoint before dispatch. Replace every placeholder; this is a schema guide, not an executable launcher or proof that monitoring exists.

```text
job / objective / acceptance criteria:
master task + remote recovery owner + handoff lock:
project revision / policy revision / runbook + input hashes:
owned paths / target host + working directory / artifact store:
phase roles / exact primary provider-client-model-effort-command:
eligible alternatives in order + actual availability evidence:
account/profile inventory + shared allowance deduplication + exclusions:
immutable experiment pins / required review families and capability:
full input + model-task-seed/repetition manifest / expected cell count:
initial + continuation prompt hashes / fixed completion + continuation rules:
per-cell + whole-run limits / nested timeout checks / finalization reserve:
per-cell status + final artifact/check receipts / full-denominator completion gate:
usage snapshot + timestamp + shared account scope + next reset:
included allowance / applicable authorized prepaid balance / spend controls:
per-host client capability evidence / policy revision / unreachable hosts:
auth profile + owner / supported recovery flow / browser dependency:
next-phase estimate / finishing reserve / shared concurrency / triggers:
current phase / completed checks + findings / exact next command:
checkpoint / results / process + child job identifiers:
watch command + config + state / cadence + progress timeout:
watch smoke evidence / reboot behavior / stop or wake-up condition:
native limit + scope / fixed launch arguments / per-candidate attempts:
operational recovery cap + absolute deadline / frozen scientific + review caps:
recovery receipt state / skipped candidates + evidence / remaining allocation:
notification channel + delivery check + incident deduplication key:
effective permission mode + runtime evidence + pending approval mechanism:
remote checkpoint/input hash acknowledgement + account/model + first useful output:
verified main landing / completion record / notification outcome:
```

The worker runbook keeps its own title and closing TLDR (end-only) under Rule 36. It carries the relevant recovery and acceptance instructions; this manifest supplies exact values and evidence.

## Policy verification cases

Review a proposed dispatch against these cases before calling it unattended-ready:

| Situation | Required outcome |
|---|---|
| Task-creation tool has no permission field | Inspect child runtime permissions; use an eligible supported full-access client if needed, preserving platform boundaries and one writer. |
| Approval text was queued but the app still shows a pending request | Identify the actual request/control; do not claim recovery until the next useful action is verified. |
| One task passes while other declared cells remain pending | Evaluation remains partial; retain the complete manifest and execute remaining cells. |
| A solver emits a final message with an unfinished file | Apply only fixed continuations within cumulative bounds; verify the artifact and report incompleteness honestly. |
| The coordinator disconnects while a measured attempt is healthy | Durable owner and monitor keep the admitted procedure running; no coordinator-driven cancellation. |
| A cell exhausts its budget or infrastructure interrupts it | Preserve native cause, evidence and denominator; no silent extra attempt or best-of replacement. |
| Master is ultra; worker runs an established analysis script | Direct command or regular executor selected explicitly; finishing budget retained. |
| Several agents share a subscription with little allowance left | Combined budget/concurrency reduced or eligible alternate chosen before the next batch. |
| One OpenAI work account is quota-blocked; personal/school routes are known | Inventory and verify the other eligible existing accounts without asking again; do not report provider-wide exhaustion. |
| Three probes failed; six existing accounts are known | Keep untried accounts explicit and continue within the finite candidate budget; a binding task launch cap stops launches, not the truthfulness of the inventory. |
| Coordinator hits context or `max-turns` while its account has allowance | Checkpoint and use a suitable supported continuation/fresh agent; preserve any frozen coordinator-launch cap. |
| Scientific deadline, measured attempt budget or admission gate has stopped the run | Preserve that blocked/terminal outcome; another subscription cannot reopen it or reset its counters. |
| Quota stops an agent with exit zero while its compiler continues | No false DONE; preserve/adopt compiler, then resume only missing coordination. |
| Laptop sleeps and primary provider is exhausted | Remote watch records failure, fences the writer, uses the verified alternative and sends a notification. |
| Replacement command returns but never executes a useful step | Recovery remains unverified; bounded next action or explicit blocker. |
| Astra benchmark is unfinished and Claude can execute commands | Claude may supervise the fixed Astra run; benchmark outputs are not silently replaced with Claude outputs. |
| Required reference reviewer cannot run anywhere eligible | Preparation continues; acceptance remains pending with a durable notification and real retry plan where possible. |
| Source branch was pushed but target cannot read its runbook | No successful handoff; repair transfer or report it blocked. |
| Watcher loses contact with a possibly live owner | No second writer until ownership is resolved. |
| Mac app works but the cluster's saved refresh credential is revoked | One owner restores the target login through the supported flow; no copied active credentials; verify continuation separately. |
| Included Codex allowance is exhausted but authorized prepaid credit is available | Check account/model applicability and spend controls, then admit only the bounded authorized unit; do not call the entire account unfunded. |
| Vals Claude is signed in but an administrator spending limit blocks it | Classify as a spending limit; do not repeatedly log in, change the admin limit or expect Codex credits to fund Claude. |
| Cursor/Antigravity exists locally but remote authentication is unchecked | Remote client remains ineligible until actual target access, billing, tools and a useful action are verified. |
| A login needs a browser while both Macs are unavailable | Preserve/adopt live jobs, use only an eligible alternative, or record the real browser dependency and bounded retry; no false autonomous-recovery claim. |
| All approved subscriptions are unavailable | Preserve work, stop repeated probes, notify, and schedule a real bounded retry when possible; never purchase credits or use provider keys. |

## Source note

The exact provider allowances remain runtime facts. OpenAI's [official usage guidance](https://learn.chatgpt.com/docs/pricing) states that model, task size and context affect consumption, local and cloud work share allowances, and smaller models can extend usage. The thresholds and recovery procedure above are Brando's operational policy, not promises from OpenAI or any other provider.
