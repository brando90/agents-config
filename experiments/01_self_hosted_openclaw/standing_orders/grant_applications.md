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
4. **Draft** application material from Brando's identity sources (per [`MASTER_PLAN.md`](../MASTER_PLAN.md) §4.3 hybrid identity-source design):
   - **Bio** — fetch `_data/bio.yml` from [`brando90/brandomiranda`](https://github.com/brando90/brandomiranda) website repo via raw GitHub URL; pick the variant matching the requested word count (50 / 100 / 250 / 500) or the elevator pitch.
   - **Active projects** — call GitHub API `api.github.com/users/brando90/repos?sort=pushed&per_page=15` to get the freshest project list; for each project that aligns with the funder's interests, pull the narrative from that repo's `README.md` (raw GitHub URL), or from `_data/projects.yml` override in the website repo if the README is a stub.
   - **Reusable paragraphs** (diversity / impact / research statement core) — fetch from `_data/grant_paragraphs.yml` in the website repo.
   - **Compose** — generate research statement / personal statement by stitching the matched bio + project narratives + reusable paragraphs.
5. **Fill safe form fields** (Playwright):
   - Always-safe: name, email, affiliation, ORCID, links — pulled from `_data/bio.yml` (public) and `~/keys/brando_personal_facts.json` (sensitive subset).
   - Pre-confirmed drop-downs (citizenship, PhD year, etc.) from `~/keys/brando_personal_facts.json` (mode 600, never committed).
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

> **Identity-source design (2026-05-08):** the original plan stored bio + project narratives as flat files in this repo. That goes stale because Brando would have to update his real CV (his website) AND these files for every change. Pivoted to a hybrid where Brando's website + GitHub `pushed_at` is the source of truth; this repo only holds the workflow + sensitive data lives in `~/keys/`. Full rationale in [`MASTER_PLAN.md`](../MASTER_PLAN.md) §4.3.

1. **Website-repo data files (Brando's side, one-time setup):**
   - [ ] Add `_data/bio.yml` to [`brando90/brandomiranda`](https://github.com/brando90/brandomiranda) with 4 length variants (50 / 100 / 250 / 500 words) + 1 elevator pitch.
   - [ ] Add `_data/grant_paragraphs.yml` with 3–5 reusable paragraphs (diversity statement, broader impact, research-statement core).
   - [ ] Audit top 15 most-recently-pushed repos: any with a stub README that wouldn't survive a grant reviewer gets either a paragraph-length README *or* an override entry in `_data/projects.yml`.
2. **Sensitive personal facts** — `~/keys/brando_personal_facts.json` (mode 600, never committed) populated with: legal name, ORCID, citizenship, current affiliation, home + mailing address, letter-writer roster (name + email + relationship).
3. **Letter-of-recommendation template** — `~/agents-config/email-signature.md`-style template for "asking a recommender" emails. Brando confirms the template language; agent uses it for LoR-request drafts (still subject to `post` approval before any send).
4. **Known-grants seed** — `experiments/01_self_hosted_openclaw/config/known_grants.txt` with 5–10 programs Brando is currently watching (NSF GRFP, Hertz, NSF CAREER-eligible, Stanford internal, conference-specific).
5. **Bootstrap from past success** — Brando provides 1 successful past application (e.g. GRFP) so OpenClaw can extract the 4-length bios + reusable paragraphs from real proven text rather than a blank page.
6. **Playwright skill state** — does OpenClaw ship a browser-automation skill, or do we need to add one? Same blocker as Stack Exchange posting (see [`stackexchange_proofassistants_post.md`](./stackexchange_proofassistants_post.md)).

## Status

| Date | Status |
|------|--------|
| 2026-05-08 | Skeleton drafted. Setup questions pending. Implementation deferred until Phase 6.3 of [`MASTER_PLAN.md`](../MASTER_PLAN.md). |
| 2026-05-08 | Identity-source design pivot: bio / projects / paragraphs no longer live as flat files in this repo. Hybrid: website (`_data/*.yml`) + GitHub API (`pushed_at` for active projects) + `~/keys/` (sensitive). See [`MASTER_PLAN.md`](../MASTER_PLAN.md) §4.3 for full rationale. Removes the "this will go stale" failure mode. |
