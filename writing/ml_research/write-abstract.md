# write-abstract.md — CS197 Six-Move Abstract Skill

**TLDR:** Reusable, paper-agnostic skill for writing the abstract of a top-tier ML / CS paper using the CS197 (Stanford) six-move bit-flip architecture compressed to ~150 words. Pass a title and free-form rough ideas (and optionally a draft path for context); the skill produces a first draft plus 2–3 alternate openings to choose from.

## When to use this skill

Trigger when the user asks for help drafting or revising the **abstract** of a research paper aimed at NeurIPS, ICML, ICLR, Nature, Science, or similar top venues. Typical invocation:

> Use the write-abstract skill from `~/agents-config/writing/`.
> Title: `<paper title>`
> Rough ideas: `<free-form paragraph or notes about the paper>`
> Draft path (optional, for context): `<path to draft directory, .tex file, or .pdf>`
> Output path (optional): `<where to write the abstract>`
> Write me a first draft.

This skill is a sibling of [`~/agents-config/writing/ml_research/write-intro.md`](write-intro.md) and [`~/agents-config/writing/ml_research/ml_research_writing.md`](ml_research_writing.md) (GitHub fallback: <https://github.com/brando90/agents-config/blob/main/writing/ml_research/ml_research_writing.md>); load those if the user is working on adjacent sections or wants the broader writing-voice and LaTeX-rules guide. This file is specifically about the **abstract section's structure**.

## ⚠ Jargon boundary (CS197 terms)

This skill uses bit-flip vocabulary internally to scaffold the abstract. **Never put any of those terms in the actual abstract text** — `bit flip`, `the bit`, `flip the bit`, `vectoring`, `(research) velocity`, `north star`, `killer demo`. They're planning shorthand between you and Brando, not reviewer-facing language. Allowed as `% LaTeX comment` to guide structure (e.g., `% move 3: flip the bit`). Not allowed in body prose, sentences, or anything a reviewer reads. See `INDEX_RULES.md` Trigger Rule 23.

## Required and optional inputs (interpret from the user's message)

**Required:**
- **Title** — the paper's title (or working title).
- **Rough ideas** — free-form text describing what the paper is, the problem, the approach, the results pitch. May be a paragraph, a bulleted list, or unstructured notes. Do not require structure.

**Optional:**
- **Draft path** — directory, single `.tex` file, or `.pdf`. Used for context (existing abstract, related work, results). Auto-detect:
  - Directory → `ls -la`, read existing abstract file (commonly `00_abstract.tex` or `abstract.tex`) for prior framing, then revise / replace in place.
  - Single `.tex` file or `.pdf` → read for context only; write to stdout or the user-specified output path.
- **Output path** — where to write the abstract. If draft is a directory, default to the existing abstract file. Otherwise default to writing inline in the response (no file output).

## Read inputs in this order before writing

1. **Title and rough ideas.** This is the authoritative source for what the paper is about. Extract:
   - the problem being solved
   - the prior assumption being inverted (the bit)
   - the new idea (the flip)
   - the concrete system or method (the instantiation)
   - the evaluation pitch
   - the broader implications

   If any of these are missing from the rough ideas, ask the user ONCE or fill with a `[TODO: ...]` flag and proceed.

2. **Draft path (if provided).** Read the existing abstract for prior framing, the introduction for context, related-work / bib for terminology consistency. Trust the rough ideas over the existing abstract — the rough ideas are the current direction.

3. **Sanity check the project.** If the rough ideas mention terminology absent from the draft (or vice versa), surface this discrepancy in your reply but do not block on it — abstracts evolve faster than the rest of the paper.

## Architecture: six moves, ~150 words total

The abstract is the same six-move scaffold as the intro, but compressed to ~1–2 sentences per move instead of one paragraph each.

1. **Problem motivation (1–2 sentences).** Name the failure mode or problem **directly in sentence 1**. No "In recent years" buildup. The reader should know what's broken before the end of the first sentence — this is the Sanmi rule, the highest-leverage edit in abstract writing.

2. **Set up the bit / prior assumption (often folded into sentence 1 or 2).** What's the implicit assumption in prior work that this paper inverts? Sometimes named explicitly ("Existing benchmarks rely on..."), sometimes implied by the problem statement.

3. **Flip the bit (1 sentence, with pivot word).** "We introduce X," "We show that Y," "Here we present Z." Use a clear verb that announces the contribution. Pivot word ("However," "We instead," "In contrast") often helpful but not mandatory.

4. **Instantiate the bit flip (1–2 sentences).** Name the system. State the concrete mechanism that realizes the idea. This is where memorable terminology lives — coined terms, named metrics, distinctive technical mechanisms.

5. **Evaluation (1 sentence with concrete numbers).** Pull headline numbers from the rough ideas or draft. Format like "Models achieve X% on metric A but only Y% on metric B, exposing <key gap>." If numbers aren't yet known, write `[TODO: X% → Y% drop]` rather than vague placeholders like "[key finding]".

6. **Broader perspective / implications (1 sentence).** State the vision, not self-congratulation. Avoid "for the first time… genuinely trustworthy" framing — that reads as marketing. Prefer "moving <field> from <old state> to <new state>" framing.

## Voice

- Active voice: "We introduce," "We show," "Here we present."
- Every sentence must earn its place at NeurIPS / ICML / ICLR / Nature.
- Concrete numbers > vague adjectives.
- No filler, no hedging, no throat-clearing.
- Style check: would a NeurIPS / Nature editor cut this sentence? Specifically avoid:
    (a) "In recent years / decades" openings
    (b) Hedging stacks ("it could potentially be argued that")
    (c) Hype adjectives without numbers ("revolutionary," "groundbreaking")
    (d) Self-congratulatory closings ("for the first time… genuinely trustworthy")
- Avoid overclaiming "first" unless the rough ideas clearly support it.
- The Feynman test: if the reader doesn't learn something new in every sentence, they stop reading. Cut sentences that don't teach.

## Quality bar (Sanmi / Brando comparison lessons)

| Dimension      | Weak version                                                            | Strong version                                                                    |
|----------------|-------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| Opening        | Taxonomy of failure modes (3 sentences)                                 | Names the failure mode in 1 sentence                                              |
| Hook           | Reader knows what's new at line 7                                       | Reader knows what's new at line 1                                                 |
| Metric         | Mentioned only in body                                                  | Named in the abstract                                                             |
| Memorable term | None                                                                    | A coined term ("verification hallucinations," "Mirage emergent abilities")        |
| Finding        | Placeholder ("[key finding]")                                           | Concrete: "X% → Y% drop"                                                          |
| Closing        | Self-congratulatory ("for the first time… genuinely trustworthy")        | Vision: "from <old> to <new>"                                                     |

Aim for the strong version on every dimension.

## Length target

~150–200 words for NeurIPS / ICML / ICLR style (single paragraph). Up to ~250 words for Nature-style structured summary. If the user specifies a venue, calibrate accordingly. If the rough ideas suggest a different venue convention, ask once.

## Iteration expectation

Abstracts get rewritten *many* times. After producing the first draft, also produce 2–3 alternate single-sentence variants of move 1 (problem motivation) so the user can pick the strongest hook. Label them:

- "Opening A: failure-mode-first"
- "Opening B: contrast-first"
- "Opening C: question-first"

## File-writing notes

- If writing to a `.tex` file, wrap output in `\begin{abstract} ... \end{abstract}`.
- If the file already had a `\begin{abstract}` block, replace its contents rather than appending.
- If writing to `.md` or stdout (no output path), use plain prose (no LaTeX wrapping).
- Do NOT delete the existing abstract file. Edit in place.
- Do NOT compile — abstract changes are usually iterated many times before compile is worth running. The user will compile when ready.

## Deliverable

1. **Primary first draft** of the abstract (~150 words), written inline in the response or to the output path / detected abstract file if provided. Do NOT paste the full contents in your reply if you wrote it to a file — show only `git diff --stat` and the first / last few lines.
2. **2–3 alternate openings** (single-sentence variants of move 1), labelled as above.
3. **A summary** in the reply containing:
   1. how the rough ideas mapped to the six moves,
   2. any `[TODO: ...]` flags inserted and why,
   3. any terminology choices worth flagging (coined terms, named metrics) so the user can reuse them consistently elsewhere in the paper,
   4. if a draft path was provided and the abstract was written to a file: `git diff --stat <abstract_path>`.
