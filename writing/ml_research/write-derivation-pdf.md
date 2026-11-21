# Derivation PDF for maths requests (Trigger Rule 91)

Date: 11-21-2026

**TLDR:** When Brando asks for maths, a derivation or equations, he gets a LaTeX-typeset PDF with the detailed derivation, not plain-text maths. The `.tex`, `.md` and `.pdf` live in the project's GitHub experiment folder on main and in his Google Drive. Source: Brando, 11-21-2026: "we should create an ac rule for pdfs maths. I always want to receive something like this, ideally with a detailed derivation."

## Structure of the PDF

1. **Title and date** (`MM-DD-YYYY`), project and experiment folder.
2. **What this shows and does not show** (top of page 1, plain words plus equations): the claim, the assumptions, and the limits of the metric or loss: which moments or features it can learn (for example only first moments, only linear features), what it cannot see, when it is blind. Brando, 11-21-2026: "that should be super explicit".
3. **Notation table**: every symbol, its type and meaning. Define each symbol again where it first appears in the derivation.
4. **Derivation**: every step shown, one equation per line, the justification of each step beside it, final formulas boxed.
5. **Per-term table** when a loss or metric has several terms: term, what it measures, gradient or effect, what it can and cannot learn.
6. **Results and checks**: numeric sanity checks and the experiment that tests any claim that one loss or method beats another (also at limited data). An untested claim is labelled untested.
7. **Sources**: which repo files, runs or papers each number came from.

## Delivery

- **GitHub:** `<experiment folder>/<NAME>_<MM-DD-YYYY>.{tex,md,pdf}` committed to main (no branch, no PR). In the `.md`, use GitHub math (`$...$`, `$$...$$`) and open it on GitHub to check that it renders.
- **Drive:** upload the same three files (the PDF first) into the project's Drive folder; share each as anyone-with-the-link, comment access; if comment access fails, view.
- **Google Docs:** equations are real Docs equations or images rendered from the LaTeX; never plain text or raw LaTeX.
- **Check before sending:** compile with `pdflatex` (twice), render every page with `pdftoppm -r 80 -png`, look at each page (nothing cut off, symbols defined), open the Drive link, then send the PDF link first and the Doc and GitHub links as they are ready.
