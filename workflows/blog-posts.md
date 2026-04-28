# Workflow: Blog Posts (SAIL Blog Style)

**TLDR:** Reference for writing and publishing research blog posts in the
Stanford AI Lab (SAIL) Blog format. Use when starting a project blog post
or porting an existing draft into the SAIL template — covers structure,
voice, figures, citations, and the publish flow.

---

## Structure (SAIL Blog Format)

1. **Title:** Short, memorable, can be playful (e.g., "Fantastic Bugs and Where to Find Them in AI Benchmarks").
2. **Author line:** All authors, comma-separated.
3. **Date.**
4. **TL;DR:** 2–3 sentences summarizing the key contribution, method, and result. Include links to [Paper], [GitHub], [Data] at the end.
5. **Introduction:** Set the stage — what's the problem, why does it matter, what's the status quo, and what does this work do differently? ~3–5 paragraphs. Include a motivating figure (Figure 1) early.
6. **Method:** Explain the approach at a level accessible to a broad ML audience. Use figures and diagrams. Avoid excessive math — put rigorous definitions in the paper and say "see our paper for details."
7. **Results:** Walk through key experiments. One subsection or paragraph per major result. Include figures and tables inline. Lead with the takeaway, then show the evidence.
8. **Conclusion:** 1 paragraph summarizing contributions and future directions. End on an optimistic note about impact.
9. **Footer:** RSS/Twitter/email subscription links. Tags (e.g., `machine learning`, `formal verification`).

---

## Style Rules

- **Accessible language:** Write for a broad ML audience, not just domain experts. Define terms on first use.
- **Figures are mandatory:** Every blog post needs at least 2–3 figures. Lead with a compelling visual (pipeline diagram, key result chart, or motivating example).
- **TL;DR is mandatory:** The first thing after the title. Readers decide whether to continue based on this.
- **Link to artifacts:** Paper (arXiv), GitHub repo, dataset, W&B report — all linked in the TL;DR and again in the conclusion.
- **Conversational but precise:** More informal than a paper, but numbers and claims must be accurate.
- **No walls of text:** Break up with figures, bullet lists, and subheadings. If a paragraph is >5 sentences, split it.
- **Cross-reference the tweprint:** The blog post and tweprint should launch together. Link the tweprint thread from the blog and vice versa.

---

## Reference Examples

- **SAIL Blog — Fantastic Bugs:** https://ai.stanford.edu/blog/fantastic-bugs/ — Exemplary structure: playful title, strong TL;DR with artifact links, motivating Figure 1, accessible method section, clear results with inline figures, concise conclusion.
- **SAIL Blog homepage:** https://ai.stanford.edu/blog/ — Browse for more examples of tone and formatting.

---

## Process

1. **Draft** in Google Docs or Overleaf for easy co-author review.
2. **Figures:** Export as high-res PNG. Use consistent styling (same font, color palette).
3. **Internal review:** Share with co-authors and get sign-off before publishing.
4. **Publish:** Submit to the SAIL blog (or project website). Coordinate timing with the tweprint launch.
5. **Cross-post:** Share the blog link in the tweprint thread, Discord, Slack, and mailing lists.
