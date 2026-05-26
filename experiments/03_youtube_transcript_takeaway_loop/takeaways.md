# Takeaways — Improvements to `agents-config`

**Scope note.** The original ask was "main takeaways from the talk to improve this
repo." Since the transcript could not be fetched (see `fetch_attempts.md`), the
takeaways below are split into two clearly labelled sections:

- **Section A — Meta-takeaways from the *attempt*** (concrete; tied to files in
  this repo; can be acted on today).
- **Section B — Placeholders for content-takeaways** (to be filled once
  `transcript.md` is populated).

---

## Section A — Meta-takeaways from the fetch attempt

### A1. Add a "talk-distillation" experiment template

The repo has `experiments/experiment_template_readme.tex` aimed at ML-research
experiments (Objective / Hypothesis / Dataset / Metric). It does not fit
"distil a talk or paper into repo changes." Today every video/talk experiment
will reinvent the layout.

**Concrete change:** add `experiments/experiment_template_talk_distill.md`
with the structure used in this folder (README + metadata.json + fetch log +
fetch script + transcript.md + takeaways.md), so the next talk-to-takeaways
loop is `cp -r` away.

### A2. Promote `fetch_transcript.sh` to `scripts/`

Right now `fetch_transcript.sh` lives inside this experiment. Every future
experiment that wants to ingest a YouTube talk will copy-paste it.

**Concrete change:** move the script to `scripts/fetch_youtube_transcript.sh`
once it is shown to work from a non-blocked machine, and reference it from the
talk-distillation template. Keep the experiment-local copy as a thin wrapper
that calls the shared one.

### A3. Codify the "external fetch is blocked" failure mode in `CLAUDE.md`

When an agent cannot reach an external resource, the correct behaviour is
(a) log the attempts, (b) capture whatever metadata *is* reachable (oEmbed
worked here), (c) build the rest of the deliverable as a skeleton, and
(d) ask the user for the missing piece — never fabricate. The current
`CLAUDE.md` does not say this anywhere.

**Concrete change:** append a "When external fetches fail" bullet to the
Mandatory Response Protocol in `CLAUDE.md` (or in `INDEX_RULES.md` if it
lives there), with the four-step pattern above. Reference this experiment as
the canonical example.

### A4. Cache oEmbed metadata before the transcript step

`https://www.youtube.com/oembed` and `https://noembed.com/embed` were the only
two YouTube endpoints that *did* answer. They give title, channel, thumbnail
— enough to start an experiment folder even when the transcript itself is
out of reach. The template should fetch oEmbed *first* so the experiment
folder is partially populated even on a total transcript failure.

**Concrete change:** add an `oembed` step to the talk-distillation script
that always runs and always writes `video_metadata.json`, independent of
whether the transcript fetch succeeds.

### A5. Add `WebFetch` allow/deny notes for known-blocked hosts

The repo's `.claude/settings.json` could pre-allow the oEmbed hosts (so the
permission prompt is skipped on read-only metadata calls) and document which
YouTube paths are known not to work from this sandbox so future Claude sessions
don't burn time rediscovering it. The `fewer-permission-prompts` skill is the
right place to add this.

**Concrete change:** run `/fewer-permission-prompts` after this PR merges and
add `WebFetch(https://www.youtube.com/oembed*)` and
`WebFetch(https://noembed.com/*)` to the project allowlist; leave a comment
that direct `youtube.com`, `googlevideo.com`, and `youtu.be` fetches are
blocked from cloud IPs.

---

## Section B — Content takeaways (TODO)

To be filled once `transcript.md` is populated. Each item should follow this
shape so it is actionable, not generic:

> **Claim from talk (≤2 sentences, with timestamp):**
> **What in the repo it touches (file:line or section):**
> **Proposed change (concrete diff or new file):**
> **Why it is worth doing (1 sentence):**

Speaker context (from public profiles, not the talk itself — to be confirmed
against the transcript): Vishnu Ravi works on Stanford Spezi (open-source
modular framework for digital health apps), LLM-based EHR querying, and
AI-driven care platforms. Plausible themes likely to appear in the talk and to
have parallels in this repo:

- **Modular, standards-based composition** (Spezi's design philosophy) →
  parallels to how `~/agents-config` composes hooks, skills, and agents. Look
  for advice on module boundaries, versioning, or capability declaration.
- **LLM-on-EHR evaluation methodology** → parallels to the QA-gate experiment
  (`experiments/00_refactor_qa_gate/`). Look for evaluation patterns,
  hallucination-mitigation tactics, or human-in-the-loop checkpoints.
- **Open-source health-tooling governance** → parallels to how this repo
  manages its own self-improving config (`todo_self_improving_agents_config.md`).

Re-read the transcript with the above hooks in mind and replace this section
with specific, cited items.
