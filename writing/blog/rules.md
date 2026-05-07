# Brando Blog Rules
**TLDR:** Mandatory checklist for drafting or revising Brando's personal blog posts. Load this with `~/agents-config/writing/blog/blog_writing.md` and `~/agents-config/writing/blog/write-blog-post.md` whenever rough ideas need to become a polished post for `~/brandomiranda/`.

---

## Source Anchors

Use the recent published posts as the style baseline before major drafting:

- `~/brandomiranda/_posts/2026-04-22-formal-methods-scalable-oversight.md`
- `~/brandomiranda/_posts/2026-04-13-correctness-gated-multi-agent-workflow.md`

If the target topic is research process or writing, also skim nearby drafts such as:

- `~/brandomiranda/_drafts/2026-04-16-writing-a-paper-and-picking-projects.md`
- `~/brandomiranda/_drafts/2026-04-16-arguing-a-research-project.md`

Do not copy phrasing from the anchors. Extract the moves: direct question, personal stake, technical compression, clean sections, honest uncertainty, and a closing that returns to the thesis.

If `~/brandomiranda/` is unavailable, continue from these docs and mark any anchor-specific facts as unresolved instead of inventing details.

---

## Non-Negotiable Rules

1. **One central question.** Every post answers one live question, not a topic cloud. Write the question explicitly in the first 1-3 paragraphs or make it obvious from the TL;DR.

2. **Thesis before tour.** State what the post believes before surveying details. The reader should know the argument by the end of the TL;DR and feel the tension by the end of the opening.

3. **Use Brando's first-person authority.** "I think," "I suspect," "I don't know," and "to me" are allowed when they clarify stance. Do not flatten the post into institutional research prose.

4. **Personal, but not diary.** Anecdotes are entry points or evidence. They must pay rent by making the technical or philosophical point sharper.

5. **Technical rigor stays intact.** Check factual claims, links, years, names, tools, paper titles, repo names, and numbers. If a claim is unverified, either verify it or mark it as opinion.

6. **Accessible technical language.** Write for a broad technical reader. Define Lean, formal methods, verification, scalable oversight, agents, benchmarks, or similar terms when the post depends on them.

7. **No paper abstract voice.** Blog prose can use contractions, short punch sentences, rhetorical questions, and direct claims. Avoid "we present," "this work proposes," and venue-style throat clearing unless the post is explicitly about a paper.

8. **No generic AI slop.** Cut "rapidly evolving landscape," "transformative potential," "delve," "unlock," "leverage," "seamlessly," "robust framework," "paradigm shift," "game-changer," and similar phrases unless they are quoted for critique.

9. **Strong claims, honest uncertainty.** It is fine to say "here's my hot take" or "I genuinely don't know." Do not hedge out of fear. Do not overstate beyond the evidence.

10. **Short sections with useful headings.** Headings should name the role of the section: "The worry," "The structural move," "What I built," "What I learned." Avoid vague headings like "Background" when the section is really an argument.

11. **Paragraphs stay breathable.** Default to 2-5 sentences per paragraph. Split anything that becomes a wall of text unless a deliberately dense paragraph is doing rhetorical work.

12. **Default length: 900-1,600 words.** Shorter is fine for a sharp essay. Longer needs a clear structural reason and more sectioning.

13. **Use memorable compression.** Each post should have at least one sentence that crystallizes the argument in plain language, e.g. "Let the verifier check the answer; let the human check the question." Write toward that line.

14. **End by returning to the question.** The close should land the argument, not trail into generic optimism. If the post began with a worry, say what the worry becomes after the post's reframing.

15. **CS197 shorthand stays private.** Terms like `bit flip`, `vectoring`, `north star`, and `killer demo` may guide planning, but remove them from reader-facing blog prose unless the post is explicitly teaching CS197 concepts.

16. **Use Jekyll mechanics correctly.** Published posts live in `~/brandomiranda/_posts/YYYY-MM-DD-slug.md`; drafts live in `~/brandomiranda/_drafts/YYYY-MM-DD-slug.md`. Keep frontmatter, author line, TL;DR, and optional citation block consistent with recent posts.

17. **Do not confuse personal blog with SAIL blog.** Personal posts do not require the SAIL format, mandatory 2-3 figures, artifact links in the TL;DR, co-author review, or launch coordination unless Brando asks for those explicitly. For a SAIL / lab research blog post, use `~/agents-config/workflows/blog-posts.md` instead.

---

## Shape Templates

### Personal Research Essay

Use for philosophical or research-direction posts like scalable oversight.

1. Live conversation, worry, or observation.
2. Why the worry is real but incomplete.
3. Structural reframing: the move that makes the problem tractable.
4. How far the idea goes, including limits.
5. What the worry means after the reframing.

### Project / Workflow Post

Use for posts like the agents-config writeup.

1. Practical problem Brando hit personally.
2. Why the problem matters for serious work.
3. What Brando built.
4. How it actually works in daily practice.
5. What Brando learned.
6. What this opens next.

### Research-Teaching Essay

Use for CS197-style posts on writing, project choice, or argument.

1. The failure mode students or researchers hit.
2. The principle that fixes it.
3. A worked example.
4. Concrete rules.
5. Takeaways that a reader can apply immediately.

---

## Final Pass Checklist

- Does the title name the actual argument, not just the topic?
- Does the TL;DR give the question, answer, and stakes?
- Does the first paragraph avoid generic setup?
- Does every section advance the same central claim?
- Are factual claims verified or framed as opinion?
- Are the best 2-3 lines memorable enough to quote?
- Did you remove paper voice, startup voice, and generic AI phrases?
- Did you preserve Brando's directness, humor, and willingness to say "I don't know"?
