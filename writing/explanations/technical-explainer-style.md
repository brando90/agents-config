# Technical Explainer Style

**Doc link:** <https://github.com/brando90/agents-config/blob/main/writing/explanations/technical-explainer-style.md>

**TLDR:** House style for teaching documents — explainers, notation references, derivation walkthroughs, onboarding notes. Bolded claim-sentences carry the argument, `\boxed{}` marks definitions and results, and `\underbrace{}_{\text{plain English}}` annotates terms in place. Explicitly **not** for paper prose: Trigger Rule 13 governs there, and several rules below directly conflict with it.

---

## When to load

Load this doc when the deliverable's job is to **make Brando (or a reader) understand something**, not to ship in a venue:

- Explaining a concept, algorithm, or derivation in chat or in a `.md` file
- Notation references and translation tables between conventions
- Walkthroughs of a paper's method, including his own papers
- Onboarding docs, internal teaching notes, "how does X actually work" answers
- Any answer where he asks to "explain in detail" or says he doesn't know a term

## When NOT to load

Do **not** apply this style to:

| Artifact | Governing rule instead |
|---|---|
| `.tex` paper prose, abstracts, captions | Trigger Rule 13 → [`writing/ml_research/ml_research_writing.md`](../ml_research/ml_research_writing.md) |
| Posters | Trigger Rule 30 → [`write-poster.md`](../ml_research/write-poster.md) |
| SAIL / lab blog posts | Trigger Rule 31 |
| Tweet threads, LinkedIn posts | Trigger Rules 32, 33 |
| Commit messages, PR descriptions | Trigger Rule 7 |

**The conflict is real, not cosmetic.** `\boxed{}`, `\underbrace{}`, second person, and TL;DR blocks all read as lecture notes to an ICLR reviewer. A doc written in this style must be rewritten, not lightly edited, on the way into a paper.

---

## The two mechanics that carry the style

Everything else follows from these.

**1. Every section opens with a bolded full sentence that states a claim, not a label.** The test: a reader who reads *only* the bold sentences, skipping all body text and every equation, should still get the complete argument. Bare-noun headings (`## Advantage`, `## Background`) cannot pass that test and are banned.

**2. Equations annotate themselves.** Use `\underbrace{...}_{\text{plain English}}` so the reader never looks away from the formula to find a legend. The annotation is prose, not another symbol.

---

## Prose rules

- **Bolded claim-sentence opens each section.** Full sentence, assertion, own paragraph.
- **Paragraphs are 1–3 sentences**, one idea each. Whitespace does the pacing.
- **Pivot between sections with a question the reader would actually ask**, then answer it. "Now ask: was that observed return good for the state we were in?" An equation that arrives after a question is motivated; one that arrives after a heading is merely announced.
- **Second person, present tense, active voice.** "You run the current policy, observe the rewards, take a gradient step."
- **Gloss every new symbol in plain English within one sentence of first appearance.** Composes with Hard Rule 10 (expand acronyms and jargon on first use in every response).
- **Announce notation collisions out loud, with the reason.** "I'm using $R_t$ rather than the common $G_t$ so that $G$ stays the group size." This is the single strongest trust signal in the style: it proves the writer is tracking the *reader's* symbol table, not just their own.
- **Pair every general formula with a concrete numeric micro-example** using small numbers verifiable in the head. Two actions with $Q = 10, 4$ giving $V = 7$ and advantages $\pm 3$ beats a paragraph of interpretation.
- **Give the obvious objection its own bolded question.** "Why is this legitimate?" then the proof.
- **Bold has exactly two jobs:** the section-opening claim, and 3–8 word key distinctions inside a paragraph. Never scattered for emphasis.
- **`**TL;DR:**` goes at the bottom, never the top.** It compresses what was just read. (Distinct from Trigger Rule 16's file-level `**TLDR:**` header, which is a *summary* of a document the reader has not read yet. A long explainer carries both: the Rule 16 header at the top, the compression at the bottom.)

---

## Equation rules

- **Display math on its own line, blank lines around it.** Nothing containing a sum, fraction, integral, or expectation goes inline.
- **`\boxed{}` on definitions and final results only** — roughly one per section. The boxes are what a reader would copy onto a cheat sheet. Never box intermediate algebra.
- **`\underbrace{}_{\text{...}}` with English underneath**, not symbols. Good: `\underbrace{f_\theta(o_t \mid \cdot)}_{\text{probability under the policy being updated}}`. Bad: `\underbrace{f_\theta}_{\pi_\theta}`.
- **Sandwich every equation:** one sentence before saying what it does, one after saying what it means. No orphans.
- **`\begin{aligned}` for derivation chains**, so equalities stack vertically and the argument reads downward.
- **Inline math only for single bare symbols** in running prose — $G$, $R_t$, $\theta^+$ — each glossed at first appearance.
- **Tables show the arithmetic, not just the result:** `10-7=+3`, not `+3`.
- **Number a step when the derivation has more than two moves** ("Step 1 — the log-derivative trick", "Step 2 — the dynamics cancel"), and name the move rather than describing it.

---

## Antipatterns

| Antipattern | Fix |
|---|---|
| Bare-noun heading (`## Advantage`) | Bolded claim sentence (`**Advantage is the gap between one action and your policy's own average.**`) |
| Wall of prose between equations | Break into 1–3 sentence paragraphs |
| Symbol legend placed after the equation | Move it inside, as `\underbrace` |
| Boxing every equation | One box per section, definitions and results only |
| Restating the question before answering | Start with the answer |
| Inline $\sum$ or $\frac{}{}$ in running prose | Display it |
| Introducing notation and explaining it three paragraphs later | Gloss on first use |
| Silently renaming a symbol the reader already uses | Say you're renaming it and why |

---

## Before / after

**Before:**

> ## Advantage Functions
>
> The advantage function is defined as $A^\pi(s,a) = Q^\pi(s,a) - V^\pi(s)$ where $Q^\pi$ is the state-action value function and $V^\pi$ is the state value function. It measures the relative benefit of an action. It is widely used in policy gradient methods for variance reduction purposes.

**After:**

> **Advantage is the gap between one specific action and your policy's own average at that state.**
>
> $$
> \boxed{
> A^\pi(s,a)
> \;\triangleq\;
> \underbrace{Q^\pi(s,a)}_{\substack{\text{take } a \text{ now,}\\ \text{then follow } \pi}}
> \;-\;
> \underbrace{V^\pi(s)}_{\substack{\text{follow } \pi \\ \text{from the start}}}
> }
> $$
>
> Both terms you already know. Since $V^\pi(s) = \sum_a \pi(a \mid s) Q^\pi(s,a)$, the advantage is mean-zero under your own policy — you cannot beat your own average on average.

---

## Reusable prompt block

Paste this when dispatching an explainer to another agent, or when Brando wants the style applied in a fresh chat.

```
Write this explanation in the following style.

STRUCTURE
- Open each section with a bolded full sentence stating the takeaway as a
  claim, not a label. A reader who reads only the bold sentences should get
  the complete argument.
- Paragraphs are 1-3 sentences, one idea each.
- Pivot between sections with a question the reader would actually ask,
  then answer it.
- Close with a "TL;DR:" of 2-4 sentences. Never open with it.

PROSE
- Second person, present tense, active voice.
- Gloss every new symbol in plain English within one sentence of its first
  appearance.
- If you rename a symbol to avoid clashing with notation I already use, say
  so explicitly and say why.
- Pair every general formula with a concrete numeric micro-example using
  small numbers I can verify in my head.
- Anticipate the obvious objection and answer it under its own bolded
  question.
- Use bold for exactly two things: section-opening claims, and 3-8 word key
  distinctions inside a paragraph. Nothing else.

EQUATIONS
- Display math on its own line with blank lines around it. Never inline
  anything containing a sum, fraction, integral, or expectation.
- Wrap definitions and final results in \boxed{}. About one box per section.
  Never box intermediate algebra.
- Annotate terms inside equations with \underbrace{...}_{\text{plain English}}.
  The annotation is prose, not a symbol.
- Sandwich every equation: one sentence before saying what it does, one
  after saying what it means. No orphaned equations.
- Use \begin{aligned} for derivation chains so the equalities stack.
- In tables, show the arithmetic, not just the result (e.g. "10-7=+3").

AVOID
- Bare-noun headings.
- Walls of prose between equations.
- Symbol legends placed away from the equation they explain.
- Restating my question before answering it.
```

---

## Composition with other rules

- **Hard Rule 10** (expand acronyms and jargon on first use) is a strict superset of the glossing rule here. Both apply.
- **Trigger Rule 16** (document header: `# Title`, `**Doc link:**`, `**TLDR:**`) applies to any explainer written to disk. That top TLDR is a summary; the bottom TL;DR is a compression. Both.
- **Trigger Rules 23–24** (CS197 jargon; audience-calibrated terminology) apply here too. An explainer is reader-facing prose even when the reader is Brando.
- **Trigger Rule 13** is mutually exclusive with this doc. If a task turns out to be paper prose, drop this style entirely rather than blending the two.

---

## Provenance

Brando identified this style on 09-20-2026 from a GPT-6 explanation of advantage functions and REINFORCE, and asked for it to be captured as a reusable house style with a trigger rule that keeps it out of paper prose.
