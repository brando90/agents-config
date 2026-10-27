# Standing Order — Instagram Posting

**TLDR:** Brando provides intent + photo(s); OpenClaw drafts feed-post + story + reel-caption variants and posts after `post` approval. Used for SBSBZ recaps, paper announcements, conference photos, casual life updates.

## Goal

Make Instagram a 30-second-per-post operation instead of 10 minutes of caption-writing.

## When this fires

- **From Drive folder** — see [`drive_to_social.md`](./drive_to_social.md). The Drive watcher delegates IG-specific drafting here.
- **Brando-initiated (Telegram)** — forward photo(s) + one-line intent ("bachata night recap, IG feed only" or "VeriBench accepted at NeurIPS, IG + story").
- **Cross-post from FB Event** — when an SBSBZ FB Event is created via [`fb_event_post.md`](./fb_event_post.md), optionally draft IG announcement (separate `post`).

## Inputs

1. **Photo(s)** — 1–10 images, served by Drive ID or attached.
2. **Intent** — one-line context (event recap, paper announcement, casual life update, etc.).
3. **Surface** — feed / story / reel (default: feed; if Brando says "story" or "reel", route accordingly).
4. **Hashtag set** — derived from intent: bachata/zouk → SBSBZ tags from `config/ig_hashtags.json`; paper → research tags; etc.

## Workflow

1. **Capture**: photos + intent.
2. **Classify** surface (feed / story / reel) and template (SBSBZ recap / paper announcement / casual / Lean-AI).
3. **Draft**:
   - **Feed caption**: 50–150 words, leading hook + body + 5–10 hashtags + tagged accounts.
   - **Story caption**: ≤ 30 words, single hook.
   - **Reel caption**: 30–80 words + 8–15 hashtags (reels reward hashtags more).
4. **Show**: preview thumbnail grid + caption + hashtag set + posting time recommendation.
5. **Approve (Brando)**: `post` / `edit:` / `tweak:` / `cancel`.
6. **Execute**: IG Graph API (Business/Creator account linked to FB Page) — `POST /{ig-user-id}/media` then `POST /{ig-user-id}/media_publish`. Playwright fallback otherwise.
7. **Log**: `~/openclaw/audit/social_posts.jsonl` with `{platform: "ig", surface, post_id, url}`.

## Outputs

- Posted IG content (feed / story / reel).
- Audit log entry.

## Safety rules

- **Approval level:** `never_autonomous`.
- **Face-blur guard** — if a photo includes faces other than Brando's recurring SBSBZ community, ask before posting.
- **Hashtag spam guard** — refuse > 25 hashtags (IG soft-shadowbans high counts).
- **DM auto-reply** — never. (IG DMs are out of scope.)

## Open setup questions

1. **IG account type** — Business or Creator? Required for Graph API; otherwise Playwright with persisted login.
2. **FB Page linkage** — IG must be linked to a FB Page Brando admins for the Graph API path.
3. **Hashtag library** — populate `config/ig_hashtags.json` (SBSBZ tags, research tags, casual tags).
4. **Templates** — feed / story / reel caption templates per category in `config/ig_templates/`.

## Status

| Date | Status |
|------|--------|
| 2026-05-08 | Skeleton drafted. Setup questions pending. Implementation deferred until Phase 6.4 of [`MASTER_PLAN.md`](../MASTER_PLAN.md). |
