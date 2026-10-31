---
name: scientific-terminology
description: "One term per concept in ML research writing: define a term once, reuse it exactly, never vary words for style, flag places where two words name one thing, and change a renamed term everywhere. Use for any ML paper, tech report, appendix, research Doc, results update, poster or slide text, and when reviewing AI-written research text."
---

# scientific-terminology: one term per concept

**TLDR:** In research writing, every concept gets one term. Define it once, then reuse that exact word. Do not swap in synonyms to make prose sound varied: this is scientific communication, not an English class. If a term changes, change it everywhere.

## When to use this skill

Load it whenever the work is ML research writing or editing: papers (`.tex`), appendices, tech reports, research Google Docs, result emails and chat updates, posters, slides, review text, and any AI-written draft someone asks you to check. It is also for Brando and Varun's shared papers, so it applies to every agent that touches them.

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

## Why (Brando's words, 10-31-2026)

- "in science, using variations randomly muddies a word and makes it unclear because our language is precise and we reuse the language precisely."
- "If we decided to use the word density, we stick to it, and it's clear what it means. Not vary it in the same sentence to make it sound like good for an English class. This is not an English class. This is scientific communication. It's different."
- "it has to be clear when we're doing this and it has to be loaded. Otherwise, me and Varun will be getting bad AI assistance."
