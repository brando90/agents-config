# write-intro.md — CS197 Six-Move Introduction Skill

**TLDR:** Reusable, paper-agnostic skill for writing the Introduction section of an ML / CS paper using the CS197 (Stanford) six-move bit-flip architecture. Pass an abstract path and a draft path; the skill auto-detects edit-in-place vs context-only mode and writes a first draft.

## References (origin conversations)

These are the source conversations that produced this skill — kept for traceability, not required reading:

- Claude: <https://claude.ai/chat/3fa66124-cdc8-4c5e-9072-cfe9344c6c0e>
- ChatGPT (VeriBench Code2FormalBench project): <https://chatgpt.com/g/g-p-67a52d2e317c8191b791da7851248040-veribench-code2formalbench/c/69faadd9-1e4c-83e8-ae2b-d8d192a1ab2b>
- Gemini: <https://gemini.google.com/app/9508861b8d1d20c1>

## When to use this skill

Trigger when the user asks for help drafting or revising the **Introduction** section of a research paper aimed at NeurIPS, ICML, ICLR, Nature, Science, or similar top venues. Typical invocation:

> Use the write-intro skill from `~/agents-config/writing/`.
> Abstract: `<path to abstract file>`
> Draft: `<path to draft directory or file>`
> Write me a first draft.

This skill is a sibling of [`~/agents-config/writing/ml_research_writing.md`](ml_research_writing.md) (GitHub fallback: <https://github.com/brando90/agents-config/blob/main/writing/ml_research_writing.md>); load that file too if you need the broader writing-voice and LaTeX-rules guide. This file is specifically about the **introduction section's structure**.

## Required inputs (interpret from the user's message)

- **Abstract path** — file path to the finished / current abstract (`.tex` or `.md`). The user will name this explicitly.
- **Draft path** — path to current paper draft. The skill auto-detects:
  - Directory (e.g., `<repo_root>/paper_latex/NeurIPS_2026_VeriBench/`) → **edit-in-place mode**. Find the existing intro file in the directory and revise it.
  - Single `.tex` file → context-only. Read for context, write fresh.
  - `.pdf` file → context-only. Extract context from PDF, write fresh.

## Read inputs in this order before writing

1. **Abstract file.** The intro's six paragraph topic sentences should each make the same claim as a sentence in the abstract — recognizable but not a near-paraphrase.
2. **Draft path.**
   - If directory: run `ls -la <draft_dir>`. Read the existing intro file (revise in place, do not rewrite blind), `<draft_dir>/related_work.tex` for citations, the bib file for valid keys, `<draft_dir>/main.tex` for preamble / packages, and any results tables / figures referenced.
   - If single file: read for context. Write a fresh intro to a path matching the directory's naming convention (e.g., if abstract is `<draft_dir>/00_abstract.tex`, intro goes in `<draft_dir>/01_intro.tex`).
3. **Project context.** Confirm what project this is. Look at the abstract's claims, the draft's title and prior intro, and the surrounding directory. If terminology in the abstract appears to belong to a different paper than the draft suggests (e.g., the abstract introduces a metric or system name absent from the draft, or the draft is for a clearly different project), STOP and report the conflict before writing.
4. If the abstract and existing intro conflict on framing or contributions, **trust the abstract** — it is the current direction.

## Architecture: six moves, ~one paragraph each (~80–150 words)

Each paragraph has a topic sentence stating the claim, then 2–5 supporting sentences with citations for every factual claim. Treat the topic sentence as the thesis the paragraph must prove. Do not stray.

1. **Problem motivation.** Sentence 1 names the problem directly — no "In recent years" buildup. Motivate why the problem matters with evidence / citations. End by explaining why the problem isn't solved (sets up paragraph 2).

2. **Set up the bit (prior assumption).** Identify the SINGLE shared assumption across prior work that this paper inverts. Focused mini related-work summary in service of the bit flip — NOT a survey. Cite only papers that share the inverted assumption.

3. **Flip the bit (conceptual contribution).** Begin with a pivot — "However," "In contrast," "We instead." State the contribution at the conceptual level. State the idea before naming the system.

4. **Instantiate the bit flip (concrete solution).** Name the system. Describe how it concretely realizes the idea from paragraph 3. Reference the main figure. This is where memorable terminology lives.

5. **Evaluation.** State the evaluation protocol and headline numbers. Pull numbers ONLY from the abstract or results in the draft — do not invent. If a number is missing, write `[TODO: exact number from <source>]`.

6. **Implications + contributions.** State what changes in the field if this work succeeds. End with a bullet `\begin{itemize}` contributions list. If an existing contributions list exists in the prior intro, refine it rather than rewriting from scratch.

## Voice

- Active voice: "We introduce," "We evaluate," "We show."
- Every factual claim gets a citation. No exceptions.
- Concrete numbers > vague adjectives.
- Style check: would a NeurIPS / Nature editor cut this sentence as filler, hype, or vague? If yes, rewrite. Specifically avoid:
    (a) "In recent years / decades" openings
    (b) Hedging stacks ("it could potentially be argued that")
    (c) Hype adjectives without numbers ("revolutionary," "groundbreaking")
    (d) Abstract metaphors where a concrete noun would do
- Avoid overclaiming "first" unless `<draft_dir>/related_work.tex` clearly supports it.

## Citation discipline

- Only use BibTeX keys that exist in the draft's bib file. Before each `\cite{}`, grep the bib file to confirm the key exists.
- Never invent BibTeX keys.
- For required-but-missing citations, use `\todocite{describe what's needed}` and ensure this preamble line exists in `<draft_dir>/main.tex` (add if missing):
  `\providecommand{\todocite}[1]{\textcolor{red}{[CITE: #1]}}`
  If `xcolor` is not loaded in `<draft_dir>/main.tex`, fall back to:
  `\providecommand{\todocite}[1]{\textbf{[CITE: #1]}}`
- Missing citations must be visually flagged in the rendered PDF, not silently broken.

## Compilation and git workflow

### Edit-in-place mode (`--draft` is a directory)

- Do NOT delete the existing intro file. Edit in place. Git tracks the diff.
- Detect the build command in this order:
  1. `Makefile` or repo-root `Makefile` with a paper target
  2. `.latexmkrc` or `latexmkrc`
  3. fallback: `cd <draft_dir> && latexmk -pdf main.tex`
- The intro is included via `\input{...}` — do NOT compile the intro fragment standalone.
- Confirm exit code 0, no "Undefined control sequence" errors, no "Citation undefined" warnings beyond `\todocite{}` flags.
- Show the final 30 lines of the compile log.
- If compilation fails: fix the error, or revert with `git checkout <intro_path>` and report the exact error.

### Context-only mode (`--draft` is a single file)

- Write a fresh intro to the inferred output path.
- Verify by inspection: balanced braces, matching `\begin` / `\end`, no empty `\cite{}`, no markdown fencing, all `\todocite{}` macros defined.
- State explicitly that you did NOT compile.

## First-draft semantics

If the user asks for a "first draft" or it's clear this is early-stage writing:

- Use `\todocite{...}` liberally for citations you're not confident about
- Use `[TODO: ...]` for missing numbers, figure references, or details
- Don't block on missing details — flag them and keep writing

## Genre constraint (default)

Default to "old problem, new solution" — the most common and lowest-risk genre. If the abstract or existing draft clearly indicates otherwise, follow that.

## Deliverable

1. The intro written in place (directory mode) or to inferred path (file mode). Do NOT paste its contents in your reply.
2. A summary in your reply containing:
   1. which abstract sentences map to which intro paragraphs,
   2. any `\todocite{}` flags inserted and why,
   3. compile status (success / failure with log tail, or inspection-only),
   4. `git diff --stat <intro_path>` if in directory mode.
