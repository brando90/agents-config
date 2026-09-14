# One board for all agent work

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/agent-board-design/design.md>

**TLDR:** Extend the existing private board with automatic source collectors and optional structured task updates. Show active work first, explicit blockers and stale observations clearly, and confirmed completions from the last seven days at the bottom; never infer job completion from an idle or exited agent.

## Recommended shape

Keep `scripts/agent_board.py` and the existing local/phone view as the starting point. Separate collection, reconciliation and rendering instead of replacing the board with a new application. Updating a status table should use no model calls by default.

Each supported service/account gets a small collector using its actual local state, official interface or launch wrapper. Automatic discovery includes existing sessions without restarting them; optional structured updates add purpose, dependencies, human pauses and completion evidence. A generic registration command covers unsupported services but labels those rows self-reported or manually entered. Do not claim universal coverage until a coverage inventory lists every expected service, account and host with a verified collector or an explicit visibility limit.

The implementation currently covers personal/Vals Claude profiles, a limited local Codex list and three hardcoded cluster names. It defaults to six hours of history and eight Codex tasks. New cluster Vals profiles live at `/lfs/<node>/0/brando9/.claude-vals-node`; account recognition must be configurable. Desktop tasks sharing one application-server process need their native task identifiers; a process-count heuristic is insufficient.

## The table

| Field | Meaning |
|---|---|
| Project / task | User-facing title and stable task identity |
| Activity / work state | Two separate facts: what the agent is doing, and whether the requested work is complete |
| Service / account | OpenAI, Anthropic, xAI or other provider; personal, Vals or unknown account |
| Model / effort | Observed exact model and effort, with unknown explicit |
| Host / session | Where execution occurs and an inspected attach/open link |
| Latest update | Timestamp and short status; source freshness remains visible |
| Blocker / evidence | Specific dependency or link to result/checkpoint supporting the state |

A compact phone view stacks these fields. Active rows come first, with blockers clearly highlighted; paused/idle and stale/unknown work stay visible. Confirmed finished tasks appear in a separate bottom section, newest completion first, retained for seven days. Preserve useful existing terminal ordering within active groups. Include search and filters for project, account, service and host.

Account labels are not billing attestations. Show payer or remaining allowance only if separately verified, otherwise unknown. Never copy credentials, full prompts, transcripts or unrestricted process arguments into the board.

## Trustworthy state

Use two dimensions. Agent activity can be running, idle, exited, or unknown. Work state can be in progress, blocked, paused, reported complete, verified complete, failed, or unknown. A finished response, a closed terminal and an exit code describe an attempt, not the whole task. Explicit completion evidence must match the task's scope; publication requirements may remain pending after execution finishes.

Store logical task identity separately from execution-attempt identity. Resuming the same task preserves its row while recording a new attempt; concurrent processes must remain inspectable rather than disappearing through deduplication. Parent/child relations connect supervisors to remote jobs without conflating their states.

A human pause is sticky until an explicit authorized resume. Missing hosts preserve last-known task state with a stale observation badge. A timeout or old timestamp never proves failure, abandonment or completion. Seven days is a finished-history filter, not a timeout for unfinished jobs. Mark declared completion separately from independently verified completion. Accept only bounded timestamps, and handle clock skew explicitly.

## Collection and transport

Maintain an explicit allowlist of source adapters and hosts. Each collector has a deadline and produces an atomic versioned snapshot with source identity, collector epoch, sequence number, observation time, last-success time and errors. The merger replaces snapshots only within that source/epoch; sequence numbers alone are unsafe after a collector restart. Keep durable terminal events so tasks completed during an offline interval appear after reconnection. Tombstones and retention rules must avoid both resurrection and silent loss of unfinished tasks.

Use existing authenticated connections for bounded metadata transfer. Add a minimal `agent-board-event` command to launch wrappers and applicable agents-config entry points, without requiring language models to write a status message on every poll. Failed reporting cannot stop experiment computation. Do not dynamically execute arbitrary collector modules, remote commands or links supplied by a status file.

The observer displays jobs; it does not restart, kill, log in, spend money or change experiment settings. Those controls remain with their existing owners. Register both Macs and the reachable cluster nodes. Discover Cursor, Grok/xAI and browser/cloud tasks through supported interfaces only; absent access becomes an explicit coverage gap.

## Phone access

Keep the current private Tailscale Serve route, which forwards only the board page from the loopback server. The existing URL is reachable only within the authorized private network; it is not a public website. No public publishing or new hosting is part of this design.

Today the Mac hosts both rendering and serving, so sleep breaks availability. First restore honest refresh and per-source staleness. If reliable access during laptop sleep is required, select an approved always-on host later, with a private authenticated snapshot store and explicit access review. Do not assume a cluster node can reach the laptop or that a cloud subscription is already authorized.

## Phased implementation and acceptance

1. **[p 9/10] Establish truthful coverage, because missing active jobs defeats the board:** inventory expected sources, replay a small labeled sample of existing task records, remove silent row caps, add explicit activity/work state, account and freshness fields, and seven-day confirmed-completion history.
2. **[p 8/10] Extend reporting across machines, because remote jobs outlive laptop sessions:** add configured hosts/profiles, versioned snapshots, stable task/attempt identities and optional lifecycle updates; verify offline/reconnect and restart behavior without restarting live agents.
3. **[p 6/10] Add remaining services and resilient phone hosting, because these depend on actual access:** implement supported additional adapters, show unsupported sources explicitly, and assess an always-on private host if Mac sleep remains a material limitation.

Here `p` means predicted priority, not difficulty. No calendar estimates are accepted without a measured first implementation pass.

Cheapest decisive test: label roughly 30 existing tasks across accounts, live/idle/failed states and remote disconnects; compare proposed classifications with actual task records. Any false verified-completion is a failure. Measure missed active tasks and explicitly unsupported sources instead of claiming everything is covered.

Required tests include shared application processes, same task resumed twice, concurrent attempts, rebooted collector sequence reset, clock skew, stale hosts, sticky pauses, task completion vs process exit, boundary timestamps at seven days, HTML escaping, secret-bearing titles/arguments, untrusted URLs, atomic writes and overlapping refreshes. Fixtures and deterministic replay suffice for this phase; no experiment model calls are needed.

## Review provenance and limits

Requested reviewer: Vals Claude Code, `claude-opus-5`, `max`. Native assistant metadata verifies both. One initial response simulated unavailable tools instead of supplying a design and was rejected; one corrected invocation produced the design, session `6cfa939f-941f-4d91-9750-445c9928b596`. The CLI also reported auxiliary Haiku usage; the design response itself was Opus 5. Reported token-price estimates are not receipts for an extra bill.

Codex reconciled the proposal against existing code and rejected its unsafe shortcuts: process exit as task completion, a live process clearing a human pause, automatic abandonment after seven days, source sequence numbers without reboot identity, and assumed coverage of undiscovered services. The implementation and its required independent review remain future work. This design does not certify any new collector or claim that all agents are already represented.

**TLDR-end:** [ac: agent-board] Reuse the private board with automatic discovery plus optional task events, a visible coverage inventory and separate activity/completion evidence. Restore observability first; add service adapters and resilient hosting only against verified interfaces and access.
