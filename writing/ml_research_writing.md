# ML Research Paper Writing Guide

**When to load:** Any time you edit `.tex` files for an ML research paper (NeurIPS, ICML, ICLR, etc.).

---

## Writing Persona

You are a top ML researcher writing for elite venues (NeurIPS, ICML, ICLR). You aim for best paper awards and long-term impact. Write:

- **Crisply** — every sentence earns its place
- **Active voice** — "We introduce X" not "X is introduced"
- **Scientifically** — precise claims, grounded in evidence
- **Persuasively but not bombastically** — let the work speak; no self-congratulatory language
- **Concisely and professionally** — respect the reader's time

---

## Core Principle: Challenging Assumptions

<!-- "Bit flip" is CS 197 teaching jargon for this concept. Use it ONLY as
     internal shorthand / LaTeX comments (% bit flip: ...) to organize your
     thinking.  NEVER write "bit flip" in actual paper prose. The published
     text must read as normal professional scientific writing. -->

A good heuristic for structuring an impactful contribution:

> Identify a widely held assumption in prior work → show why it is wrong or incomplete → introduce your approach that overturns it.

This assumption-inversion is the narrative spine of the paper. Use it to plan structure (e.g., `% assumption to challenge: ...` comments in `.tex`), but the prose itself should simply present the problem, the gap, and your solution in clear, professional language — no meta-commentary about "flipping" anything.

---

## Abstract Writing

The abstract is critical — Title + Abstract may be all people read. Apply the Feynman Test: if the reader doesn't learn something new immediately, they won't read on.

### The 6-Point Abstract Structure

Each point gets 1–2 sentences in the abstract (vs. a full paragraph in the intro):

1. **Problem motivation:** State the problem and why it matters. Optionally why it hasn't been solved.
2. **Prior assumption / gap:** Identify the assumption or limitation in prior work that your paper challenges.
3. **Your contribution:** Introduce your novel idea that addresses the gap. Lead with surprise — immediate hook, not a slow multi-sentence buildup.
4. **Approach / solution:** Describe how your solution concretely works. Factual, comprehensive, extremely succinct/direct.
5. **Evaluation:** Briefly mention your evaluation method and key result. Use concrete numbers, not placeholders.
6. **Implications:** Broader perspective and significance. Vision, not self-congratulation.

### Abstract Tactics (Before → After)

| Element | Weak | Strong |
|---|---|---|
| **Hook** | Multi-sentence taxonomy before reader knows what's new | Line 1 — immediate surprise |
| **Metric** | Not mentioned until body | Named in abstract ("multiplicative evaluation metric") |
| **Finding** | Placeholder: "[key finding]" | Concrete: "X% → Y% drop" |
| **Memorable term** | None | Coin a term ("verification hallucinations") |
| **Closing** | "For the first time… genuinely trustworthy" (self-congratulatory) | "From X to Y" (vision statement) |
| **Length** | Too detailed for 30-second scan | Punchier, direct |

### References

- [Stanford paper writing tips — Abstract](https://cs.stanford.edu/people/widom/paper-writing.html#abstract)
- [Nature summary paragraph guide](https://www.nature.com/documents/nature-summary-paragraph.pdf)
- [arXiv:2304.15004](https://arxiv.org/abs/2304.15004)
- [VeriBench paper_latex/](https://github.com/brando90/veribench/tree/main/paper_latex) — original source for this guide's examples and structure

---

## Introduction Writing

The intro expands the same 6-point structure from the abstract, dedicating a full paragraph to each point:

1. **Problem motivation** — full paragraph establishing the problem and its importance
2. **Prior assumption / gap** — paragraph on what prior work assumes or misses
3. **Your contribution** — paragraph introducing your novel idea
4. **Approach / solution** — paragraph on your concrete method
5. **Evaluation** — paragraph on methodology and key findings
6. **Implications** — paragraph on broader impact and significance

---

## General LaTeX Writing Rules

- **One sentence per line** in `.tex` source — makes diffs clean and reviews easier.
- **Use `\textsc{}` for system/benchmark names** (e.g., `\textsc{VeriBench-DT}`).
- **Use `\emph{}` for key terms** on first introduction (e.g., *verification hallucinations*).
- **Concrete over vague** — replace "significant improvement" with "12.3% improvement."
- **Cut filler** — remove "It is worth noting that," "In this paper, we," "It should be noted."
- **Avoid orphan references** — don't start sentences with bare citations like "[23] shows..."
- **Use `~` (non-breaking space)** before `\cite{}` and `\ref{}`: `Section~\ref{sec:method}`.

---

## Overleaf-Style Local Workflow

For local LaTeX editing with live preview (Cursor / VS Code):

1. Install **MacTeX**: `brew install --cask mactex`
2. Install the **LaTeX Workshop** extension
3. Open a `.tex` file — **save to compile**, `Cmd+Alt+V` to open PDF preview side-by-side

> **Tip:** If LaTeX Workshop doesn't find the root file, add `% !TEX root = main.tex` at the top of any sub-file.
