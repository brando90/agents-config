# OpenClaw Concepts — Q&A Explainer Reference

**TLDR:** Plain-English explainers for non-obvious OpenClaw design decisions. Each entry leads with a one-line `**A (TLDR):**` direct answer, followed by detail. Append new Q&As here as they come up — this is the durable home for the kinds of "wait, why?" questions that would otherwise live only in chat history.

Format: every entry follows `### Q: <question>` → `**A (TLDR):** <one-line direct answer>` → `**Detail.** <as long as needed>`.

---

## Q1: One Telegram bot per instance — `getUpdates` 409 conflicts. What does that mean and why?

**A (TLDR):** Telegram only lets one process long-poll a bot token at a time; with 3 OpenClaws sharing one token, two of them get `HTTP 409` and lose messages — so each host gets its own bot.

**Detail.** A Telegram bot receives messages either via webhooks (Telegram POSTs to a URL you own) or long-polling (your code calls `getUpdates` and Telegram holds the connection open until a message arrives). OpenClaw uses long-polling.

Telegram only allows **one process at a time** to hold an open `getUpdates` call per bot token. A second process trying with the same token gets `HTTP 409 Conflict` — they fight, messages drop. Upstream docs are explicit: *"If you still see `getUpdates` 409 conflicts, another OpenClaw gateway, script, or external poller is likely using the same token."* ([source](https://docs.openclaw.ai/channels/telegram.md))

**Why this matters here.** Three OpenClaw instances (Air + Pro + mercury2) sharing one bot token = three processes calling `getUpdates`. Two of them get 409'd constantly. Messages get lost. The redundancy goal is defeated.

**The fix ([`MASTER_PLAN.md`](./MASTER_PLAN.md) Step 3.1 + 4.3).** Each host gets its own `@BotFather` bot:

| Host     | Bot                                                      |
| -------- | -------------------------------------------------------- |
| Air      | `@ultimate_brando9_sk_air_bot` (renamed from existing)   |
| Pro      | `@ultimate_brando9_sk_pro_bot` (new)                     |
| mercury2 | `@ultimate_brando9_sk_mercury2_bot` (new)                |

Brando DMs whichever bot is handy; that instance handles the conversation. All three post to the shared `openclaw-ops` channel — channels are write-only fan-out, not polled, so no 409 risk there.

**Alternative considered + rejected.** OpenClaw's [`--profile rescue` pattern](https://docs.openclaw.ai/gateway/multiple-gateways.md) lets only the primary bot DM Brando, with the others silent until the primary dies. Cleaner UI (one bot to DM), but more failover complexity. Default plan is 3 active bots since the agent already rate-limits to 2 DMs/min total — redundancy beats tidiness here.

---

## Q2: What is cron and why do we need it?

**A (TLDR):** cron is a "run X every N minutes" scheduler; OpenClaw ships a built-in (`openclaw cron add`) that we use for heartbeats every 15 min and the silence watcher.

**Detail.** **cron** is a scheduler — "run this command on this recurring schedule." Name comes from the Unix `cron` daemon (1975). Schedule format is five fields (minute, hour, day-of-month, month, day-of-week):

```
*/15 * * * *   = every 15 minutes
0 7 * * *      = every day at 07:00
0 9 * * MON    = every Monday at 09:00
```

`*` means "any"; `*/15` means "every 15."

**OpenClaw ships its own cron** ([`openclaw cron add`](https://docs.openclaw.ai/automation/cron-jobs.md)). Register a job once; OpenClaw runs it forever, persisted at `~/.openclaw/cron/jobs.json`, surviving gateway restarts. So we don't need system cron and we don't need to write a custom watchdog loop.

**Why we need it for OpenClaw:**

1. **Heartbeats** — each instance posts `[host] alive @ <ts>` to `openclaw-ops` every 15 min. Without this, there's no way to notice if mercury2 silently died. ([`MASTER_PLAN.md`](./MASTER_PLAN.md) Step 2.2.)
2. **Silence watcher** — a separate cron checks "did peer X post in the last 30 min? if not, alert." That alert is the trigger that surfaces a crash.
3. **(Possibly) the triage poll loop itself** — the "every 90s, scan unread admin emails" cycle may end up as a cron job too, depending on how OpenClaw's agent loop is wired (vs. an internal agent timer).

Without cron we'd hand-roll a bash `while true; sleep 900; ...` per host and plumb it into launchd / tmux ourselves. Cron is the cleaner standard tool for "do X every N minutes."

---

## Q3: What does "Idempotency + ops layer" mean in [`MASTER_PLAN.md`](./MASTER_PLAN.md) Phase 2?

**A (TLDR):** Idempotency = Gmail-label locks so the 3 instances don't double-send the same reply; ops layer = heartbeats + silence watcher + rate limits posted to a private Telegram channel. Together they're the safety net that makes multi-instance safe.

**Detail — Idempotency (the duplicate-send prevention layer).**

**Idempotency** = doing something twice has the same effect as doing it once. In English: *no duplicates even when racing.*

**The problem it solves.** All 3 OpenClaw instances read the same Gmail inbox. They poll independently. If two of them spot the same unread admin email at the same instant, without coordination they'd both: draft a reply, DM Brando in Telegram, wait for "approve", send the email. Result: **two replies sent**, two DMs to Brando, embarrassing chaos.

**The fix ([`MASTER_PLAN.md`](./MASTER_PLAN.md) Step 2.1).** Use Gmail labels as a poor-man's distributed lock.

```
Instance A spots email → applies label "claw-claimed-by-mac-air" (atomic, Gmail-side)
Instance B spots same email → sees the label → skips it
Instance A drafts → DMs Brando → on approve, sends → swaps label to "triaged-by-claw"
```

Plus a **5-minute stale-claim TTL**: if Instance A crashes mid-draft (claim label set but never resolved), after 5 min Instance B can "steal" the claim and finish. Otherwise a crashed instance would freeze that email forever.

Why Gmail labels work as a lock: applying a label is atomic on Gmail's server. Either it's there or it isn't — no race condition on the lock itself.

**Detail — Ops layer (alarm system + rate limits).**

Three small mechanisms, all on Telegram:

1. **Heartbeat** — each instance posts `[host] alive @ <ts>` to private `openclaw-ops` every 15 min via `openclaw cron add`. One channel scrollback shows all 3 reporting in.
2. **Silence watcher** — separate cron posts `[mercury2] SILENT >30min — investigate` if a peer stops checking in. That's how Brando notices mercury2 died at 3am.
3. **Rate limits** — max 1 approval-DM per minute per instance, max 2 per minute total. If the agent goes haywire, the worst case is 2 DMs/min spam, not 200.

Plus **lifecycle events**: agent posts `STARTING` on boot and `RECOVERED` after a crash → the launch/recovery shows up in the same channel where heartbeats land.

**Why this is its own Phase (between Phase 1 Air-only and Phase 3 Pro):**

- **Phase 1 (Air alone):** No race possible — only one reader. No need for idempotency.
- **Phase 2 (build the layer on the Air):** Build + test the locking + heartbeat mechanism while there's still one reader. It's a no-op with one instance, but **the mechanism is wired and proven** before adding Pro.
- **Phase 3 / 4 (add Pro + mercury2):** Now there's actually a race. The lock catches it. Skip Phase 2 → first day Pro is online, you'll get duplicate sends.

Mental model: *"Phase 1 = the feature works. Phase 2 = the feature still works when 3 of them are running. Phase 3/4 = actually start the other 3."*

---

## How to add a new Q&A entry

1. Append a new section: `### Q<N>: <the question>`.
2. First content line: `**A (TLDR):** <one-line direct answer>` — must fit on one line, must answer the question, no hedging.
3. Then `**Detail.**` paragraph(s). Cite file:line in this repo (or upstream OpenClaw docs URL) when grounding a claim.
4. Cross-reference from `MASTER_PLAN.md` if the concept needs to be visible in the main plan.

This file is referenced from [`MASTER_PLAN.md`](./MASTER_PLAN.md) §10 cross-references.
