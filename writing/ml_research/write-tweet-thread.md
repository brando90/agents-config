# write-tweet-thread.md — X/Twitter Thread Skill (paper → tweprint draft)

**TLDR:** Reusable, paper-agnostic skill for turning a paper (arXiv/OpenReview link, repo path, or PDF) into an announcement thread for X/Twitter in the CoDaPO/tweprint house style: 6–9 numbered tweets, every tweet ≤280 chars (programmatically checked), exact numbers only, hook → problem → method → results → insight → links. Drafts go to the paper's repo + PR + per-paper email for co-author review — never posted directly.

## When to use this skill

Trigger when the user asks for a tweet thread / X thread / tweprint announcing a paper. Typical invocation:

> Use the write-tweet-thread skill.
> Paper: `<link | repo path | PDF>` · Venue/status: `<accepted at ...>` · Links: `<arXiv, GitHub>`

Siblings: [`write-linkedin-post.md`](write-linkedin-post.md) (announcements usually launch together — offer to produce both), [`write-sail-blog-post.md`](write-sail-blog-post.md), [`write-poster.md`](write-poster.md). Format/voice reference: [`../../workflows/tweprints.md`](../../workflows/tweprints.md) — where the two disagree (thread length: this skill says 6–9, tweprints says 4–8; tagging: this skill omits handles by default, tweprints tags in the final tweet), **this skill wins for paper announcements**. Gold-standard example: [`assets/codapo_example_x_thread.md`](assets/codapo_example_x_thread.md) (structure mirrored below).

## ⚠ Non-negotiables

1. **≤280 characters per tweet, verified programmatically** — count with X rules approximated: every URL = 23 chars, emoji ≈ 2 chars. Print the per-tweet counts in your reply. Never eyeball it.
2. **Draft-for-review, never post.** Deliver as a file in the paper repo + PR + email to that paper's author group (one email per paper). Posting is a human act.
3. **Anonymity check.** If the paper is under double-blind review, put a loud header note: post only after acceptance/de-anonymization is public. Same for private repos / missing arXiv links — mark `[TODO]`, never fabricate.
4. **Numbers only from the paper**, hedges preserved (a "candidate bottleneck" does not become "the bottleneck" in a tweet). CS197 jargon and AI-tell words stay out (Trigger Rules 23–24, antipattern #15).
5. **Author @-handles omitted by default** (per the CoDaPO template) unless the user supplies them — leave a `> Author @-handles intentionally omitted for now.` header line.

## Structure (CoDaPO template, composed with `workflows/tweprints.md`)

File header: title line `# <Paper> — EN Twitter / X Thread`, then blockquote requirements (≤280 chars; links status; handles omitted). Then `n/N:` tweets separated by `---`:

1. **1/N Hook 🚨/🚀** — the core question or most surprising number + what the project is + `🧵`.
2. **2/N Problem 🔍** — what's broken; ❌ or numbered patterns for prior-work limits.
3. **3/N Diagnosis/idea 🧠💡** — the one-sentence insight; teaser "That's where X comes in 👇" optional.
4. **4/N Method ⚙️** — the artifact/mechanism, one line per component (➡️/🔧/🎯/🔁).
5. **5–7/N Results 📊📈** — one tweet per result family, exact numbers, lead with the metric.
6. **N/N Links 🤝** — 📄 paper, 🐙/💻 code, venue, "feedback welcome"; credits/handles when supplied.

Each tweet must stand alone; shorter thread beats padded thread. 1–2 tweets should name a figure to attach (note it in an HTML comment).

## Deliverable

1. `<paper_repo>/blog/<yyyy-mm>-<paper-slug>-x-thread.md` (comms artifacts live beside the blog draft), committed on the paper's comms/review branch, PR'd (or appended to the existing review PR).
2. Reply with: per-tweet char counts, all `[TODO]` flags, and the anonymity/privacy warnings that apply.
3. One review email per paper to its author group with the draft attached (compose with `write-poster.md` Deliverable 1b).
4. Also produce 2 alternate hook tweets (1/N variants) labeled "Hook A/B/C" so co-authors pick the opener.
