# Experiment NN — [Speaker / Talk Title] → Repo Takeaways

**Status:** [Skeleton / Transcript Captured / Takeaways Drafted / Patches Merged]
**Started:** YYYY-MM-DD
**Branch:** `claude/<slug>`
**Source:** [video / paper / podcast URL]
**Title / Author:** [from oEmbed or manual]

## Purpose

This template is for the recurring loop: "take an external talk or paper,
distil it, and turn the distillation into concrete patches to `agents-config`."
It is *not* for ML-research experiments — for those, copy
`experiment_template_readme.tex` instead.

## Required files

```
experiments/NN_<slug>/
├── README.md              <- this template, filled in
├── video_metadata.json    <- written by scripts/fetch_youtube_transcript.sh (oEmbed)
├── fetch_attempts.md      <- log of every fetch attempt + outcome; only created on failure
├── transcript.md          <- verbatim transcript (auto-fetched or pasted)
└── takeaways.md           <- Section A: meta-takeaways  /  Section B: content-takeaways
```

## Bootstrap commands

```bash
SLUG="NN_<slug>"
mkdir -p "experiments/$SLUG"
bash scripts/fetch_youtube_transcript.sh <youtube_url> "experiments/$SLUG"
# transcript.md will be missing if YouTube blocks this IP — paste manually.
```

## `takeaways.md` item shape

Every takeaway must be actionable, traceable, and small. Use this shape:

> **Claim from source (≤2 sentences, with timestamp/page):**
> **What in the repo it touches (file:line or section):**
> **Proposed change (concrete diff or new file path):**
> **Why it is worth doing (1 sentence):**

Group takeaways into two sections:

- **Section A — Meta-takeaways from the *attempt itself*** (process, tooling,
  blockers). Often the most valuable when the source content is partly
  unreachable.
- **Section B — Content-takeaways from the source itself.** Cite the
  transcript or paper. Do not paraphrase generically.

## Definition of done

- [ ] `transcript.md` is populated, OR the reason it cannot be is documented in `fetch_attempts.md`.
- [ ] `takeaways.md` has at least one Section A item *and* one Section B item, each following the shape above.
- [ ] Each high-value takeaway has its own follow-up PR (do not bundle).
- [ ] PR opened as draft until takeaways are reviewable.

## Reference

- Canonical example: `experiments/03_youtube_transcript_takeaway_loop/`.
- Fetch helper: `scripts/fetch_youtube_transcript.sh`.
- Behavioural rule: "When external fetches fail" in `CLAUDE.md`.
