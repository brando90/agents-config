# Unified agent board design review

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/agent-board-design/prompt.md>

**TLDR:** Design an extension of the existing agents-config agent board for all active and recently finished agent work across companies, personal and Vals accounts, both Macs and Stanford nodes. Produce a concrete, phased recommendation with evidence-backed status semantics and one week of finished work at the bottom; do not implement, start jobs, or change access.

User request: restore the usefulness of ~/.agent-board/board.html and its phone link. Include OpenAI, Anthropic, Grok/xAI, other services, personal and Vals accounts. Active work first; finished within seven days at the bottom. Think through the difficult design before implementation.

Verified current facts:
- Existing implementation is scripts/agent_board.py in agents-config; runtime HTML under ~/.agent-board, not a committed generated file.
- Local collectors parse Claude personal and Vals transcripts/registries and Codex transcripts. A generic external.json exists. SNAP poller names only skampere1, skampere2, skampere3. Code defaults to six-hour history and eight Codex tasks.
- Rows currently group by personal Claude, Vals Claude, local Codex, cluster jobs; ordered by terminal tabs. There is no universal lifecycle event protocol.
- Mac renderer was disabled; this session restored the existing deterministic 20-second renderer. Summarizer (personal claude -p every five minutes) stays disabled. Avoid model calls for routine updates.
- Existing private Tailscale Serve connection forwards only board HTML from loopback port8766; public Funnel is disabled. Renderer and link depend on this Mac staying awake. No new public exposure authorized.
- Many Codex desktop tasks can share an app-server process: never equate a process with one task. A completed response/idle terminal does not mean completed experiment. Scheduled checks and remote children are separate state.
- Target machine/service unreachable means unknown/stale, not failed/finished. Human-requested pauses remain pauses. Resumed tasks keep stable identity. Multiple snapshots must not duplicate rows. Missing data must be explicit.
- Model and account are different fields; routing via a profile does not prove payer or independent allowance. Never copy credentials, raw transcript contents or sensitive command arguments to the board.
- Use provider-supported local state/hooks/CLI access; do not invent Grok/remote connectors. Each unsupported source needs explicit coverage state and optional manually registered jobs. Keep observer separate from job control, authentication recovery and model spending.

Provide: recommended minimal architecture, canonical row/event fields, source evidence precedence and lifecycle state machine, active/blocked/idle/stale vs recently finished rendering, per-host collection and offline reconciliation, plugin/collector approach, private phone access and laptop-sleep tradeoffs, how to migrate existing live agents without restart, deduplication/retention/security tests, and 3 prioritized implementation phases. Explain whether every agent should report itself or combine automatic discovery and optional structured status events. Name the consequential uncertainty and cheapest test. Keep answer <=1400 words. Report assumptions and missing visibility honestly. This is a design opinion, not acceptance review of future code.

TL;DR: Review the supplied current implementation and propose a small, extensible, private board with trustworthy per-task status, all account/service dimensions and seven-day completed history. Return a design only; no actions or deployment.
