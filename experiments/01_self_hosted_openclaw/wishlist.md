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
- [x] Flight search (cheapest reasonable / best schedule / reimbursement-safe) — promoted to [`standing_orders/travel_search.md`](./standing_orders/travel_search.md) 2026-05-08
- [x] Compare options, summarize tradeoffs — covered by `travel_search.md`
- [x] Never book without approval, never enter payment info — encoded in `travel_search.md` § Safety rules
- [x] Preference template: home airport, alternates, max layovers, red-eye tolerance, reimbursement constraints — encoded as `travel_search.md` § Inputs

**First concrete trip — McAllen / Harlingen summer 2026:**
- **Window:** Sat Jun 13 → Sun Jun 21 2026 (the 8-day natural gap between Stanford spring quarter end Jun 10 and summer quarter start Jun 22)
- **Backup window:** Aug 16 → Aug 23 (after summer quarter ends Aug 15) if June 13–21 doesn't work
- **Origin:** SFO (alt: SJC, OAK)
- **Destinations:** MFE (McAllen) OR HRL (Harlingen) — flexible, pick whichever is cheaper / more convenient
- **Duration:** 8 days, depart Sat morning, return Sun evening
- **Ceiling:** TBD by Brando (typical SFO→RGV is $300–500 RT)
- **Airline:** Southwest preferred (carry-on free, frequent SFO→DAL/HOU→RGV routes); American/United also fine
- **Why first test:** real trip Brando actually wants to book → proving-ground for the `travel_search.md` standing order end-to-end
- **Status:** spec'd, blocked on `travel_search.md` going live (Phase 6.8)
- Verified Stanford 2026 calendar: spring quarter ends Wed Jun 10, commencement Sun Jun 14, summer quarter Mon Jun 22 → Sat Aug 15 ([source](https://studentservices.stanford.edu/calendar-events/academic-calendars/stanford-academic-calendar-2025-2026))

### Personal portals — medical / utilities / subscriptions

- [ ] **SuperCare ASV resupply auto-confirmation** — Brando uses a ResMed AirCurve / BiPAP ASV machine for sleep apnea. SuperCare Health (his DME supplier) gates each insurance-defined resupply cycle (masks every 1–3 mo, headgear/tubing on staggered cadences) on Brando confirming "yes still using, ship the next batch."
  - **Tier 1 (easy)** if SuperCare's trigger is **email-based**: add their sender to `config/admin-filter.txt`; triage agent drafts "yes please ship, machine in active daily use" → Brando approves in Telegram → agent sends. Slots straight into the email-triage MVP.
  - **Tier 2 (medium)** if **portal login required**: use OpenClaw's bundled `browser` plugin per [`todos.md`](./todos.md):75. Credentials in `~/keys/supercare_credentials.json` (mode 600). Screenshot-before-submit per the standing-orders default safety rules.
  - **Tier 2.5 (harder)** if **SMS**: needs Twilio or iMessage relay; Telegram can't see SMS.
  - **Tier 0 (out of scope)** if **phone-call only**: voice agent territory; not realistic for v1.
  - **Status:** blocked on Brando forwarding one recent SuperCare resupply notification (any redacted PII fine) so we know which tier applies before designing.

- [ ] Other recurring personal-portal logins (utilities, subscriptions, doctor portals) — same pattern as SuperCare; add as they come up.

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
