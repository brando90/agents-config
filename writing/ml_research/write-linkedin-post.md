# write-linkedin-post.md — LinkedIn Post Skill (paper → announcement draft)

**TLDR:** Reusable, paper-agnostic skill for turning a paper into a LinkedIn announcement in the CoDaPO house style: excitement + title + venue, institutional collaboration credit, problem → diagnosis → method (➡️ components) → exact-number results bullets → links + hashtags. ~350–500 words, professional register. Drafts go to the paper's repo + PR + per-paper email — never posted directly.

## When to use this skill

Trigger when the user asks for a LinkedIn post announcing a paper. Typical invocation:

> Use the write-linkedin-post skill.
> Paper: `<link | repo path | PDF>` · Venue/status · Links: `<arXiv, GitHub>`

Siblings: [`write-tweet-thread.md`](write-tweet-thread.md) — announcements usually launch together; when the user asks for "announcements," produce both. Gold-standard example: the CoDaPO LinkedIn post (saved by Brando 2026-07-04; structure mirrored below).

## ⚠ Non-negotiables

1. **Draft-for-review, never post.** File in the paper repo + PR + one review email per paper to its author group.
2. **Anonymity/privacy check.** Double-blind paper → loud header: post only after acceptance is public. Private repo / no arXiv → `[TODO]` links, never fabricate.
3. **Author-naming policy is the user's call.** The CoDaPO example names every author with affiliations; for large author lists (>8), default to institutions ("led by researchers at X, with collaborators at Y, Z") plus `[TODO: confirm author-naming policy]` — naming some but not all co-authors on LinkedIn is a political decision only the user makes.
4. **Numbers only from the paper, hedges preserved.** No CS197 jargon, no AI-tell filler (Trigger Rules 23–24, antipattern #15) — LinkedIn tolerates enthusiasm, not *leverage/seamless/delve*.

## Structure (CoDaPO template)

File header: `# <Paper> — EN LinkedIn` + blockquote link status. Then:

1. **Opening:** "We are excited to share our new paper, accepted at `<venue>`: **"<Title>"**!" (adjust verb to actual status).
2. **Collaboration credit:** institutions + names per Non-negotiable 3.
3. **Problem paragraph:** the gap in plain terms, ending with the question the paper asks.
4. **Bold-header sections** mirroring the paper's arc, e.g. **"First, a diagnosis."** (bulleted findings) → **"Then, the method: <Name>."** with ➡️ **Component** one-liners → a "crucially, ..." sentence for the key property (cost, scope, guarantee).
5. **Empirical Results:** 3–5 bullets, exact numbers with arrows (X% → Y%), one bullet per result family; include the paper's own caveats.
6. **Explore the work:** 📄 Paper / 💻 GitHub links.
7. "We welcome contributions and feedback!" + 5–8 hashtags (#MachineLearning #<venue year> + domain tags).

Length 350–500 words. Every claim must appear in the paper.

## Deliverable

1. `<paper_repo>/blog/<yyyy-mm>-<paper-slug>-linkedin.md`, committed on the paper's comms/review branch, PR'd (or appended to the existing review PR).
2. Reply with `[TODO]` flags + anonymity/privacy warnings.
3. One review email per paper (bundle with the X-thread draft when both were produced — same paper, same email).
