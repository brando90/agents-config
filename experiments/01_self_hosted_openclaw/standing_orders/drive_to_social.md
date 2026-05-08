# Standing Order — Drive → FB/IG Photo Pipeline

**TLDR:** Brando drops photos into `Drive/OpenClaw/social-queue/<event-name>/`. OpenClaw watches the folder, picks the best 1–10 photos, drafts FB + IG captions using SBSBZ event templates, suggests a posting schedule, and DMs the preview. Brando says `post` to publish.

## Goal

Eliminate the multi-step "download from Drive → write caption → upload to FB → write again → upload to IG" tax. One drop into a tagged folder = one Telegram approval = posted on both platforms.

## When this fires

- **Drive folder watch** — `gog drive list --folder OpenClaw/social-queue/` polled every 15 min via `openclaw cron`. New file → enters this workflow.
- **Brando-initiated (Telegram)** — `/social <event-name>` — manual trigger to re-process a folder, or `/social <event-name> --reprocess` to re-do an already-posted folder.

**Never** posts without explicit `post`.

## Inputs

1. **Drive folder** — `Drive/OpenClaw/social-queue/<event-name>/` (event-name slug picks the SBSBZ template).
2. **Photos** — JPEG/PNG; OpenClaw inspects EXIF for date/location.
3. **Optional caption hint** — file `_intent.txt` in the folder, if present.
4. **Target channels** — derived from event-name (SBSBZ events → FB + IG; paper events → IG + LinkedIn + X via [`paper_announcements.md`](./paper_announcements.md)).

## Workflow

1. **Capture**: cron polls Drive, finds new folder or new files in existing folder.
2. **Classify**: event-name → SBSBZ template? Paper announcement? Lean-AI? Casual?
3. **Pick** the best 1–10 photos (heuristic: face-detection score, sharpness, varied angles; use `gog drive thumbnail` for previews).
4. **Draft** captions for each target channel by delegating to [`fb_event_post.md`](./fb_event_post.md) (if also creating an event) and [`ig_post.md`](./ig_post.md). For mailing list, draft via SBSBZ templates.
5. **Suggest schedule** — immediate / next-morning / golden-hour-tomorrow (PT). Default: golden hour.
6. **Show**: thumbnail grid + per-channel caption + schedule + target channels.
7. **Approve (Brando)**: `post` (all channels) / `edit: <channel>: <text>` / `tweak: <channel>: <instr>` / `cancel`.
   - Per-channel granularity: `edit: ig: <new caption>` only changes IG; bare `post` accepts all.
8. **Execute**: post to each approved channel via the appropriate sub-standing-order.
9. **Log**: `~/openclaw/audit/social_posts.jsonl` per channel + a parent row referencing the Drive folder.

## Outputs

- Posted FB / IG / mailing-list content (per the approved channels).
- Drive folder marked as `_posted_<ts>` (rename or label).
- Audit log entries.

## Safety rules

- **Approval level:** `never_autonomous`.
- **Per-channel approval** — Brando can `post` all, or `edit:` / `tweak:` per channel before final.
- **Photo-leak guard** — don't process photos from folders matching `*-private*` or containing a `_DO_NOT_POST` file.
- **Idempotency** — once a folder is marked `_posted_<ts>`, don't re-process without explicit `/social <event-name> --reprocess`.

## Open setup questions

1. **Drive folder convention** — confirmed `Drive/OpenClaw/social-queue/<event-name>/` (per Brando 2026-05-08).
2. **Photo-pick heuristic** — local face-detection (mediapipe / Vision framework) or call out to a service?
3. **Schedule mechanism** — immediate post via API, or queue via FB/IG native scheduling?
4. **`_intent.txt` schema** — freeform Brando-prose, or structured (target channels, schedule override, hashtags)?

## Status

| Date | Status |
|------|--------|
| 2026-05-08 | Skeleton drafted. Setup questions pending. Implementation deferred until Phase 6.4 of [`MASTER_PLAN.md`](../MASTER_PLAN.md). |
