# Test Task — Email Alex Aiken's PhD Students re: Verifying Agent-Generated Semantics for VeriVeribench

**TLDR:** Single outreach email from Brando to Alex Aiken's current PhD students (Stanford formal-methods / PL group) asking how to verify the correctness of formal semantics that an agent generates — for the VeriVeribench project. CC's all 3 of Brando's emails per Trigger Rule 26 + Stepan Nesterov (Stanford AI for Lean / `aiforlean.org`) since this is his expertise area. Validates Gmail bulk-send to multiple TO recipients with a non-trivial CC list.

## Channel

Email only (no Discord, no Telegram channel post). Outbound is `gog gmail send`.

## Recipients

- **TO:** Alex Aiken's current PhD students at Stanford. List TBD — populate from Aiken's lab page ([https://theory.stanford.edu/~aiken/](https://theory.stanford.edu/~aiken/) or current Stanford CS faculty page). Likely include current students working on FM / PL / SAT / verification (names redacted here until Brando confirms the list — common names from Aiken's lineage tend to be 4–8 active PhD students at any time).
- **CC:** Stepan Nesterov (Stanford AI for Lean) — email TBD; likely on `aiforlean.org` mailing list or via Stanford CS directory. Brando wrote his handle as "neserov55" then clarified "stepan from the lean ai club".
- **CC (Trigger Rule 26):** all 3 of Brando's email addresses:
  - `brando.science@gmail.com`
  - `brando9@stanford.edu`
  - `brandojazz@gmail.com`

> **Note on bulk-send safety:** if the resolved TO list is > 3 recipients, this triggers `confirm-bulk` per the [`standing_orders/README.md`](../standing_orders/README.md) default safety rules — Brando confirms the full recipient list before send.

## Drafted message

- **Subject:** `verifying agent-generated semantics — quick question for aiken students (re: VeriVeribench)`
- **Body** (lowercase, brando voice, one polite frame so it doesn't read as terse to recipients Brando doesn't know personally):

  > hi all — brando here, sanmi koyejo's group. we're building **VeriVeribench**, a benchmark / project where the agent generates formal semantics (lean 4 types, definitions, specs) for a target program, and we evaluate.
  >
  > the question we keep hitting: **how do we verify the agent's generated semantics are *correct*?** not type-correct in lean's kernel sense — that's just `lake build` — but that the formal artifact actually captures the intended meaning of the underlying program.
  >
  > directions we've considered: round-trip translations (semantics → code → semantics; check fixed point); equivalence proofs vs. a reference implementation; property-based testing of the semantics against a test suite the program already passes; conservativity over a base theory; bisimulation. probably more we haven't seen.
  >
  > you all live closer to this problem than we do. any pointers — papers, tools, techniques, "we tried X and it didn't work" — that you'd send a fresh phd student starting on this? happy to chat sync / read async / collaborate.
  >
  > cc'ing stepan (stanford AI for lean) since this is his sweet spot too.
  >
  > thanks much,
  > — brando
  >
  > —
  > brando miranda · stanford cs · stairlab.stanford.edu/members/brando_miranda.html

## Approval flow

1. Agent renders the email (subject + body + full TO list + full CC list).
2. DMs Brando in Telegram with format:

       📬 [test-aiken-veriveribench] Email — bulk send (N recipients)
       TO: <comma-separated list of Aiken students>
       CC: stepan@<...>, brando.science@gmail.com, brando9@stanford.edu, brandojazz@gmail.com
       Subject: verifying agent-generated semantics — quick question for aiken students (re: VeriVeribench)
       ---
       <body>
       ---
       Reply: confirm-bulk / edit: <new body> / tweak: <instruction> / cancel

3. Approval requires `confirm-bulk` (not just `post`) because TO list is > 3 recipients per the bulk-send safety rule.
4. On `confirm-bulk`: agent sends via `gog gmail send --to "<list>" --cc "<list>" --subject "..." --body "..."`.
5. On `edit: <text>` or `tweak: <instruction>`: regenerate, loop back to step 2 (still requires `confirm-bulk` to ship).
6. On `cancel`: discard, log the cancel.

## Prereqs (must be true before this can run)

- [x] `gog` skill exposed to agent and Ready ✓ (per [`MASTER_PLAN.md`](../MASTER_PLAN.md) Appendix E "Current pickup state" — Gmail row marked ✅ working)
- [x] CC-3 Trigger Rule landed in [`INDEX_RULES.md`](../../../INDEX_RULES.md) Trigger Rule 26 ✓ (committed 2026-05-08)
- [ ] Alex Aiken's current PhD student list resolved (Brando provides, OR Claude looks up from `theory.stanford.edu/~aiken/` if asked)
- [ ] Stepan Nesterov's email resolved (Brando provides; check Stanford CS directory or `aiforlean.org` member list)
- [ ] VeriVeribench project name confirmed — is it "VeriBench" (existing benchmark) or "VeriVeribench" (typo or distinct project)?

## Open questions

1. **Recipient list for Aiken students** — how does Brando want to source it? Options: (a) Brando pastes the names + emails; (b) Claude scrapes Aiken's lab page; (c) Brando uses a Stanford CS directory query.
2. **Stepan Nesterov full identity + email?** — Stepan from the Lean AI Club; Brando referenced "neserov55" handle then corrected to "stepan". Confirm full name spelling (Nesterov / Neserov) + canonical email.
3. **Project name confirmation** — Brando wrote "VeriVeribench". Is that the canonical name, or shorthand for VeriBench?
4. **Tone calibration** — is the draft above the right register for Aiken's students? More academic? Reference 1–2 specific papers? Mention specific results from VeriBench so they have context?
5. **Subject line specificity** — should it name VeriVeribench in the subject (more concrete, may flag Spam filters) or just describe the question (more discoverable)?
6. **Anyone else to CC?** — Sanmi Koyejo (advisor)? Other members of Brando's lab who are co-authors? Co-PI on VeriVeribench?

## What this test validates

- Bulk-send approval flow with `confirm-bulk` token (first real test of the >3-recipient threshold)
- Multi-CC composition: Trigger Rule 26 (3 brando addrs) + named external CC (Stepan) all in one email
- `gog gmail send --to "list" --cc "list"` syntax with non-trivial recipient lists
- Tone calibration on a colleague-grade outreach to people Brando may not know personally (different from the Saumya email which is to a known close colleague)
- Evidence the audit log captures bulk sends correctly (who got it, when, message ID)

## Adjacent value (research direction, not task scope)

The question itself ("how to verify agent-generated semantics") is a real research problem and the answers will feed VeriVeribench's design directly. Worth: when responses come back, capture them in a notes file (e.g., `~/agents-config/research/veriveribench/correctness_of_agent_semantics_notes.md`) — even one good pointer changes the evaluation design. Out of scope for this email task itself; flag as follow-up if useful answers arrive.

## Status

| Date       | Status                                                                                                                                                                                          |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-05-08 | Drafted. Blocked on: Aiken student list (Brando provides or Claude scrapes lab page on Brando's word), Stepan's email, VeriVeribench name confirmation. CC-3 Trigger Rule already in place ✓. |
