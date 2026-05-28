# Test Task — Email Saumya re: NeurIPS Reciprocal Reviewer

**TLDR:** Single email to Saumya asking her to email NeurIPS PCs to register Brando as the reciprocal reviewer for `<paper / submission TBD>`. CCs `brando.science@gmail.com` for auditability per the current routing rule. Validates Gmail send behavior + tone calibration on a colleague-grade email.

## Channel

Email only (no Discord, no Telegram channel post). The agent's outbound is `gog gmail send`.

## Recipient

- **To:** Saumya `<full email TBD by Brando>`
- **CC:** `brando.science@gmail.com`, per [`INDEX_RULES.md`](../../../INDEX_RULES.md) Trigger Rule 26. Add `brando9@stanford.edu` or `brandojazz@gmail.com` only if Brando explicitly asks.

## Drafted message

- **Subject:** `neurips reciprocal reviewer — quick ask`
- **Body** (lowercase, brando voice, direct):

  > hey saumya, quick favor — can you ping the neurips PCs to add me as the reciprocal reviewer for `<paper id / our submission>`? happy to draft the language you send if useful. thanks!

## Approval flow

1. Agent renders the email (subject + body + recipients).
2. DMs Brando in Telegram:

       📬 [test-saumya-neurips] Email to saumya <email>, cc: <3 brando addrs>
       Subject: neurips reciprocal reviewer — quick ask
       ---
       <body>
       ---
       Reply: post / edit: <new body> / tweak: <instruction> / cancel

3. On `post`: agent sends via `gog gmail send --to <saumya-email> --cc <3 brando addrs> --subject "..." --body "..."`.
4. On `edit: <new body>`: replace body, send.
5. On `tweak: <instr>`: regenerate (e.g. *"more formal"*, *"add specific paper ID"*), loop back.
6. On `cancel`: discard.

## Prereqs (must be true before this can run)

- [x] `gog` skill exposed to agent and Ready ✓ (per [`MASTER_PLAN.md`](../MASTER_PLAN.md) Appendix E "Current pickup state" — Gmail row marked ✅ working — already working on the Air)
- [ ] Saumya's full email captured (Brando provides, ideally added to a contacts roster file)
- [ ] Paper ID / submission identifier confirmed (which paper is this for?)
- [x] Brando routing rule landed in [`INDEX_RULES.md`](../../../INDEX_RULES.md) (so the agent knows the CC behavior is canonical, not just for this task)

## Open questions

1. **Saumya's full email?**
2. **Which paper / submission ID?** (NeurIPS uses OpenReview paper IDs; if the conference is mid-cycle, the ID is `NeurIPS-2026-<n>` or similar)
3. **Should the agent also draft the language Saumya sends to NeurIPS?** Brando says *"happy to draft if useful"* — option to also produce a 2nd draft (the message Saumya forwards to PCs) for her convenience.

## What this test validates

- `gog gmail send` end-to-end with CC field populated
- The Brando routing rule (Trigger Rule 26) is followed in practice — verify `brando.science@gmail.com` appears in CC and personal email does not unless explicitly requested
- Tone calibration on a colleague-grade email (more formal than the Sri DM, less formal than admin reply)
- Single-channel send approval flow (vs. multi-channel like the workhackathon nudge)

## Status

| Date       | Status                                                                                                  |
| ---------- | ------------------------------------------------------------------------------------------------------- |
| 2026-05-08 | Drafted. Blocked on Saumya's email + paper ID. Brando routing rule now lives in INDEX_RULES.md.        |
