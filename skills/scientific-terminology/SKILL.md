---
name: scientific-terminology
description: "One term per concept in ML research writing: define a term once, reuse it exactly, never vary words for style, flag places where two words name one thing, and change a renamed term everywhere. Use for any ML paper, tech report, appendix, research Doc, results update, poster or slide text, and when reviewing AI-written research text."
---

# scientific-terminology: one term per concept

**TLDR:** In research writing, every concept gets one term. Define it once, then reuse that exact word. Do not swap in synonyms to make prose sound varied: this is scientific communication, not an English class. If a term changes, change it everywhere.

## When to use this skill

Load it whenever the work is ML research writing or editing: papers (`.tex`), appendices, tech reports, research Google Docs, result emails and chat updates, posters, slides, review text, and any AI-written draft someone asks you to check. It is also for Brando and Varun's shared papers, so it applies to every agent that touches them. If the paper's repo has its own AGENTS.md with a term table, read it too: it holds that paper's chosen terms and wins over this list for that paper.

## Rule

1. **One term per concept.** Pick the term when the concept first appears. Define it once, with units or type when it is a quantity (for example "per-token probability mass" vs "density": say which and why).
2. **Reuse it exactly.** The same word in the abstract, the method, the tables, the figure captions, the appendix, the code and the chat update. No "mass" in one place and "density" in another for the same quantity. No "amount", "level", "degree" or "score" as a stand-in for a defined term.
3. **No synonym variation for style.** AI drafts drift toward varied wording because it reads as "good writing" in an English class. In a paper it muddies the word, because readers take a different word to mean a different thing.
4. **Two words, two concepts.** If two terms are both needed, define how they differ. If they name the same thing, delete one.
5. **Changing a term means changing it everywhere.** Search every file of the paper (all `.tex` sections, appendix, captions, tables, figure labels, README, code comments, the notes Doc) and replace each use; then search again for the old word.
6. **Standard terms of the field stay.** Words with an agreed meaning in the literature (for example "advantage", "leave-one-out") are used as the field uses them, and are not renamed or paraphrased.
7. **Flag, do not silently fix, when unsure.** When two words seem to name one thing, list the places (file, line, both words) and suggest the one to keep. Brando or the first author picks, except for plain slips.

## Step by step

1. Before drafting or editing, list the paper's key terms (quantities, metrics, methods, splits, objects) from its existing text.
2. While writing, use only those terms. Introduce a new term only with its definition.
3. Before finishing, run the check: `grep -rniE "<candidate synonyms>"` over the paper sources for each key term, and read each hit. For a whole paper, also read the abstract, one table caption and the appendix side by side for drift.
4. Report in the update: the terms used, any place where two words named one thing and which you kept, and any term you changed with the list of places.

## Dictionary: LLM wording to avoid, standard ML term

AI drafts use words ML readers do not use (often borrowed from biology, clinical trials or spreadsheets). Brando, 10-31-2026: "arm" and "cell" "need to be in our dictionary to human, LLM to human translations so that I understand the language that you use, my AIs use." Use the standard term; this list grows, so add a row when Brando names a new word. Rows added Oct 31, 2026 (15:30) from his word list on the RL environment paper; that paper's own choices (quadrant, covariates, learning signal per token, mixed-group rate) are in its AGENTS.md at https://github.com/brando90/rl-env-scaling.

| LLM wording | Use instead |
|---|---|
| arm (of an experiment) | variant, setting, condition, or the method's name |
| cell (of a results grid) | table entry, quadrant, or option (name the row and column) |
| contract (of a training setup) | configuration (verifier, loss mask, clipping, KL setting), or name the settings |
| protocol (of a procedure) | procedure, algorithm, or evaluation setup; say what it does |
| coordinates (of model inputs) | covariates or features (scaling-law papers say covariates) |
| utility (of a training run) | gain, return or reward: name the quantity (for example "held-out pass@1 gain") |
| points (of a metric change) | name the metric and unit: "percentage points (pp) of pass@1", or relative error |
| signal (bare) | learning signal (name what it is a signal for) |
| trainer (as the algorithm) | RL optimization algorithm, optimizer, or its name (GRPO); "trainer" is a library class |
| untouched (data or scale) | held-out (prompts, scale, split) |
| calibration (informal, "refit") | refit or re-estimate; "calibration" only for predicted probabilities or interval coverage matching outcomes |
| compact (of a model) | state the fact: "N-parameter", "five-coefficient", or "simple"; "compact" has a precise meaning in analysis |
| frozen (of coefficients or a split) | "fixed before X, not refit"; say when it was fixed |
| uniform mixture | equally weighted mixture |
| envelope, audit, admitted/admission, stress test | error band; evaluation or check; unmasked or selected; test |

If you meet any of these words in a draft, replace it with the standard term and keep that one term for the concept everywhere (rule 5).

## Why (Brando's words, 10-31-2026)

- "in science, using variations randomly muddies a word and makes it unclear because our language is precise and we reuse the language precisely."
- "If we decided to use the word density, we stick to it, and it's clear what it means. Not vary it in the same sentence to make it sound like good for an English class. This is not an English class. This is scientific communication. It's different."
- "it has to be clear when we're doing this and it has to be loaded. Otherwise, me and Varun will be getting bad AI assistance."
