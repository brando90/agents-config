# Experiment 01 — OpenClaw Admin Assistant Wishlist

**TLDR:** Running, append-only backlog of everything Brando wants the self-hosted OpenClaw admin assistant to handle, grouped by channel/domain. The current `cc_prompt.md` covers only the email-triage MVP — this file is the long-tail list so nothing gets forgotten as the assistant matures.

> **How to use this file:** drop ideas into the right section as they come up, no formatting fuss. When an item is ready to actually build, promote it to a `standing_orders/<name>.md` (recurring) or `skills/<name>/SKILL.md` (on-demand) and link back here.

## Operating principle (re-stated, do not weaken)

OpenClaw **drafts and prepares**. Brando **approves**. OpenClaw **executes only after explicit approval**. Never auto-reply on any high-value channel (email, Discord, WhatsApp, mailing lists, forms). Voice-triggered drafts are fine because *Brando initiated the request* — but the draft still needs his review before send.

Default approval level per channel:
- email → `approve_to_send`
- WhatsApp → `approve_to_send` (auto-reply is `never_autonomous`)
- Discord → `approve_to_send`
- mailing-list blast → `never_autonomous` (always explicit)
- web forms / grants / Stanford official submissions → `never_autonomous`
- travel booking / payments → `never_autonomous`

## Channel / domain backlog

### Email (Gmail)
- [ ] Daily admin-email digest in WhatsApp (current MVP — see `cc_prompt.md`)
- [ ] Draft replies for Stanford admin, financial aid, conference orgs
- [ ] Reply templates: polite yes / polite no / ask deadline / schedule meeting / defer / health-constrained delay
- [ ] Mailing-list announcement drafts (bachata, zouk, Lean AI Club)

### WhatsApp
- [ ] **Voice-dictation → cleaned draft → approve → send** — see `standing_orders/whatsapp_voice_draft.md`
- [ ] Reply drafts to incoming messages (pull-only, no auto-reply)
- [ ] Convert incoming messages into todos / proposals / grant ideas
- [ ] Outbound class reminders (bachata / zouk) — drafted, approved, sent

### Discord
- [ ] Triage threads in personal + Lean AI Club servers
- [ ] Draft replies (never auto-reply)
- [ ] Long-thread → 1-paragraph summary
- [ ] Convert messages into todos / grant opportunities / project ideas

### iMessage / Telegram
- [ ] Telegram fallback if WhatsApp Baileys flakes (per `cc_prompt.md` Phase 3)
- [ ] iMessage via AppleScript bridge (local Mac instance only)

### Stanford admin
- [ ] Fill repetitive forms (screenshot-before-submit + approval)
- [ ] Draft messages to financial aid, registrar, dept staff
- [ ] Bureaucracy checklists (visa, employment, reimbursement)
- [ ] Never submit official forms autonomously

### Grants (Stanford + Lean AI)
- [ ] Intake from email / Discord / WhatsApp / pasted text
- [ ] Extract: deadline, eligibility, page limits, budget rules, required materials, links, letters
- [ ] Produce checklist + initial draft of application material
- [ ] Reusable bio paragraphs (50 / 100 / 250 / 500 words)
- [ ] Reusable project summaries (Lean AI, VeriBench, formal verification)
- [ ] Never submit without explicit approval

### Web forms (general)
- [ ] Inspect form → map fields → draft answers → fill safe fields
- [ ] Screenshot before submit
- [ ] Never bypass CAPTCHA
- [ ] Never enter payment info

### Travel
- [ ] Flight search (cheapest reasonable / best schedule / reimbursement-safe)
- [ ] Compare options, summarize tradeoffs
- [ ] Never book without approval, never enter payment info
- [ ] Preference template: home airport, alternates, max layovers, red-eye tolerance, reimbursement constraints

### Event ads (bachata / SBSBZ zouk / social dance)
- [ ] Weekly drafting workflow
- [ ] Channel variants: mailing list, Discord, WhatsApp, Instagram caption, short text blurb
- [ ] Templates: class announcement, social event, reminder, cancellation, venue change
- [ ] Approval before any post / send

### Lean AI Club
- [ ] Weekly meeting announcements
- [ ] Speaker / reading group / project recruiting messages
- [ ] Grant opportunity broadcasts
- [ ] Follow-up notes ("thanks for attending")
- [ ] Lean AI grant drafting

### Quality-of-life
- [ ] Convert any inbound message (any app) into: draft / todo / proposal / grant / form answer / announcement
- [ ] "What did I commit to today?" daily summary
- [ ] "What's overdue?" weekly summary

## Promotion path

When an item here matures into a real workflow:
1. Move the spec to `standing_orders/<name>.md` (recurring) or `skills/<name>/SKILL.md` (on-demand).
2. Define inputs, outputs, approval level, audit logging.
3. Add a row to `cc_prompt.md` Status & Log.
4. Tick the checkbox here so it's clear it's done.

## Out of scope for this experiment

- Inbound-webhook receivers in `uutils` (uutils stays a notification/utility library)
- Hosted myclaw.ai
- Auto-reply on any consequential channel
- Anything that moves money or submits an official Stanford / grant form without approval

## Status

| Date | Item | Status |
|------|------|--------|
| 2026-04-26 | Wishlist file created | seeded with current backlog from ChatGPT planning convo |
| 2026-04-26 | WhatsApp voice-dictation flow spec'd | see `standing_orders/whatsapp_voice_draft.md` |
