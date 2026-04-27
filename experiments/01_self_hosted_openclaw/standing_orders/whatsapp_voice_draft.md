# Standing Order — WhatsApp Voice-Dictation Draft & Approve

**TLDR:** Brando dictates by voice (messy speech-to-text is fine). OpenClaw cleans the transcript into a polished WhatsApp message, shows the draft, and only sends after Brando explicitly approves. Never auto-replies to incoming WhatsApp messages.

## Goal

Send WhatsApp messages (replies or proactive) at the speed of voice with the polish of typed text — without OpenClaw ever sending anything Brando didn't see and approve.

## When this fires

- Brando says (typed or dictated) in OpenClaw: *"Draft a WhatsApp to `<contact>`: `<messy transcript>`"*
- Or pastes raw dictation output and asks for cleanup + send
- Or replies in OpenClaw to an OpenClaw notification about an incoming WhatsApp message ("draft a reply that says…")

**Never** triggered automatically by an incoming WhatsApp message. Auto-reply on WhatsApp = `never_autonomous`.

## Inputs

1. **Recipient** — contact name or phone number. Resolve via OpenClaw's WhatsApp contact list. If ambiguous, ask Brando.
2. **Raw content** — speech-to-text transcript (filler words, transcription errors, missing punctuation expected) OR typed shorthand.
3. **Optional context** — what Brando is replying to, tone (casual / professional / formal), urgency.

## Workflow

1. **Capture (Brando)** — voice input via:
   - macOS system dictation (Fn-Fn → speak → Fn-Fn) directly into OpenClaw's chat input. *Easiest, no extra setup.*
   - MacWhisper / Whisper.cpp app → copy → paste into OpenClaw. *Higher quality, more setup.*
   - OpenClaw's built-in voice button if available (verify in app).
2. **Clean (OpenClaw)** — produce a polished WhatsApp message:
   - Remove filler ("um", "uh", "like").
   - Fix obvious transcription errors using context.
   - Restore punctuation and capitalization.
   - Match Brando's voice (default = casual + concise + warm; refine once `templates/personal_voice.md` exists).
   - Keep length ≤ 2 short paragraphs unless the transcript clearly demands more.
3. **Show (OpenClaw)** — display:
   - Recipient name + phone (last 4 digits visible).
   - Final draft, exactly as it will be sent.
   - Original transcript collapsed for reference.
4. **Approve (Brando)** — one of:
   - `send` / `yes` / `y` → send as-is.
   - `edit: <new text>` → replace and send.
   - `tweak: <instruction>` → e.g. "shorter", "more formal", "add 'see you Friday'" — OpenClaw produces a new draft, loop back to step 3.
   - `scrap` / `no` / `n` → discard, no send.
5. **Send (OpenClaw)** — call WhatsApp connector (Baileys session paired via QR — see `cc_prompt.md` Phase 3). Confirm delivery in chat.
6. **Log (OpenClaw)** — append to `~/openclaw/audit/whatsapp_sends.jsonl`:
   - timestamp, recipient (phone last 4 only), final draft text, approval token (`send` / `edit` / `tweak`), whether voice or typed.

## Outputs

- A sent WhatsApp message that reads like Brando typed it carefully.
- An audit log entry.
- No state change if Brando says `scrap`.

## Safety rules

- **Approval level:** `approve_to_send` (default for WhatsApp).
- **Never** send without an explicit approval token in the current chat turn — silence ≠ approval.
- **Never** send a message containing strings that look like secrets (regex check for API keys, OAuth tokens, password-shaped strings). If detected, refuse and ask Brando to confirm in plaintext that the secret is intentional.
- **Never** send to a recipient Brando hasn't messaged before *unless* Brando explicitly typed the phone number in this turn.
- **Bulk send:** if a draft is destined for >3 recipients, treat as a mailing-list operation — require a separate `confirm-bulk` token, not just `send`.
- **Tone-drift callout:** if cleanup changed meaning materially (not just polish), flag it: "I rewrote 'X' as 'Y' — confirm?"

## Open setup questions

These need answers before this standing order goes live:

1. **WhatsApp connector status** — is Baileys paired on local OpenClaw? (Phase 3 of `cc_prompt.md`.) Multi-device limit is 4: phone + Mac WhatsApp + how many OpenClaws can we afford?
2. **Voice capture preference** — does Brando want macOS dictation, MacWhisper, or OpenClaw's built-in voice button (if any)?
3. **Voice template** — sample 5–10 of Brando's existing WhatsApp messages to extract voice/tone for the cleanup prompt. Until then, default to casual-warm.
4. **Audit log location** — `~/openclaw/audit/` ok, or somewhere DFS-backed?

## Status

| Date | Status |
|------|--------|
| 2026-04-26 | Spec drafted. Setup questions pending. Implementation deferred until email-triage MVP (Phases 0–5 of `cc_prompt.md`) is stable. |
