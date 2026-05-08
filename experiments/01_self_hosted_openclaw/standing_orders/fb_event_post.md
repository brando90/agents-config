# Standing Order — Facebook Event Posting (SBSBZ + general)

**TLDR:** Brando dictates an SBSBZ class / social / cancellation; OpenClaw drafts a Facebook Event (title, time, venue, description, cover image) using the matching template, shows the preview, and creates the event after `post`. Same flow for general (non-SBSBZ) events.

## Goal

Collapse the "I need to post tonight's bachata social to FB Event before 5pm" recurring scramble into a 30-second Telegram exchange. Reuse SBSBZ templates so phrasing is consistent across recurring events.

## When this fires

- **Brando-initiated (Telegram)** — `/fbevent <template-name> <date-time> <venue> [extra notes]` — e.g. `/fbevent class 2026-05-15T19:00 dancespot tonight's class is bachata-only`.
- **Brando-initiated (Telegram)** — free-form: *"draft an FB event for tomorrow's SBSBZ social at the Stanford ballroom 8pm-midnight"*.
- **Cross-trigger** — when [`drive_to_social.md`](./drive_to_social.md) detects a folder named `<event>_advance/`, it can route here instead of (or in addition to) IG/FB feed posts.

**Never** auto-creates events. SBSBZ recurring schedule (if any) is drafted but never created without `post`.

## Inputs

1. **Template** — class / social / reminder / cancellation / venue_change / recap (from `config/sbsbz_templates/`); or `general` for non-SBSBZ events.
2. **Date / time** (with timezone — default America/Los_Angeles).
3. **Venue** — name + address (look up from `config/sbsbz_venues.json` if recurring; else Brando provides).
4. **Description body** — Brando's intent in 1–2 sentences.
5. **Cover image** — optional; pull from `Drive/OpenClaw/sbsbz/cover-images/` or Brando attaches.
6. **Target Page or Group** — SBSBZ FB Page (default) or a Group Brando admins.

## Workflow

1. **Capture**: Brando sends the command or free-form description.
2. **Classify**: which template? Which target Page/Group? Use `config/sbsbz_templates/<template>.md` if matched; else freestyle from a generic template.
3. **Draft**:
   - **Title**: `<event-type>: <key descriptor> — <date>` (e.g. "Bachata Social: Sensual Night — Sat May 17").
   - **Description**: render the template with Brando's inputs filled in. Include WhatsApp / IG / mailing-list cross-links if present in `config/sbsbz_links.json`.
   - **Cover image**: best-fit from Drive folder, or skip.
   - **Event details**: start/end time, location, online URL if hybrid.
4. **Show**: preview as it will appear on FB (rendered title + description + image thumbnail + time + venue).
5. **Approve (Brando)**: `post` / `edit: <text>` / `tweak: <instr>` / `cancel`.
6. **Execute**: FB Graph API `POST /{page-id}/events` (preferred) or Playwright fallback for Group events. Capture event URL.
7. **Log**: `~/openclaw/audit/social_posts.jsonl` with `{platform: "fb_event", page_id, event_id, event_url}`.

## Outputs

- Created FB Event with URL.
- Audit log entry.
- (Optional cross-post): IG announcement (see [`ig_post.md`](./ig_post.md)) + mailing list (Gmail) — separate `post` approval each.

## Safety rules

- **Approval level:** `never_autonomous`.
- **Recurring events** — never auto-renew. If a class is weekly, Brando still confirms each week (or sets up a `confirm-recurring` token at setup time, batched 4-week-ahead).
- **Cross-posting** — never auto-cross-post to IG / mailing list without separate approval per channel.
- **Cancellation** — cancellations skip the cover-image step and use a higher-urgency template; still requires `post`.
- **Venue change** — must reference the original event URL; offer to update existing event vs. create new.

## Open setup questions

1. **FB Page admin token** — does Brando have admin access to the SBSBZ FB Page? Long-lived Page access token via Graph API.
2. **Group vs Page** — is SBSBZ a FB Page (Graph API works) or only a Group (Graph API limited; Playwright needed)?
3. **Templates seed** — populate `config/sbsbz_templates/` with current SBSBZ phrasing (class / social / reminder / cancellation / venue_change / recap).
4. **Venues file** — `config/sbsbz_venues.json` with the recurring venues (Stanford ballroom, dance studios, etc.) including addresses.
5. **Acronym** — what does SBSBZ stand for, exactly? Confirmed *bachata + zouk, no salsa*; fill the expansion into the spec when known.

## Status

| Date | Status |
|------|--------|
| 2026-05-08 | Skeleton drafted. Setup questions pending. Implementation deferred until Phase 6.4 of [`MASTER_PLAN.md`](../MASTER_PLAN.md). |
