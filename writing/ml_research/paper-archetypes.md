# Paper archetypes (templates for ML research papers)

**Doc link:** <https://github.com/brando90/agents-config/blob/main/writing/ml_research/paper-archetypes.md>

**TLDR:** Reference summary of Neel Guha's eight machine learning (ML) paper templates. Pick the template early (it shapes the research, not only the write-up), name it in the paper's planning doc, and do not force a mismatched template.

**Source:** [Templates for Machine Learning Research Papers](https://neelguha.github.io/blog/2026/templates/) by Neel Guha. Sanmi Koyejo flagged it (03-25-2026) as a good prescriptive framework. Ported 10-26-2026 from branch `claude/review-paper-archetypes-BAsGF` (summary written 04-13-2026); read the post itself before quoting it.

## The eight templates

| # | Template | Core idea |
|---|----------|-----------|
| 1 | **Data artifact** | New dataset/benchmark that reveals insights existing benchmarks miss. |
| 2 | **Horse race** | Exceptional empirical results on a credible, recognized benchmark (e.g., AlexNet, BERT). |
| 3 | **New paradigm** | Fundamentally different way of doing something; hardest to execute; can launch subfields. |
| 4 | **Resurrected baseline** | A simple baseline solves problems that complex methods address (e.g., LIMA). |
| 5 | **Unification** | Hidden connections across seemingly different methods; demands mathematical rigor. |
| 6 | **Problem solving** | Workhorse template: identify specific technical challenges, solve each distinctly, combine. |
| 7 | **Discovery** | Answer an important open question previous work could not (e.g., Chinchilla scaling laws). |
| 8 | **Countervailing wisdom** | Challenge community consensus; rare because computer-science culture avoids public disagreement. |

## Key advice from the post

- Successful papers follow formats the community recognizes; papers that deviate feel "off" to reviewers even when they cannot say why. "Doing research and writing your research are inextricable": choose the template early, not at the end.
- Choose templates that genuinely fit the contributions; do not force mismatches.
- New-paradigm papers must say that the evaluation criteria are changing, so reviewers do not judge by old standards.
- Problem-solving papers should show how each challenge is solved individually, not one solution for everything.
- Start writing early; translating research into a template reveals gaps and opportunities.
- The author notes the list reflects his own biases and publication history.

## How to use it here

- When starting or reframing a paper (Trigger Rule 13), state which template(s) the paper follows in its planning doc or `README.md`, and keep the abstract/introduction (Trigger Rules 21-22) consistent with that choice.
- Mixed contributions: name the primary template and treat the others as supporting evidence rather than co-equal claims.
- Open follow-ups: discuss the templates as a group and decide which fit current projects; consider folding template guidance into [`ml_research_writing.md`](ml_research_writing.md) once the lab has tried it on a draft.
