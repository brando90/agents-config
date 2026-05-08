# Standing Order — Grant Applications

**TLDR:** OpenClaw watches Brando's inbox + Discord for grant CFPs (NSF GRFP, Hertz, conference fellowships, etc.), extracts the requirements, drafts the application from a reusable bio + project library, fills the safe form fields via Playwright, screenshots, and DMs Brando the final preview. **Brando clicks the actual submit button himself in his own browser session — OpenClaw never submits a grant.**

## Goal

Collapse "I have ten grants I could apply to but each one takes a full afternoon of bureaucracy" into "OpenClaw drafted 10 applications this week — review and submit." The bottleneck shifts from *typing* to *Brando deciding which to submit*, which is the right shape.

## When this fires

- **Inbound (Gmail)** — triage agent flags a message as a grant CFP. Heuristic: keywords ("deadline", "eligibility", "stipend", "fellowship", "applications open"); sender domain in `config/known_grants.txt`.
- **Inbound (Discord)** — Lean-AI / personal-server posts containing the same heuristic.
- **Brando-initiated (Telegram)** — `/grant <url-or-paste>` — Brando passes a CFP URL or pastes the body, OpenClaw extracts.

**Never** triggered without an explicit detected/passed CFP.

## Inputs

1. **CFP source** — Gmail message, Discord post, or pasted URL/text.
2. **Grant identity** — name (e.g. "NSF GRFP 2027"), funder, deadline, eligibility constraints.
3. **Required materials** — research statement, personal statement, transcripts, letters of recommendation, budget, etc.
4. **Form-fill scope** — which web form fields OpenClaw is allowed to fill (always: name/email/affiliation/ORCID; never: payment, signature, free-form essays without prior approval).

## Workflow

1. **Capture**: CFP arrives or is pasted.
2. **Classify**: is this actually a grant Brando is eligible for? (PhD-level, US-residency, formal-verification-relevant, etc.) If not eligible, DM "found grant X — eligibility: <reason ineligible> — proceed anyway?"
3. **Extract** (structured JSON):
   - Funder + program name
   - Deadline (with timezone)
   - Eligibility checklist
   - Required materials (file types, page limits, word counts)
   - Letters of recommendation (count, deadline)
   - Submission portal URL
   - Estimated effort (low / med / high) based on materials count
4. **Draft** application material from `config/brando_bio.md` + `config/brando_projects.md`:
   - Match length: pick the bio at the appropriate word count (50 / 100 / 250 / 500).
   - Match focus: select project paragraphs that align with the funder's interests.
   - Generate research statement (if requested) by combining project paragraphs + a stitching narrative.
   - Generate personal statement (if requested) from bio + diversity/impact paragraphs.
5. **Fill safe form fields** (Playwright):
   - Always-safe: name, email, affiliation, ORCID, links.
   - Pre-confirmed drop-downs (citizenship, PhD year, etc.) from `config/brando_personal_facts.json`.
   - **Skip**: payment info, signature fields, free-form essays Brando hasn't pre-approved.
6. **Screenshot before submit** — full-page screenshot of the filled form, DM'd to Brando along with: extracted requirements summary + draft materials + checklist.
7. **Approve (Brando)**: `post` marks the draft as ready (does NOT submit); `edit:` / `tweak:` to revise; `cancel` to discard.
8. **Brando submits manually** — opens the URL in his own browser, reviews fields, clicks submit. **OpenClaw never clicks submit on a grant portal.**
9. **Log**: append to `~/openclaw/audit/grants_drafted.jsonl` and `~/openclaw/audit/grants_filled.jsonl`.

## Outputs

- Draft application materials saved to `~/openclaw/grants/<funder>_<program>_<year>/draft/`.
- Filled-form screenshot at `~/openclaw/grants/<funder>_<program>_<year>/screenshot.png`.
- Audit log entries.
- **No actual submit** — that's Brando's job.

## Safety rules

- **Approval level:** `never_autonomous` for any clicking on a grant portal beyond field-fill. **Save-as-draft is fine; submit is not.**
- **Never enter payment info.**
- **Never sign anything.**
- **Letter-of-recommendation requests** — if a grant requires LoRs, OpenClaw drafts the *recommender request email* (using `config/brando_lor_template.md`) but never sends it without separate `post` approval. Don't auto-poke Brando's letter-writers.
- **Page-limit / word-limit guard** — refuse any draft that exceeds the limit; resize first.
- **Eligibility false-positive guard** — if Brando is clearly ineligible (wrong country, wrong career stage), refuse with a one-line explanation rather than burning a draft cycle.

## Open setup questions

1. **Bio library bootstrap** — Brando provides 1 successful past application (e.g. GRFP) so OpenClaw extracts bio paragraphs at 50 / 100 / 250 / 500 words and project summaries.
2. **Project library bootstrap** — VeriBench, Moogle.ai, Stanford AI for Lean, formal verification — 1–3 paragraphs each, in `config/brando_projects.md`.
3. **Personal-facts file** — `config/brando_personal_facts.json` (mode 600 if it contains anything sensitive; encrypt the truly-sensitive subset via `~/keys/`).
4. **Letter-writers list** — names + emails + relationship; `config/brando_lor_template.md` (or sibling file).
5. **Known-grants seed** — `config/known_grants.txt` with 5–10 programs Brando is currently watching (NSF GRFP, Hertz, NSF CAREER-eligible, Stanford internal, conference-specific).
6. **Playwright skill state** — does OpenClaw ship a browser-automation skill, or do we need to add one? Same blocker as Stack Exchange posting (see [`stackexchange_proofassistants_post.md`](./stackexchange_proofassistants_post.md)).

## Status

| Date | Status |
|------|--------|
| 2026-05-08 | Skeleton drafted. Setup questions pending. Implementation deferred until Phase 6.3 of [`MASTER_PLAN.md`](../MASTER_PLAN.md). |
