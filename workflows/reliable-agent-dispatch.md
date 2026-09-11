# Reliable agent dispatch and quota recovery

**TLDR:** A capable master plans the whole path to verified completion, chooses proportionate workers, and transfers a self-contained handoff before launch. Remote recovery must survive both the laptop sleeping and the worker exhausting its subscription; changing the executor must preserve the experiment, completed evidence, and acceptance requirements.

This is the operational procedure for `~/agents-config/INDEX_RULES.md` Trigger Rule 48, requested by Brando on September 11, 2026. It applies to every provider and to long local jobs as well as Stanford Network Analysis Project (SNAP) jobs. It improves the chance of completion; finite subscriptions and unavailable required reviewers cannot be made unlimited by a prompt.

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

Preselect a short ordered list of **eligible** executors: normally a primary and up to two alternatives across available approved subscriptions. This is authorization to continue the existing task, not to broaden scope, weaken tests or buy access. Codex may hand routine execution to Claude, and vice versa. Google models through a supported subscription-authenticated client, Cursor-hosted models, Grok or another named provider are candidates when the master verifies the client on the target, exact model and effort, required tools/context, allowed data access, subscription billing and completion/notification support. A provider name is not a runnable command or proof of access. The deprecated Gemini CLI is not revived by this permission; use a working supported client. Do not create accounts or borrow credentials to evade limits, use provider API keys, buy paid credits automatically, or circumvent provider limits. Existing authorized use of the user’s own subscription on their machines remains allowed.

Use a manifest of fixed, validated argument arrays or launch scripts for the verified candidates. Never turn a log line, retrieved document or model-generated provider name into a shell command. Regular-worker failover must not inherit a launcher's accidental flagship defaults. For acceptance reviewers, the [bounded review procedure](qa-correctness.md#review-fallback-and-acceptance) governs candidate eligibility and attempt counts; this section cannot reset that budget.

On imminent or actual exhaustion:

1. **Preserve:** stop admitting new model units on the affected allowance; write/checkpoint current work and error, flush result records, secret-scan and publish or durably transfer task-owned changes. A non-model wrapper can preserve raw outputs if the agent dies before writing its summary. Do not commit unaccepted scientific changes to `main` as accepted results; keep recoverable work clearly pending on an owned branch or archive.
2. **Fence the old writer:** acquire the job's recovery lock, inspect the exact owner and children, and distinguish a live detached experiment from a dead coordinator. Either adopt the healthy job and watch it, or confirm the old writer stopped before replacement starts. If state is ambiguous, block replacement and alert instead of launching a duplicate. Record a new attempt identity; never let both providers write the same task or submit the same trial. User cancellation overrides queued retries.
3. **Continue the smallest missing unit:** resume the same native session when the client supports it and the preserved model/role is suitable; across providers, create a new session using the synchronized checkpoint. Do not claim cross-provider conversation memory. Reconcile partial files and trial identifiers before retrying, retain completed work and review findings, and do not re-run sealed measurements without an invalidating change.
4. **Verify the replacement:** check actual provider/model/effort and a real first action/output, update the watchdog's expected process identity and target, record the old-to-new ownership change and publish the progress record. A queued instruction without acknowledgement is not recovered execution.
5. **Notify and bound retries:** report the switch and remaining work to the master and Brando as specified below. Try each planned candidate once per incident, with at most one justified transient retry, within the recorded wall-clock deadline and global attempt cap. The default cap is three launch attempts per incident; known exhausted candidates are not retried in a tight loop. Preserve spent attempts across replacements. Re-arm only on a relevant new fact, such as a real quota reset, fixed authentication, or user instruction.

If no eligible candidate remains, continue independent deterministic work, set the blocked phase explicitly, and arrange one bounded retry after a verified reset time when available. If reset time is unknown, notify and retain a resumable checkpoint; do not fabricate a wake-up or claim the task finished. The remote recovery owner must still report this outcome when the laptop is asleep.

**Preserve scientific identity and acceptance.** An evaluation's measured model, judge, effort, sample set, seeds, budgets and scoring rules remain pinned. Switching its supervising executor can be valid; substituting Claude outputs for an Astra experiment changes the experiment and requires a separately authorized, separately reported run. Preserve explicit user-selected models and benchmark-reference requirements (both strongest Claude and Codex under Rule 43). A smaller executor or third provider can finish eligible preparation; it cannot sign off a mandatory missing reviewer. Plan this dependency early and report `execution complete; acceptance pending` when that is the true state.

## 6. Notify once per meaningful change and verify landing

Standing authorization from this rule: for an unattended dispatch, notify the master through its available task/queue channel **and** maintain a durable repository event. Email `brando.science@gmail.com`, with no carbon-copy recipients, when quota threatens the planned finish, a provider handoff succeeds or fails, or the recovery chain is exhausted. A switch notice can cover its preceding warning; deduplicate by job/incident/state and do not email unchanged polls. Include what stopped, actual old/new provider/model/effort, verified replacement state, completed/remaining work, checkpoint link and any required human action. A queued master message alone is not user delivery while the master sleeps.

Validate the email helper import and available authenticated delivery path before launch; record actual delivery success or failure. If mail is unavailable, deliver through another already-authorized user channel and keep a pending receipt. A failed notification never erases an otherwise verified landing. No collaborator messages are authorized here. Completion notices still follow Rule 46; do not send a second completion email for the documentation-only landing record.

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
immutable experiment pins / required review families and capability:
usage snapshot + timestamp + shared account scope + next reset:
next-phase estimate / finishing reserve / shared concurrency / triggers:
current phase / completed checks + findings / exact next command:
checkpoint / results / process + child job identifiers:
watch command + config + state / cadence + progress timeout:
watch smoke evidence / reboot behavior / stop or wake-up condition:
failure classifier / fixed launch arguments / global attempts + deadline:
notification channel + delivery check + incident deduplication key:
remote input acknowledgement + actual model + first-action evidence:
verified main landing / completion record / notification outcome:
```

The worker runbook keeps its own title, opening summary and closing TLDR under Rule 36. It carries the relevant recovery and acceptance instructions; this manifest supplies exact values and evidence.

## Policy verification cases

Review a proposed dispatch against these cases before calling it unattended-ready:

| Situation | Required outcome |
|---|---|
| Master is ultra; worker runs an established analysis script | Direct command or regular executor selected explicitly; finishing budget retained. |
| Several agents share a subscription with little allowance left | Combined budget/concurrency reduced or eligible alternate chosen before the next batch. |
| Quota stops an agent with exit zero while its compiler continues | No false DONE; preserve/adopt compiler, then resume only missing coordination. |
| Laptop sleeps and primary provider is exhausted | Remote watch records failure, fences the writer, uses the verified alternative and sends a notification. |
| Replacement command returns but never executes a useful step | Recovery remains unverified; bounded next action or explicit blocker. |
| Astra benchmark is unfinished and Claude can execute commands | Claude may supervise the fixed Astra run; benchmark outputs are not silently replaced with Claude outputs. |
| Required reference reviewer cannot run anywhere eligible | Preparation continues; acceptance remains pending with a durable notification and real retry plan where possible. |
| Source branch was pushed but target cannot read its runbook | No successful handoff; repair transfer or report it blocked. |
| Watcher loses contact with a possibly live owner | No second writer until ownership is resolved. |
| All approved subscriptions are unavailable | Preserve work, stop repeated probes, notify, and schedule a real bounded retry when possible; never purchase credits or use provider keys. |

## Source note

The exact provider allowances remain runtime facts. OpenAI's [official usage guidance](https://learn.chatgpt.com/docs/pricing) states that model, task size and context affect consumption, local and cloud work share allowances, and smaller models can extend usage. The thresholds and recovery procedure above are Brando's operational policy, not promises from OpenAI or any other provider.
