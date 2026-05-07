# write-blog-post.md - Brando Blog Post Skill
**TLDR:** Reusable workflow for converting Brando's rough idea dumps into polished personal blog posts in the style of his recent `~/brandomiranda/` posts. Load `rules.md` and `blog_writing.md`, infer the strongest argument, draft or edit the post, then verify mechanics and unresolved facts.

---

## When To Use This Skill

Use this when Brando asks to write, draft, revise, polish, restructure, or publish a personal blog post, especially when he dumps rough ideas and expects the agent to turn them into a finished essay.

Typical prompts:

> Dumping ideas: `<messy notes>`. Turn this into a blog post.

> Make this blog badass in the style of the scalable oversight post.

> Write a post for `~/brandomiranda/_drafts/...` from these thoughts.

> Revise this draft so it sounds like my recent blog posts.

This skill is for Brando's personal site. For Stanford AI Lab / SAIL project blog posts, use `~/agents-config/workflows/blog-posts.md` instead. If Brando explicitly wants a personal adaptation of a SAIL-style post, load both and keep the target format explicit.

---

## Inputs

Interpret these from the user's message. Do not block if some are missing.

- **Rough ideas** - free-form notes, voice memo transcript, bullets, chat dump, paper idea, or messy thesis.
- **Target path** - optional file path. If absent and the user clearly wants a file in the blog repo, default to `~/brandomiranda/_drafts/YYYY-MM-DD-slug.md`.
- **Existing draft path** - optional. If provided, edit in place after reading it.
- **Audience** - optional. Default: broad technical readers who know AI/ML at a high level but may not know formal methods or Brando's projects.
- **Goal** - optional. Common goals: personal essay, project launch, research direction, teaching post, opinion post, announcement.
- **Required links/facts** - optional repo, paper, project, people, dates, figures, or citations.

If critical factual information is missing, write with `[TODO: ...]` markers rather than stopping.

---

## Read Before Writing

1. `~/agents-config/writing/blog/rules.md`
2. `~/agents-config/writing/blog/blog_writing.md`
3. Existing target draft, if any.
4. Recent anchor posts if local:
   - `~/brandomiranda/_posts/2026-04-22-formal-methods-scalable-oversight.md`
   - `~/brandomiranda/_posts/2026-04-13-correctness-gated-multi-agent-workflow.md`
5. Any linked source artifacts the post depends on, such as repos, papers, notes, figures, or prior posts.

If `~/brandomiranda/` is unavailable, proceed from the loaded writing docs and say that the local style anchors were unavailable.

---

## Decide The Mode

### Idea-Dump Mode

Use when the user gives rough thoughts and no existing draft.

Output:

- If a target path is provided or clearly implied, write a complete draft to that path.
- If no file output is implied, return a polished draft inline plus a short note of unresolved facts.

### Edit-In-Place Mode

Use when the user gives a draft path.

Rules:

- Preserve frontmatter, title/date unless they are clearly placeholders.
- Preserve user-specific facts and links unless they are wrong.
- Rewrite structure when needed; do not just line-edit weak organization.
- Leave `[TODO: ...]` markers for missing facts instead of inventing.
- Do not delete citation blocks, artifact links, or media references unless obsolete.

### Publish-Prep Mode

Use when the user asks to publish or finalize.

Rules:

- Verify frontmatter, date, slug, author line, TL;DR, links, image paths, and optional BibTeX block.
- Run a local Jekyll/build check if the blog repo supports it and dependencies are available.
- Report any unresolved `[TODO]` markers.

---

## Drafting Workflow

### Step 1: Distill The Spine

Write these privately before drafting:

- **Question:** What question is this post answering?
- **Thesis:** What does Brando believe?
- **Tension:** What makes this non-obvious or worth writing?
- **Personal stake:** Why is Brando the right person to write it?
- **Reader payoff:** What should the reader understand or do differently?

If the spine is fuzzy, pick the strongest interpretation and proceed with a `[TODO: confirm framing]` only if necessary.

### Step 2: Choose The Shape

Pick one:

- **Worry to structural move** - for oversight, understanding, formal methods, values, AI risk, human judgment.
- **Built thing to research program** - for tools, repos, workflows, benchmarks, communities, launches.
- **Teach the principle** - for CS197-style advice, writing, project selection, research methods.
- **Contrarian essay** - for hot takes, field critique, or "everyone asks X, but the real question is Y."

### Step 3: Build The Skeleton

Create:

- Working title.
- TL;DR with 2-3 sentences.
- 4-7 section headings.
- One sentence per section saying what that section proves.
- A planned closing line or closing move.

### Step 4: Draft

Write the draft in one pass using the skeleton. Keep momentum. Preserve Brando's voice:

- First person when useful.
- Strong topic sentences.
- Concrete examples.
- Technical explanations in plain language.
- Short punch sentences after dense paragraphs.
- Honest uncertainty where the topic demands it.

### Step 5: Badass Pass

Revise for force:

- Cut generic setup.
- Replace bland headings.
- Add at least one memorable compression line.
- Make the central contrast explicit.
- Ensure every section makes a claim.
- Remove paper abstract voice and startup-marketing voice.

### Step 6: Trust Pass

Revise for correctness:

- Check links and names.
- Verify numerical and factual claims.
- Mark unresolved facts with `[TODO: ...]`.
- Ensure Markdown renders cleanly.
- Ensure the post can stand alone for a reader who has not read Brando's prior posts.

---

## File Format For `~/brandomiranda/`

Use this for new drafts or posts:

```markdown
---
layout: post
title: "Title Here"
date: YYYY-MM-DD
---

*Brando Miranda — Month YYYY*

**TL;DR.** Two or three sentences.
```

Notes:

- Use `_drafts/YYYY-MM-DD-slug.md` until the user asks to publish.
- Use `_posts/YYYY-MM-DD-slug.md` for published posts.
- The slug should be lowercase, hyphenated, and title-derived.
- Recent posts use an optional BibTeX citation block for citable essays; include one only when useful.
- Do not add a body `# H1`; the Jekyll title already supplies it.

---

## Quality Bar

Before handing back a draft, answer yes to all of these:

- Does the title promise an argument?
- Does the TL;DR make the post worth reading?
- Does the opening begin with tension rather than generic context?
- Does the draft sound like Brando rather than an AI assistant?
- Does the post contain a memorable sentence that compresses the thesis?
- Does the technical explanation stay faithful and readable?
- Are uncertainty and opinion clearly distinguished from verified fact?
- Are unresolved facts marked, not fabricated?

---

## Deliverable

If writing or editing a file, do not paste the full post in the chat unless the user asks. Reply with:

- Path written.
- Structural summary: title, TL;DR claim, section arc.
- Unresolved `[TODO]` facts or links.
- Verification run, if any.
- `git diff --stat <path>` when working inside a git repo.

If drafting inline, provide:

- The full draft.
- A short "open facts" list for anything that still needs verification.
