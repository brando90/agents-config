# Standing Order — Travel Search (flight watch + price drops)

**TLDR:** Brando dictates trip intent (origin, destination(s), dates, flexibility, ceiling); OpenClaw watches Google Flights / Kayak / Skyscanner / Southwest daily, ranks the best 3–5 options, DMs Brando in Telegram when a fare crosses his ceiling or a meaningfully better option appears. **OpenClaw never books.** Brando books in his own browser session.

## Goal

Eliminate "I should buy that ticket but I keep forgetting / waiting" indecision. Set the watcher once, get pinged when a real deal exists. Specifically used for:

- Conference / workshop travel (NeurIPS, ICML, ICLR, etc.)
- Personal trips (Rio Grande Valley visits, family events)
- Stanford reimbursement-eligible trips (where the budget is fixed and "best deal" actually matters)

## When this fires

- **Brando-initiated (Telegram):** `/trip <origin> <dest> <date-window> <duration> [ceiling]`. Free-form is also fine: *"find me flights to McAllen mid-June, 8 days, sat to sat, under $400"*.
- **Cron (per active trip-watch):** once daily at 8am PT, OpenClaw re-queries each watched trip and DMs only if a meaningful price/option change occurred (≥ $30 improvement OR new top-3 option appearing).
- **Cancellation:** `/trip cancel <id>` or `/trip stop <id>` or *"stop watching the McAllen trip"*.
- **Status:** `/trip list` shows all active watches with last-seen-best price.

## Inputs

1. **Origin** — default SFO; alternates SJC, OAK (Brando confirms or overrides per trip).
2. **Destination(s)** — single airport code or list (e.g. `["MFE", "HRL"]` to compare McAllen vs. Harlingen).
3. **Date window** — `start_earliest`, `start_latest`, `duration_days`, `return_window_days`. Lets agent search a window, not a single date.
4. **Ceiling** — USD; if no option below ceiling exists, suppress DMs (don't spam with "still nothing").
5. **Airline preferences** — Southwest yes/no (matters because it doesn't aggregate cleanly), no-red-eye, max stops, alliance preference.
6. **Baggage** — carry-on only (cheapest fare class) or checked (mid fare class).

## Workflow

1. **Capture** — store intent in `~/.openclaw/trips/<id>.json` (id = autoincrement or slug like `mcallen-jun-2026`).
2. **Daily query (cron)** — for each destination × eligible date in the window:
   - Google Flights via Playwright (no public API)
   - Kayak via scraper or unofficial API
   - Southwest separately if enabled (their fares don't show in aggregators; needs a second Playwright session against `southwest.com`)
   - Skyscanner if Brando wants international coverage
3. **Rank** — total cost first, then stops, then depart/arrive convenience. Cache last-seen-best per (trip-id, date-bucket).
4. **Show** — only DM if (a) new best ≤ ceiling AND ≥ $30 better than yesterday's cached best, OR (b) a new option entered the top 3:

       ✈️ [trip-mcallen-jun] new best: $342 SFO→MFE
       Sat Jun 13  6:55am SFO → IAH → MFE 1:18pm   (1 stop, 8h23m, Southwest)
       Sun Jun 21  2:14pm MFE → DFW → SFO 8:40pm   (1 stop, 8h26m, Southwest)
       carry-on free. -$40 vs yesterday.
       Alts: option B $358 (United, nonstop SFO→IAH then connect), option C $371 (Spirit, basic econ).
       Reply: post (book yourself) / tweak: <instruction> / cancel

5. **Approve (Brando)** — canonical vocab: `post` / `edit:` / `tweak:` / `cancel`.
6. **Execute** —
   - `post`: OpenClaw does NOT book. Brando books in his own browser. OpenClaw logs the booking link he used (if pasted back) + final price to `~/openclaw/audit/travel_search.jsonl` for traceability.
   - `tweak: <instruction>`: regenerate (e.g. *"only nonstop"*, *"widen to mid-June + 1 week"*, *"avoid IAH"*); loop back to Show.
   - `cancel`: discard, log the cancel.
7. **Log** — JSONL row per dispatch (cost, route, action) per the standing-orders README convention.

## Outputs

- DM with top-3 ranked options + delta vs yesterday + airline + key constraints (red-eye, # of stops, carry-on policy).
- Audit row per dispatch.
- `~/.openclaw/trips/<id>.json` updated with `last_seen_best`, `last_dm_at`.

## Safety rules

- **Approval level:** `never_autonomous` for booking — OpenClaw NEVER clicks "purchase" on a flight site. Ever.
- **Never stores payment info.** No card numbers, no PayPal, no saved-traveler-profile credentials beyond what Brando keeps in his own browser.
- **DM frequency cap:** 1 per trip-watch per day max. Don't spam on tiny price jitters — only DM on ≥ $30 improvement OR new option entering top 3.
- **Stale-trip nudge:** if a trip-watch has been silent for 14 days (no movement, no new options), DM *"trip <id> still watching, no movement, want to extend / cancel?"*. Saves the watcher from running indefinitely on a forgotten trip.
- **Reimbursement-flag awareness:** if Brando tags a trip as `--reimbursed`, prefer airlines / fare classes Stanford reimburses (no basic-economy if checked bags expected; flag this in the DM).
- **CAPTCHA / bot-detection:** Google Flights and especially Southwest fight headless browsers. If Playwright trips a CAPTCHA, log it, skip that source for the day, escalate to Brando if it's the only source for a trip.

## Open setup questions

1. **Home airport priority** — SFO > SJC > OAK, or any specific weight (e.g. avoid OAK for international)?
2. **Default ceiling per trip** — flat $400, or always per-trip explicit?
3. **Southwest scrape** — okay to run a second Playwright session against `southwest.com` (they don't show in Google Flights / Kayak)? Worth the extra fragility — they often have the cheapest SFO ↔ RGV fares.
4. **Skyscanner** — needed for international, skip for domestic? International defaults like passport/visa/TSA-precheck preferences stored where?
5. **Reimbursement-aware mode** — does Brando want a `--reimbursed` flag that biases toward Stanford-policy-compatible fare classes?
6. **Calendar integration** — auto-block the date range in Google Calendar (via `gog`) once Brando confirms `post`? Tentative-block on watching, hard-block on booked?

## First test case (concrete)

McAllen / Harlingen summer 2026 — see [`MASTER_PLAN.md`](../MASTER_PLAN.md) Appendix F.3 "First test cases queued" for the spec. Window: Sat Jun 13 → Sun Jun 21 2026 (the 8-day natural gap between Stanford spring quarter end and summer quarter start). This is the proving-ground trip; if travel_search.md works for this, it works for the rest.

## Status

| Date       | Status                                                                                                     |
| ---------- | ---------------------------------------------------------------------------------------------------------- |
| 2026-05-08 | Skeleton drafted. 6 setup questions pending. First test case: McAllen/Harlingen Jun 13-21 (see [`MASTER_PLAN.md`](../MASTER_PLAN.md) Appendix F.3). Implementation deferred to Phase 6.x of [`MASTER_PLAN.md`](../MASTER_PLAN.md). |
