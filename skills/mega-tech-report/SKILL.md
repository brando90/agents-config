---
name: mega-tech-report
description: Keep one .tex per research result in a repo's LaTeX folder and build them into one chronological mega tech report PDF. Open it (Rule 93) when you finish, report or update a result in a research repo, start numbering experiments, or are asked for "the tech report", "all results" or "the whole record".
---

# Mega tech report

**Doc link:** <https://github.com/brando90/agents-config/blob/main/skills/mega-tech-report/SKILL.md>

**TLDR:** Each result is one fragment `latex/results/NN_<slug>.tex`; `build_mega_report.py` regenerates `mega_tech_report.pdf` from all of them, ordered by the day each result first landed on `main`. Brando, 11-24-2026 ([Rule 93](../../rules/research.md#trigger-rule-93)).

As of 11-24-2026. First tested in `brando90/trustworthy-theorem-judges` (`latex/`, results of experiments 16, 22, 25 and 27).

## Layout in a research repo

```
latex/                        the repo's report LaTeX folder (an existing one is reused)
  mega_preamble.tex           shared packages and macros (copied from templates/, then repo-owned)
  mega_tech_report.tex        the mega document; never lists results by hand
  mega_meta.tex, mega_results.tex   generated: do not edit
  mega_tech_report.pdf        the whole record of results, committed
  results/
    _TEMPLATE.tex             copy of templates/result_template.tex (files starting with _ are skipped)
    NN_<slug>.tex             one result each: header lines, then the body
```

## Steps

1. First time in a repo: `python3 ~/agents-config/skills/mega-tech-report/build_mega_report.py --latex-dir latex --init`.
2. Copy `results/_TEMPLATE.tex` to `results/NN_<slug>.tex` (NN = the experiment's number, [Rule 88](../../rules/research.md#trigger-rule-88) folder names). Fill the five header lines. `result-date` is the day the result first landed on `main`: `git log --follow --format=%cI -- <results.md> | tail -1`; add `result-time`, so two results on one day keep their order.
3. Write the body from the experiment's `results.md` ([Rule 92](../../rules/research.md#trigger-rule-92) layout): bottom line, table (RPS, CE, TVD first; Spearman and Pearson last and secondary), caveats, appendix with harness and model, links to `results.md`, the Google Doc and the commit. Wrap wide tables in `\FitWidth{...}`. Copy numbers from `results.md`; then check every number token of the `.tex` appears in its source.
4. `python3 .../build_mega_report.py --latex-dir latex` rebuilds the PDF (`--check` lists the order without compiling; `--single NN` builds one result alone into `single_*.tex/pdf`, which you delete after reading: never commit them). Read the PDF pages before you report.
5. Commit the `.tex` files and the PDF to `main` with the `results.md`; the message carries the Doc, commit and PDF links.

## Rules of the order

- Chronological = result-date, then result-time, then NN. A re-run of a result is a dated "Update" subsection of its file; a different result from the same experiment is a new file.
- In a public repo no rater names, emails or rater-level rows go into a `.tex`.
- Fix a wrong date in the header, never by renaming files to force an order.
