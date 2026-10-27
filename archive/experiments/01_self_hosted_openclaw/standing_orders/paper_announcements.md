# Standing Order — Paper Announcements (LinkedIn + X + Blog)

**TLDR:** On a new arXiv submission, conference acceptance, or workshop talk, OpenClaw drafts cross-posts for LinkedIn, X (`@BrandoHablando`), and Brando's personal blog ([brando90.github.io/brandomiranda](https://brando90.github.io/brandomiranda)). Each surface gets its own approval — Brando can `post: linkedin` but `tweak: x` separately.

## Goal

Eliminate the "I should announce VeriBench but I haven't because writing the same thing 3 times in 3 voices is exhausting" backlog. One paper → three drafted posts → 90 seconds of approval per surface.

## When this fires

- **Brando-initiated (Telegram)** — `/paper <arxiv-id-or-url> [--type submit|accept|talk]`.
- **Optional inbound** — arxiv.org email notification → triage agent flags → Brando can confirm with `/paper <suggested-id>`.

**Never** auto-posts.

## Inputs

1. **Paper identity** — arXiv ID, title, authors, abstract.
2. **Type** — `submit` (preprint up) / `accept` (conference) / `talk` (workshop or invited).
3. **Highlight** — Brando's optional one-line "what's the headline" override.
4. **Image** — optional teaser figure from the paper or from `Drive/OpenClaw/papers/<paper-id>/`.

## Workflow

1. **Capture**: Brando sends `/paper <id-or-url> --type <type>`.
2. **Fetch**: arXiv abstract + authors + title.
3. **Draft** per surface:
   - **LinkedIn** (200–400 words): formal, "thrilled to share", co-authors tagged, key contribution, link to paper.
   - **X** (≤ 280 chars × 1–4 thread posts): hook tweet + 1–3 follow-ups summarizing contributions, paper link, co-authors @-tagged.
   - **Blog post** (300–800 words): plain Markdown; longer-form context, motivation, contribution, what's next.
4. **Show**: each draft side-by-side with character/word counts.
5. **Approve (Brando)**: `post` (all surfaces) / `post: linkedin` / `post: x` / `post: blog` / `edit: <surface>: <text>` / `tweak: <surface>: <instr>` / `cancel`.
6. **Execute**:
   - **LinkedIn**: API (if Marketing Developer Platform approved) or Playwright with persisted login.
   - **X**: API (paid tier required for write) or Playwright fallback.
   - **Blog**: write to `_posts/<date>-<slug>.md` in the brando90.github.io repo, commit + push (auto-deploys via GitHub Pages).
7. **Log**: `~/openclaw/audit/paper_announcements.jsonl` with `{paper_id, surface, post_url}` per surface.

## Outputs

- Posted LinkedIn / X thread / blog post (per approved surfaces).
- Blog commit on brando90.github.io.
- Audit log entries.

## Safety rules

- **Approval level:** `never_autonomous`.
- **Co-author etiquette** — flag if any co-author has previously asked not to be tagged (Brando maintains an `_no_tag.txt` list in `config/coauthor_tags.json`).
- **Embargo** — refuse if `--type submit` and arXiv abstract isn't actually live yet.
- **Hashtag/handle spam guard** — cap at 5 mentions per X tweet.

## Open setup questions

1. **LinkedIn API access** — does Brando have Marketing Developer Platform approval? If not, Playwright fallback with a long-lived persisted session.
2. **X API tier** — write API requires paid Basic ($100/mo) or higher; Playwright fallback otherwise.
3. **Blog repo path** — confirm `_posts/<date>-<slug>.md` Jekyll convention; or use whatever the current site uses.
4. **Co-author tag list** — populate `config/coauthor_tags.json` mapping author name → LinkedIn URL + X handle + "no tag" flag.
5. **Image teaser** — auto-extract from arXiv PDF (page-1 figure) or have Brando attach manually?

## Status

| Date | Status |
|------|--------|
| 2026-05-08 | Skeleton drafted. Setup questions pending. Implementation deferred until Phase 6.7 of [`MASTER_PLAN.md`](../MASTER_PLAN.md). |
