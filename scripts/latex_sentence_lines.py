#!/usr/bin/env python3
"""Reformat LaTeX prose to one sentence per line.

Rule: writing/ml_research/ml_research_writing.md § "LaTeX Source Layout".

The rewrite is whitespace-only: it splits prose lines at sentence ends and
joins hard-wrapped lines inside a paragraph, so the typeset PDF is unchanged.
It never touches the preamble, blank lines, comment lines (or any line holding
a `%`), lines ending in `\\`, `\\verb`/`\\lstinline` lines, display math, or
verbatim/table/figure-drawing environments.

Usage:
    latex_sentence_lines.py FILE.tex [...]           # rewrite in place
    latex_sentence_lines.py --check FILE.tex [...]   # exit 1 if a rewrite is needed

Verify after rewriting: rebuild and diff `pdftotext` output against the old PDF.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKIP_ENVS = {
    "verbatim", "verbatim*", "Verbatim", "lstlisting", "minted", "comment",
    "equation", "equation*", "align", "align*", "alignat", "alignat*",
    "gather", "gather*", "multline", "multline*", "flalign", "flalign*",
    "eqnarray", "eqnarray*", "displaymath", "math", "aligned", "cases",
    "array", "pmatrix", "bmatrix", "tabular", "tabular*", "tabularx",
    "longtable", "tikzpicture", "axis", "algorithmic", "algorithm",
    "thebibliography", "filecontents", "filecontents*",
}

# Lines starting with these commands are layout, not prose: never joined or split.
STANDALONE = {
    "begin", "end", "section", "subsection", "subsubsection", "chapter", "part",
    "label", "includegraphics", "centering", "raggedright", "raggedleft",
    "maketitle", "appendix", "bibliography", "bibliographystyle",
    "printbibliography", "vspace", "vskip", "hspace", "newpage", "clearpage",
    "pagebreak", "input", "include", "newcommand", "renewcommand", "def", "let",
    "usepackage", "setlength", "toprule", "midrule", "bottomrule", "hline",
    "cline", "resizebox", "small", "footnotesize", "scriptsize", "normalsize",
    "captionsetup", "phantomsection", "addcontentsline", "medskip", "smallskip",
    "bigskip", "par", "hfill", "vfill", "FloatBarrier", "tableofcontents",
    "newline", "linebreak", "bibitem",
}

ABBREV = {
    "e.g", "i.e", "vs", "cf", "al", "fig", "figs", "eq", "eqs", "sec", "secs",
    "app", "apps", "tab", "tbl", "approx", "resp", "no", "nos", "dr", "mr",
    "mrs", "ms", "prof", "inc", "jr", "sr", "st", "vol", "pp", "p", "ed", "eds",
    "ch", "def", "thm", "prop", "lem", "alg", "ref", "refs", "ex", "viz",
    "w.r.t", "a.k.a", "ca", "resp", "incl", "est",
}

CLOSERS = set(")]'\"’”")
OPENERS_OK = set("(`$“‘[")
STANDALONE_RE = re.compile(r"\\([A-Za-z]+)\*?")
HEADING_ONLY_RE = re.compile(r"^\\(paragraph|subparagraph)\*?\{.*\}\s*$")


def has_comment(line: str) -> bool:
    """True if the line contains an unescaped %."""
    return re.search(r"(?<!\\)(?:\\\\)*%", line) is not None


def is_standalone(stripped: str) -> bool:
    if stripped.endswith("\\\\") or "\\verb" in stripped or "\\lstinline" in stripped:
        return True
    if HEADING_ONLY_RE.match(stripped):
        return True
    m = STANDALONE_RE.match(stripped)
    return bool(m and m.group(1) in STANDALONE)


def split_sentences(text: str) -> list[str]:
    """Split one paragraph of LaTeX prose at sentence boundaries."""
    parts: list[str] = []
    start = 0
    i = 0
    n = len(text)
    math = None  # "$", "(", "[" while inside inline/display math
    while i < n:
        c = text[i]
        if c == "\\" and i + 1 < n:
            nxt = text[i + 1]
            if math is None and nxt in "([":
                math = nxt
            elif math == "(" and nxt == ")" or math == "[" and nxt == "]":
                math = None
            i += 2
            continue
        if c == "$":
            if math is None:
                math = "$"
            elif math == "$":
                math = None
            i += 1
            continue
        if math is None and c in ".?!":
            j = i + 1
            while j < n and text[j] in CLOSERS:
                j += 1
            if j < n and text[j] == " ":
                k = j
                while k < n and text[k] == " ":
                    k += 1
                if k < n and _starts_sentence(text, k) and not _is_abbrev(text, i, c):
                    parts.append(text[start:j])
                    start = k
                    i = k
                    continue
        i += 1
    parts.append(text[start:])
    return [p for p in parts if p]


def _starts_sentence(text: str, k: int) -> bool:
    ch = text[k]
    if ch.isupper() or ch in OPENERS_OK:
        return True
    return ch == "\\" and not text.startswith("\\\\", k)


def _is_abbrev(text: str, i: int, punct: str) -> bool:
    if punct != ".":
        return False
    j = i
    while j > 0 and not text[j - 1].isspace() and text[j - 1] not in "{(~[":
        j -= 1
    token = text[j:i]
    if not token:
        return False
    if len(token) == 1 and token.isupper():  # an initial, e.g. "B. Miranda"
        return True
    if re.fullmatch(r"(?:[A-Za-z]\.)+[A-Za-z]", token):  # e.g, i.e, U.S, w.r.t
        return True
    return token.lower() in ABBREV


def reformat(src: str) -> str:
    lines = src.split("\n")
    begin = next((i for i, l in enumerate(lines) if l.lstrip().startswith("\\begin{document}")), -1)
    end = next((i for i, l in enumerate(lines) if l.lstrip().startswith("\\end{document}")), len(lines))
    out: list[str] = lines[: begin + 1]

    group: list[str] = []
    indent = ""

    def flush() -> None:
        nonlocal group
        if group:
            joined = " ".join(s.strip() for s in group)
            out.extend(indent + s for s in split_sentences(joined))
            group = []

    skip_env: str | None = None
    skip_depth = 0
    display_end: str | None = None
    for line in lines[begin + 1 : end]:
        stripped = line.strip()
        if skip_env is not None:
            skip_depth += line.count(f"\\begin{{{skip_env}}}")
            skip_depth -= line.count(f"\\end{{{skip_env}}}")
            if skip_depth <= 0:
                skip_env = None
            out.append(line)
            continue
        if display_end is not None:
            if display_end in line:
                display_end = None
            out.append(line)
            continue
        opened = [e for e in re.findall(r"\\begin\{([^}]+)\}", line) if e in SKIP_ENVS]
        if opened:
            flush()
            env = opened[0]
            depth = line.count(f"\\begin{{{env}}}") - line.count(f"\\end{{{env}}}")
            if depth > 0:
                skip_env, skip_depth = env, depth
            out.append(line)
            continue
        if stripped.startswith(("\\[", "$$")):
            flush()
            closer = "\\]" if stripped.startswith("\\[") else "$$"
            if stripped[2:].find(closer) == -1:
                display_end = closer
            out.append(line)
            continue
        if not stripped or has_comment(line) or is_standalone(stripped):
            flush()
            out.append(line)
            continue
        if stripped.startswith("\\item"):
            flush()
        if not group:
            indent = line[: len(line) - len(line.lstrip())]
        group.append(line)
    flush()
    out.extend(lines[end:])
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--check", action="store_true", help="exit 1 if any file needs reformatting")
    args = ap.parse_args()
    dirty = 0
    for path in args.files:
        src = path.read_text()
        new = reformat(src)
        if new == src:
            continue
        dirty += 1
        if args.check:
            print(f"{path}: not one sentence per line")
        else:
            path.write_text(new)
            print(f"{path}: reformatted")
    return 1 if args.check and dirty else 0


if __name__ == "__main__":
    sys.exit(main())
