# Workflow: Tweprints (Tweet Threads for Research Announcements)

A "tweprint" is a tweet thread (typically 4–8 tweets) that announces a research project, dataset, or paper to the ML/AI community on X/Twitter. It is the primary way we publicize work.

---

## Structure (follow this order)

1. **Hook tweet (1/N):** Lead with the core question or surprising result. Use an attention-grabbing emoji prefix (e.g., `🚨`, `📢`). State what the project is, the single most impressive number, and end with `🧵1/N`.
2. **Problem tweet (2/N):** Explain the gap — what's broken, missing, or hard. Use ❌ bullets for limitations of existing approaches. End with a teaser: "That's where [Project] comes in. 👇"
3. **Method / How-it-works tweet (3/N):** Concise explanation of the approach. Include a figure if possible (architecture diagram, pipeline, or algorithm). Keep it accessible — no jargon without a one-line explanation.
4. **Result tweets (4/N, 5/N, …):** One tweet per key result or domain. Lead with the metric: `📊 [Project] achieves X% improvement over Y`. Use ⚡ or 📈 emojis. Attach charts/tables as images.
5. **Insight / Why-it-matters tweet:** Explain an interesting finding, ablation, or design decision. This is the "so what?" tweet.
6. **Future directions + credits tweet (N/N):** Mention future work, link to paper/code/data, tag co-authors and collaborators. Format: `Joint w/ @author1 @author2 …`

---

## Style Rules

- **Emojis:** Use them — tweprints are informal and attention-grabbing. Prefer 🚨📢📊⚡💨📈🔍🛑 over obscure ones.
- **Numbers over vague claims:** "64% of sorry's closed" beats "significant progress." Always include the concrete metric.
- **Figures:** Attach 1–2 key figures as images. The hook tweet or a result tweet should have a visual.
- **Thread length:** 4–8 tweets. Shorter is better. Each tweet must standalone — readers may see only one in their feed.
- **Tone:** Enthusiastic but honest. Don't oversell. If something is a limitation, frame it as an open challenge.
- **Tags:** Tag co-authors, relevant researchers, and the lab (`@StanfordAILab`). Tag people whose work you build on.
- **Links:** Paper link, GitHub repo, and blog post (if available) go in the final tweet.
- **Character limit:** Each tweet must be ≤280 characters. Use the thread to expand — don't cram.

---

## Reference Examples

- **ZIP-FIT tweprint:** 8-tweet thread announcing compression-based data selection. Hook: core question + best number. Threads through problem → method → results (Code Gen) → results (AutoFormalization) → insight (alignment thresholds) → future work + credits.
- **Putnam Axiom tweprint:** https://x.com/BrandoHablando/status/1945920434521923652
- **Additional thread:** https://x.com/BrandoHablando/status/1946281237435568579

---

## Tweprint Style Guide (Google Doc)

Full style notes, ideas, and drafts: https://docs.google.com/document/d/1nLZka1BLydqbOeGUwwCeKyNF-wGa1I495vPVzfc91S4/edit?tab=t.0

---

## Overleaf Tweprint Examples (by Rylan Schaeffer)

These are polished PDF tweprints — study them for visual layout and concise academic writing:
- Elusive: https://www.overleaf.com/read/dvdqtdsptksq#fd532f
- Monkey Power Laws: https://www.overleaf.com/read/vhqhpstxcmkp#ee4042
- Collapse or Thrive: https://www.overleaf.com/read/tchcwkzrvchk#e0e416

---

## Process

1. **Draft** the tweprint in a `.txt` file under `tweets/<MM_DD_YYYY>/` in the project repo.
2. **Review** with co-authors (share the `.txt` or Google Doc draft).
3. **Attach figures** — export key plots/tables as images and note which tweet they go with.
4. **Post** — copy-paste each tweet sequentially as a thread on X.
5. **Cross-post** — share the thread link on Discord, Slack, and any relevant channels.
