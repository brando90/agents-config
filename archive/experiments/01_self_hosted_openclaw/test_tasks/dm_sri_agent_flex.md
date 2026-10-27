# Test Task — DM Sri on Discord ("this is my agent ;)")

**TLDR:** First playful Discord DM from the OpenClaw agent to Sri — show that the agent is real and running, deliver Brando's voice with a wink emoji, and ask whatever Brando wanted to ask Sri about Mac minis. Validates the Discord channel end-to-end (bot intent + DM permissions + tone calibration on a low-stakes recipient).

## Channel

Discord DM (one-to-one, not a server channel).

## Recipient

- **Name:** Sri (handle TBD by Brando)
- **Discord:** `@<TBD>` — Brando provides
- **Constraint:** Brando's bot must be in a server Sri is also in (Discord lets bots DM users only if they share a server and the user hasn't disabled "DMs from server members").

## Drafted messages (pick one or paste a custom)

**Option A — deadpan-cool:**

> sri ;) this is brando's agent. yes really. openclaw on his macbook, routing via telegram → discord. <macbook minis question>. tell me i pulled it off.

**Option B — warm-show-offy:**

> sri!! ;) brando here — except not really, this is his ai agent dm'ing you. wild, i know. anyway: <macbook minis question>. he's flexing, you're the first person to see this work end to end.

**Option C — drier reveal:**

> hey sri ;) heads up — this is brando's agent (no human typing) running on his laptop via openclaw. testing the discord bridge so figured i'd say hi to you first. while i'm here: <macbook minis question>. cool, right? 😉  — brando (via agent)

## Approval flow

1. Agent renders the chosen draft.
2. DMs Brando in Telegram with format:

       💬 [test-sri-discord] Discord DM to @<sri-handle>
       <draft>
       ---
       Reply: post / edit: <new text> / tweak: <instruction> / cancel

3. On `post`: agent sends the DM. Logs to `~/openclaw/audit/test_tasks.jsonl`.
4. On `tweak: <instr>`: regenerate, loop back to step 2.
5. On `edit: <text>`: send Brando's text verbatim.
6. On `cancel`: discard.

## Prereqs (must be true before this can run)

- [x] Discord transport connected in OpenClaw (`@ultimate_brando9_bot` verified on Mac + mercury2, 2026-06-04)
- [ ] If inbound ordinary message reads fail: Discord Message Content Intent ON in dev portal Bot tab
- [ ] Bot invited to a Discord server where Sri is also a member
- [ ] Bot has permission to DM users in that server
- [ ] Sri's Discord handle captured in Brando's contacts (when contacts roster lands)

## Open questions

1. **Sri's Discord handle?** (`@username` or full name; Brando provides)
2. **Macbook minis topic?** [`MASTER_PLAN.md`](../MASTER_PLAN.md) §2 / Appendix A reference "Mac mini at home" as a candidate OpenClaw host. Is this about (a) Sri ordering/recommending them for the lab, (b) Brando considering one as a 4th OpenClaw box, (c) something Sri asked earlier and Brando owes him an answer, (d) other?
3. **Tone choice?** A deadpan-cool / B warm-show-offy / C drier reveal / paste a custom voice example.

## What this test validates

- Discord channel works end-to-end (bot can DM a real human user)
- Agent's tone calibration on a low-stakes recipient (if Sri reads it as Brando-voice → tone is dialed; if not → we have a real signal to tighten `agent-prompt.md` before the agent replies to admin email)
- The full Telegram-approval → cross-channel-execute loop (preview in Telegram, execute in Discord)
- First validation of the canonical `post / edit: / tweak: / cancel` vocabulary on a real send

## Status

| Date       | Status                                                                                  |
| ---------- | --------------------------------------------------------------------------------------- |
| 2026-05-08 | Drafted. Blocked on: Discord intent toggle (Brando, 90s) + Sri's handle + macbook minis topic context + tone choice. |
| 2026-06-04 | Discord transport connected on Mac + mercury2. Still needs Sri target identity/shared-server DM permissions, topic context, and tone choice before sending. |
