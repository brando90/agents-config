# write-sail-blog-post.md — SAIL Blog Post Skill (paper → lab-blog draft)

**TLDR:** Reusable, paper-agnostic skill for turning a paper (arXiv/OpenReview link, repo path, or PDF) into a Stanford AI Lab (SAIL) blog deliverable: a full explainer-post draft in the SAIL format, plus a conference-roundup blurb (title / authors / links / 2–3-sentence TL;DR / hero image) ready for SAIL's "Papers and Talks at <VENUE>" form. Drafts go to the paper's repo for co-author review via PR — never straight to publication.

## When to use this skill

Trigger when the user asks for a SAIL / lab blog post about a paper, or when the SAIL blog team calls for papers for a conference roundup (e.g., "SAIL at ICML 2026"). Typical invocation:

> Use the write-sail-blog-post skill from `~/agents-config/writing/ml_research/`.
> Paper: `<arXiv link | repo path | PDF>`
> Venue + status: `<e.g. accepted at ICML 2026 Math-AI workshop>`
> Target: `<explainer post | roundup blurb | both (default)>`
> Links: `<arXiv, GitHub, dataset, W&B>`

Siblings: [`write-poster.md`](write-poster.md) (same ingestion pipeline), [`write-abstract.md`](write-abstract.md), umbrella guide [`ml_research_writing.md`](ml_research_writing.md). The SAIL structure/voice reference is [`../../workflows/blog-posts.md`](../../workflows/blog-posts.md) — read it before drafting; this skill is the paper→draft *procedure*, that doc is the format spec. For Brando's personal site use `writing/blog/` instead (Trigger Rule 25).

## ⚠ Non-negotiables

1. **Draft-for-review, never publish.** SAIL posts require co-author sign-off (and the SAIL blog team's pipeline). The deliverable is a draft in the paper's repo + a PR tagging co-authors — publishing is a human decision.
2. **Broad-ML audience.** A SAIL reader is an ML person outside your subfield. Translate formal-methods vocabulary per Trigger Rule 24 (*specification* → *the theorem to prove*, etc.). Define every domain term on first use.
3. **CS197 jargon never appears in the draft body** (`bit flip`, `north star`, ...) — scaffold with `<!-- move N: ... -->` HTML comments instead (markdown equivalent of the `% CS197` LaTeX comments). Trigger Rule 23 applies.
4. **No AI-tell phrasing** (antipattern #15 in `ml_research_writing.md`): no *leverage*, *seamless*, *delve*, tutorial scaffolding. Match the register of recent SAIL posts.
5. **Numbers only from the paper.** Every claim and number in the draft must exist in the paper source; link the paper where a reader would want proof.

## Inputs (interpret from the user's message)

**Required:** paper source (link/path/PDF) and venue + acceptance status.
**Optional:** target (default: both explainer + blurb), links (arXiv/GitHub/dataset — missing ones become `[TODO: ...]`), hero figure choice, output path (default `<paper_repo>/blog/<yyyy-mm>-<venue-slug>-<paper-slug>-sail-draft.md`), deadline context (roundup form due dates — if a stated deadline has passed, say so loudly in the reply and draft the outreach note to the blog team instead of silently proceeding).

## Step 1 — Ingest the paper

Same order as `write-poster.md`: arXiv source tarball (best: original figures) → repo `.tex` + `figures/` → PDF read. Extract: title; authors; the problem and why a broad ML reader should care; the one-sentence contribution; the method at diagram level; 2–3 headline results with exact numbers; limitations/caveats the paper itself states; the money figure and 1–2 supporting figures.

## Step 2 — The two deliverables

### A. Explainer-post draft (SAIL format — full spec in `workflows/blog-posts.md`)

Structure: memorable title (playful allowed) → author line → date → **TL;DR** (2–3 sentences + `[Paper] [Code] [Data]` links) → Introduction (~3–5 short paragraphs, motivating Figure 1 early) → Method (diagram-level, "see the paper for details") → Results (one takeaway-first paragraph per result, figures inline) → Conclusion (1 paragraph, future directions) → tags. Rules: ≥2–3 figures; no paragraph over 5 sentences; conversational but every number exact; artifact links in TL;DR *and* conclusion.

### B. Roundup blurb (for "SAIL at <VENUE>" compilation forms)

A self-contained block at the top of the same file, clearly delimited, containing exactly what roundup forms ask for: paper title; full author list; venue/workshop + status; links (arXiv, GitHub, project page); 2–3-sentence TL;DR (a compressed CS197 six-move: problem → what we built → headline number → why it matters); one hero image (repo-relative path + suggested caption); contact author + email; optional 280-char tweet-length summary (compose with `workflows/tweprints.md` if a full thread is requested).

## Step 3 — Deliver for review

1. Write the draft file into the paper's repo (`blog/` dir; create it if missing). Commit on a branch, open a PR titled `SAIL blog draft: <paper short name>`, and tag the co-authors the user names (plus all authors with known GitHub handles — resolve via `~/ultimate-utils/py_src/uutils/collaborators.py` and `gh api repos/<owner>/<repo>/contributors`).
2. PR body per Trigger Rule 7 (≤10-bullet Summary + short Test plan): what the draft claims, which numbers came from where (section/table), what's `[TODO]`, and an explicit ask: "sign off or comment by <date>".
3. In the chat reply: the draft's `git diff --stat`, the TL;DR verbatim, all `[TODO]` flags, and any deadline warnings.

## Quality bar

| Dimension | Weak | Strong |
|---|---|---|
| TL;DR | Restates the abstract | 2–3 sentences a tired scroller understands, with links |
| Intro | Literature review | A failure story a broad ML reader recognizes by paragraph 2 |
| Method | Notation dump | One diagram + plain-language walkthrough |
| Results | Table screenshot wall | Takeaway sentence first, then the one figure that proves it |
| Review loop | "Posted!" | PR with tagged co-authors and a sign-off deadline |
