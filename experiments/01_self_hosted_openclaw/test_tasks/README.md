# OpenClaw Test Tasks — One-Shot Validation Inputs

**TLDR:** This directory holds **one-off** test inputs for the OpenClaw agent — discrete tasks that exercise the system end-to-end (multi-channel send, tone calibration, approval flow) once and don't need to recur. Distinct from `standing_orders/` (recurring workflows) and [`MASTER_PLAN.md`](../MASTER_PLAN.md) Appendix F (post-MVP capability backlog).

## When to put something here vs. elsewhere

| Where                     | Shape                  | Examples                                                  |
| ------------------------- | ---------------------- | --------------------------------------------------------- |
| `test_tasks/`             | One-shot, named, runnable | "DM Sri showing off the agent", "Email Saumya re: NeurIPS reciprocal reviewer" |
| `standing_orders/<name>.md` | Recurring or invocable workflow | Travel search watcher, monthly Lean AI workhackathon nudge, paper announcement |
| [`MASTER_PLAN.md`](../MASTER_PLAN.md) Appendix F | Idea, not yet shaped | "OpenClaw should handle SuperCare resupply (need trigger format)" |
| `concepts.md`             | Q&A explainer          | "What does X mean in Phase Y of the plan?"               |

A test task graduates **out** of this directory in two ways:

- It runs successfully and is logged in [`MASTER_PLAN.md`](../MASTER_PLAN.md) Status & Log → file kept here as historical record.
- The pattern recurs and is promoted to a `standing_orders/<name>.md` → file becomes a stub that points at the standing order.

## Shape of a test task file

Loose by design — these are throwaway-ish — but include at minimum:

1. **Title + TLDR** — one paragraph, what is this test actually exercising?
2. **Channel(s)** — Discord DM / Discord channel / Email / Telegram / multi.
3. **Inputs Brando needs to provide** — recipient handles, content placeholders.
4. **Drafted message(s)** — actual text the agent should send (or starting points).
5. **Approval flow** — same canonical `post / edit: / tweak: / cancel` vocabulary as standing orders.
6. **Prereqs** — what has to be true before this test can run (Discord intent enabled, exec-policy unlocked, etc.).
7. **Open questions** — anything Brando still has to fill in.
8. **What this test validates** — why it's worth running (what part of the system does it exercise?).
9. **Status** — drafted / blocked / executed / superseded.

## Current entries

- [`dm_sri_agent_flex.md`](./dm_sri_agent_flex.md) — first playful Discord DM from the agent to Sri ("this is brando's agent ;)"); validates Discord bridge + tone.
- [`email_saumya_neurips.md`](./email_saumya_neurips.md) — single email to Saumya asking her to register Brando as a NeurIPS reciprocal reviewer; validates Gmail send + Brando routing rule.

## Why this dir exists at all

The standing-orders template assumes **recurring** workflows. One-off requests don't fit that shape but still need a durable home — otherwise they live only in chat history and get lost when the session compacts. Capturing them here means:

- They survive session boundaries.
- They're greppable when a similar pattern shows up again ("we did this once for Sri, what did we say?").
- They serve as concrete first-uses for new capabilities (the Sri DM is the first multi-host Discord test; the Saumya email is the first cross-recipient Brando-routing send).
