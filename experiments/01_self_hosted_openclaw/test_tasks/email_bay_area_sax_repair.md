# Test Task — Email Bay Area Saxophone Repair Shops re: Repad / Overhaul Quote

**TLDR:** Personalized outreach emails to 4–6 Bay Area saxophone repair shops asking for a repad / overhaul quote on Brando's ~10-year-old saxophone (currently squeaking, pads almost certainly worn). Each shop gets its own email (not bulk-CC'd — they don't want to see each other's contact info). CC `brando.science@gmail.com` for auditability per Trigger Rule 26. Validates the multi-recipient send pattern when each recipient gets a separate email rather than a single bulk send.

## Channel

Email only — N parallel sends, one per shop. Outbound is `gog gmail send` per recipient.

## Recipients (Bay Area sax repair candidates — Brando picks which to email)

Sourced from saxontheweb.net forum threads + shop pages, verified 2026-05-08:

| Shop                          | Location          | Contact (TBD — verify on shop site) | Notes                                                             |
| ----------------------------- | ----------------- | ----------------------------------- | ----------------------------------------------------------------- |
| **Saxology / saxcraft.com**   | Berkeley          | https://www.saxcraft.com/           | Eric Drake + Jey Clark; full overhauls, reasonable prices         |
| **Best Instrument Repair**    | Oakland (564 14th St) | TBD                            | Full overhauls + dent work, reasonable turnaround                 |
| **Lee's Sax Worx**            | San Francisco     | TBD                                 | Pro overhauls; quotes start ~$2000/horn (premium)                 |
| **Anthony's Woodwind Corner** | San Rafael        | TBD                                 | Owner reviews horn while you wait; good rep, reasonable pricing    |
| **Lamorinda Music**           | Lamorinda area    | https://www.lamorindamusic.com/repairs | Tune-ups through complete overhauls                            |
| **Steve Deutsch Music**       | Benicia           | https://stevedeutschmusic.com/saxophone-repair/ | Woodwind specialist                                |

Brando picks 3–5 to email (probably skip the most premium / most distant unless spec'd in). Shops differ enough in pricing and approach that individual emails get better quotes than a bulk blast.

**CC on every send (Trigger Rule 26):** `brando.science@gmail.com`; add other Brando aliases only if explicitly requested.

## Drafted message (template — agent personalizes per shop)

- **Subject:** `quote request — saxophone overhaul / repad on 10yr-old <SAX_BRAND/MODEL>`
- **Body:**

  > hi <shop name>,
  >
  > looking to get a quote on a saxophone overhaul / repad. some details:
  >
  > - **horn:** <SAX_BRAND_MODEL — TBD>
  > - **age:** ~10 years from new
  > - **symptoms:** squeaking on multiple notes (pads almost certainly need replacing); not formally diagnosed beyond that. probably also needs cork / felt / spring check after this long.
  > - **use:** moderate (not pro-tier daily); want it back to feeling tight
  > - **timeline:** flexible
  > - **location:** stanford / palo alto; can drop off / ship as needed
  >
  > could you give me a ballpark on:
  >
  > 1. cost for a full repad (and what else you'd typically include — corks, felts, regulation, key fitting?)
  > 2. expected turnaround
  > 3. any "while it's open, definitely also do X" recommendations for a horn this age
  >
  > happy to bring it by for a look-see if that's faster than email back-and-forth.
  >
  > thanks!
  > — brando miranda
  > (stanford cs phd; sax for fun, not for income — so trying to balance "do it right" with "don't redo every consumable")

## Approval flow

1. Agent renders **N drafts**, one per selected shop, each with the shop's name + relevant address line filled in.
2. DMs Brando in Telegram with format:

       📬 [test-bay-area-sax-repair] N personalized emails (1 per shop)
       Recipients:
         - Saxology <saxcraft@... TBD>
         - Best Instrument Repair <... TBD>
         - Lee's Sax Worx <... TBD>
         - <etc.>
       CC (every email): brando.science@gmail.com
       Subject template: quote request — saxophone overhaul / repad on 10yr-old <SAX_MODEL>
       Body preview: <first ~200 chars>
       ---
       Reply: confirm-bulk (sends N) / edit-shop <name>: <new body> / tweak: <instr> / cancel-shop <name> / cancel-all

3. **`confirm-bulk` token required** because N > 3 recipients (per [`standing_orders/README.md`](../standing_orders/README.md) safety rules). Brando confirms once, agent sends all N in sequence (1 per minute to avoid rate-limit / Spam triggers).
4. Per-recipient overrides: `edit-shop <name>: <new body>` rewrites just that one; `cancel-shop <name>` drops just that one; `cancel-all` drops everything.
5. Each successful send writes its own audit row to `~/openclaw/audit/test_tasks.jsonl` with shop, message-id, timestamp.

## Prereqs (must be true before this can run)

- [x] `gog` skill exposed to agent and Ready ✓ (per [`MASTER_PLAN.md`](../MASTER_PLAN.md) Appendix E "Current pickup state" — Gmail row marked ✅ working)
- [x] Brando email routing rule landed in [`INDEX_RULES.md`](../../../INDEX_RULES.md) Trigger Rule 26
- [ ] Brando's saxophone brand + model (e.g. "Yamaha YAS-62 alto", "Selmer Mark VI tenor") — populates the SAX_BRAND_MODEL placeholder in subject + body
- [ ] Brando picks which 3–5 shops to email (default: Saxology + Best Instrument Repair + Anthony's Woodwind — geographically closer, mid-tier pricing band)
- [ ] Verified email addresses for each picked shop — agent does the contact-page scrape if shop site has a contact form / email listed; otherwise prompt Brando

## Open questions

1. **Sax brand / model / type?** (alto / tenor / soprano / bari changes the cost a lot — alto/tenor repad typically $400–$800 mid-tier, $1500+ premium; soprano cheaper, bari pricier)
2. **Which 3–5 shops to email?** Default 3: Saxology (Berkeley) + Best Instrument Repair (Oakland) + Anthony's Woodwind (San Rafael).
3. **Budget ceiling?** "Don't bother with quotes >$X" — useful for filtering Lee's Sax Worx (~$2000+) if Brando doesn't want premium.
4. **Drop-off vs ship?** Affects turnaround; some shops do mail-in.
5. **Phone fallback?** Sax shops often respond faster to phone than email. Should the agent also generate a "call script" Brando can use if he wants to phone instead? (Cheap to add; OOS if email-only is fine.)

## What this test validates

- **Personalized N-message send** (vs. true bulk-CC) — every recipient gets a tailored email; agent fills shop name + address into a template
- **Per-recipient `edit-shop <name>`** override semantics in the approval flow — first real test of the more granular bulk control
- **`confirm-bulk` threshold** at >3 recipients (different from the Aiken email which is also >3 but bulk-CC'd; this is N parallel sends)
- **Web-search-derived recipient list** — first task where Claude populates real candidates from web search and Brando picks among them (vs. Brando providing the full list himself)

## Adjacent

If any shop replies, drop their reply into Brando's inbox per the email-triage standing order; Brando approves a follow-up email if he picks one to use. Could become a recurring "quote-shopping" standing order if Brando does this often (cars, dentists, contractors, etc.) — promote to `standing_orders/quote_shopping.md` if pattern recurs.

## Status

| Date       | Status                                                                                                                                                                                                  |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-05-08 | Drafted. 6 candidate shops identified via web search + saxontheweb.net forum recs. Blocked on: Brando's sax brand/model, his shortlist of 3–5 shops, verified email addresses for picked shops. Pads / overhaul context is stable (the symptoms — squeaking after 10 years — almost always means worn pads, sometimes also corks/felts/springs at this age). |
