# OpenClaw Standing Orders — Shared Template & Conventions

**TLDR:** Every standing order in this directory follows the same shape (capture → clean → show → approve → execute → log) and uses the same approval vocabulary (`post` / `edit:` / `tweak:` / `cancel`). This file is the template. New standing orders should copy `_TEMPLATE.md` (below, inline) and fill in the workflow-specific bits.

## What is a standing order?

A standing order is a **named, reusable workflow** OpenClaw can execute on demand. It's distinct from:

- **Skills** (`~/openclaw/skills/`) — low-level capabilities (gog, browser, telegram). A standing order *uses* skills.
- **Cron jobs** (`openclaw cron add`) — time-triggered. A standing order can be invoked by cron, or by a Brando command, or by an inbound event.
- **The triage agent prompt** (`config/agent-prompt.md`) — the always-on background loop. A standing order is a discrete, named workflow that runs to completion when invoked.

Each standing order lives in its own `standing_orders/<name>.md` and is referenced from [`MASTER_PLAN.md`](../MASTER_PLAN.md) §3 (inventory).

## The shape (every standing order has these sections, in this order)

1. **Title + TLDR** — one-paragraph north star.
2. **Goal** — what friction this collapses.
3. **When this fires** — invocation triggers (Brando command, cron, inbound event). **Never** auto-trigger on incoming high-value channels (email reply, WhatsApp, Discord) unless explicitly approved.
4. **Inputs** — recipient, raw content, optional context. Be explicit about ambiguity-resolution.
5. **Workflow** — numbered steps: Capture → Clean → Show → Approve → Execute → **Notify (Telegram reply in originating chat + email to Brando)** → Log. The Notify step is mandatory per Default Safety Rule 8 below.
6. **Outputs** — what gets sent / posted / created, plus the audit-log row.
7. **Safety rules** — approval level, secret-leak detection, bulk-send threshold, tone-drift callout, never-do list.
8. **Open setup questions** — what needs to be answered before this standing order goes live.
9. **Status** — date, state, blockers.

## Approval vocabulary (canonical — do not drift)

| Token | Meaning |
|---|---|
| `post` | Finalize and execute the draft as shown. |
| `edit: <new text>` | Replace the draft with the provided text and execute. |
| `tweak: <instruction>` | Regenerate the draft with the given instruction (e.g. "shorter", "more formal"). Loop back to the **Show** step. |
| `cancel` | Discard the draft, no execution, log the cancel. |

Aliases (friction-reduction; OpenClaw maps them to canonical tokens):
- `send` / `yes` / `y` → `post`
- `no` / `n` / `scrap` → `cancel`

For bulk operations (>3 recipients, mailing-list blasts, multi-platform social posts), require `confirm-bulk` instead of `post`.

## Audit log convention

Every standing order writes one JSONL row per execution to `~/openclaw/audit/<workflow>.jsonl`:

```json
{
  "ts": "2026-05-08T14:23:01Z",
  "workflow": "<name>",
  "host": "${HOSTNAME}",
  "trigger": "telegram_command | cron | inbound_event",
  "input_summary": "<≤200-char summary, no PII beyond what Brando already exposed>",
  "draft_summary": "<≤200-char summary of the final draft>",
  "approval_token": "post | edit | tweak | cancel | confirm-bulk",
  "executed": true,
  "output": { "channel": "...", "id": "...", "url": "..." },
  "duration_ms": 1234
}
```

Sensitive fields (full draft text, recipient phone, etc.) are NOT in the audit log — the audit log is for "did OpenClaw act?", not "what exactly did it say?". For the latter, look at the channel's own sent log (Gmail Sent, WhatsApp chat history, etc.).

## Default safety rules (every standing order inherits)

1. **No silent execution** — silence ≠ approval. Every consequential action requires an approval token in the current chat turn.
2. **Secret-leak guard** — regex-check drafts for API-key / OAuth-token / password-shape strings. If detected, refuse and ask Brando to confirm in plaintext.
3. **Tone-drift callout** — if cleanup changed *meaning* (not just polish), flag it: *"I rewrote 'X' as 'Y' — confirm?"*
4. **Bulk threshold** — >3 recipients triggers `confirm-bulk` instead of `post`.
5. **Never enter payment info** — no credit card, bank, Venmo/Zelle/PayPal payment forms. Ever.
6. **Never bypass CAPTCHA** — escalate to Brando.
7. **Screenshot before submit on web forms** — DM the screenshot, wait for `post`.
8. **Always notify on completion** (per Brando 2026-05-08) — on a successful Execute, emit **both**:
   - **(a) Telegram reply in the originating chat** with `✅ <one-line summary> — <relevant URL>`.
   - **(b) Email to Brando** with all 3 CCs per [`INDEX_RULES.md`](../../../INDEX_RULES.md) Trigger Rule 26 (`brando.science@gmail.com` + `brando9@stanford.edu` + `brandojazz@gmail.com`); subject `OpenClaw: <workflow> done — <summary>`; body lists what was done + links + audit-log row.
   - **Exception:** if the executed action was itself sending an email *to* Brando, skip (b) (circular). Telegram reply alone is sufficient.
   - **Failure handling:** if either notification path fails, retry once, then post `🚨 [${HOSTNAME}] notify failed: <reason>` to `openclaw-ops`. Don't roll back the executed action.

## Inline template (copy this when writing a new standing order)

```markdown
# Standing Order — <Name>

**TLDR:** <1–2 sentence north star>

## Goal

<What friction this collapses, in 2–3 sentences.>

## When this fires

- <Trigger 1, e.g. Brando says `/x <args>` in Telegram>
- <Trigger 2, e.g. cron `*/30 * * * *`>
- <Trigger 3, e.g. inbound event from Gmail/Discord>

**Never** triggered automatically by <high-value-channel events>.

## Inputs

1. **<Input 1>** — <description, ambiguity-resolution>
2. **<Input 2>** — <description>
3. **Optional <input 3>** — <description>

## Workflow

1. **Capture (Brando):** <how the request enters>
2. **Clean (OpenClaw):** <normalize / parse / classify>
3. **Show (OpenClaw):** <the preview format Brando sees>
4. **Approve (Brando):** `post` / `edit:` / `tweak:` / `cancel`
5. **Execute (OpenClaw):** <skill calls, API calls, browser automation>
6. **Notify (OpenClaw):** Telegram reply in the originating chat (`✅ <summary> — <url>`) AND email to Brando with 3 CCs per Trigger Rule 26 (skip the email if the executed action was itself an email *to* Brando — would be circular).
7. **Log (OpenClaw):** append to `~/openclaw/audit/<workflow>.jsonl`

## Outputs

- <What gets sent / posted / created>
- <Audit log entry>
- No state change if Brando says `cancel`.

## Safety rules

- **Approval level:** `approve_to_send` | `never_autonomous`.
- <Workflow-specific rules — bulk threshold, dedup, recipient allowlist, etc.>

## Open setup questions

1. <Blocker 1>
2. <Blocker 2>

## Status

| Date | Status |
|------|--------|
| YYYY-MM-DD | Spec drafted. Setup questions pending. |
```

## See also

- [`MASTER_PLAN.md`](../MASTER_PLAN.md) — top-level OpenClaw plan (architecture, phases, inventory)
- [`whatsapp_voice_draft.md`](./whatsapp_voice_draft.md) — the canonical example to imitate
- [`stackexchange_proofassistants_post.md`](./stackexchange_proofassistants_post.md) — second canonical example (Playwright-driven external posting)
