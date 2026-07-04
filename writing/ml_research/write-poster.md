# write-poster.md — Conference Poster Skill (Stanford beamerposter)

**TLDR:** Reusable, paper-agnostic skill for turning a finished (or draft) paper into a top-tier conference poster. Pass a paper as an arXiv/OpenReview link, a repo path, or a PDF; the skill ingests it, distills it into the six-move poster architecture following Rylan Schaeffer's design rules (motivation / clear intuitive results / takeaway, "make it so stupidly obvious"), builds on [RylanSchaeffer/Stanford-LaTeX-Poster-Template](https://github.com/RylanSchaeffer/Stanford-LaTeX-Poster-Template) (gemini theme, XeLaTeX), compiles, and visually QA's the rendered PDF before delivering.

## When to use this skill

Trigger when the user asks to make, draft, or revise a **poster** for a paper, conference, or workshop. Typical invocation:

> Use the write-poster skill from `~/agents-config/writing/ml_research/`.
> Paper: `<arXiv link | OpenReview link | repo path | PDF path>`
> Venue: `<e.g. ICML 2026 AI4Math workshop>`
> Poster spec (optional): `<size + orientation, e.g. 36×24 in landscape>`
> Output dir (optional): `<where the poster project should live>`

Siblings: [`write-abstract.md`](write-abstract.md), [`write-intro.md`](write-intro.md), and the umbrella guide [`ml_research_writing.md`](ml_research_writing.md) (GitHub fallback: <https://github.com/brando90/agents-config/tree/main/writing/ml_research>). Trigger Rules 23–24 (jargon boundary, audience translation) apply in full — a poster is maximally reader-facing.

## ⚠ Non-negotiables

Governing design philosophy from Rylan Schaeffer (the template's author), WhatsApp 2026-07-03 — full transcript and provenance in [`assets/whatsapp_rylan_poster_advice.md`](assets/whatsapp_rylan_poster_advice.md):

> "Motivation, clear intuitive results, takeaway. People are going to be exhausted when they walk past the poster. Make it so stupidly obvious."

1. **Design for the exhausted walker.** The audience is a tired attendee shuffling past after hours on the poster floor, not a fresh referee at a desk. The main claim must land in ~5 seconds from 2 m (title + highlighted blocks + money figure) — so stupidly obvious that extracting it takes zero effort. A poster is an advertisement for a conversation, not a compressed paper; the full story lives in the paper behind the QR code.
2. **Three essential parts: motivation, clear intuitive results, takeaway.** Each carried by a figure or image wherever possible, not text — huge blocks of text are exhausting to read standing up. Everything else is optional support.
3. **Word budget: ≤ ~800 words total.** Bullets over paragraphs; no paragraph longer than 3 sentences; never paste the abstract verbatim.
4. **CS197 jargon stays in `%` comments** (`bit flip`, `vectoring`, `north star`, ...) — never in rendered poster text. Same rule as the abstract/intro skills.
5. **Compile and LOOK at the render before delivering.** A poster that "should compile" is not a deliverable. The visual QA loop below is mandatory.

## Inputs (interpret from the user's message)

**Required:**
- **Paper source** — one of: arXiv link, OpenReview link, local repo/dir path, single `.tex`, or `.pdf`.
- **Venue** — used for the footer, the poster-size lookup, and tone calibration.

**Optional (ask at most once, then default):**
- **Poster spec** — width × height + orientation. If absent, web-search "`<venue year>` poster dimensions/instructions" (specs change year to year: A0, 24×36 in, 36×48 in, 84×42 in are all common). If still unknown, keep the template default **120×72 cm landscape** and flag the assumption prominently in the reply.
- **Banner color** — default **Cardinal Red banner, white text** (the iconic Stanford look). Repo ships 4 options; the clone's default is Cool Grey — switch it (see mechanics below) unless the user picks another.
- **Output dir** — default `<paper_dir>/../<VENUE>_poster/` next to the paper (e.g. `paper_latex/ICML_2026_AI4Math_poster/`), or `<repo>/poster/` for standalone repos.
- **QR targets** — paper URL and code URL. If neither is given, insert `[TODO: qr-url]` and flag it.
- **Featured figures** — if the user names figures/tables, they win; otherwise pick per the content architecture below.

## Step 1 — Ingest the paper (in this order of preference)

Original `.tex` + figure files beat PDF scraping every time — always try to get source.

1. **arXiv link** → fetch the source tarball first, not the PDF: `curl -L https://arxiv.org/e-print/<id> -o src.tar; mkdir -p src && tar -xf src.tar -C src` (sometimes it's a single gzipped `.tex`; handle with `file src.tar`). This yields the original figure PDFs/PNGs for direct reuse. Fall back to the PDF.
2. **Local repo/dir** → read the abstract, intro, method, and results `.tex` files plus the `figures/` dir directly.
3. **PDF only** → Read it (paged). Extract figures with `pdfimages -all paper.pdf figs/` or rasterize a page region with `pdftoppm -png -r 300 -f <p> -l <p>` + crop (`brew install poppler`); prefer asking for source files if extraction quality is poor.

Extract while reading: title; authors + affiliations; the problem/failure mode; the prior assumption being inverted; the contribution claim; the system/method and its money figure; headline numbers and the one table that carries them; the takeaway; ≤5 essential citations.

## Step 2 — Content architecture (six moves → blocks)

Default 3-column landscape layout (2 columns if portrait). Label each block with a `% CS197 move N` comment. Block titles should be claims, not labels, wherever natural ("LLM provers overclaim on unverified specs" beats "Motivation").

| Column | Blocks | CS197 move |
|---|---|---|
| Left | **Problem / Motivation** (+ 1 setup figure) | 1–2 |
| Left | `alertblock` **Key idea** — the contribution in ≤3 bullets, coined term bolded | 3 |
| Middle | **Method / System** — the money figure, full column width, caption = takeaway sentence | 4 |
| Middle | **Benchmark / Setup** — only what's needed to read the results | 4 |
| Right | **Results** — headline table or plot; the single headline number set big (e.g. `{\Huge 27\%}`) | 5 |
| Right | `alertblock` **Takeaways** — ≤3 bullets, vision-not-self-congratulation | 6 |
| Right | **References** (`\footnotesize`, ≤5 entries) + QR codes (paper, code) | — |

Poster-specific prose rules, on top of the umbrella guide's voice rules:

- For each of the three essential parts — motivation, results, takeaway — first ask: **can a figure or image carry this instead of text?** Default yes; prose is the fallback.
- Figures + tables ≥ ~40% of poster area; whitespace is a feature, not waste.
- Every figure caption states the conclusion ("Compile rate collapses without the judge"), never the description ("Compile rates for all agents").
- Concrete numbers over adjectives; nothing set below `\small`.
- The stupidly-obvious test: title → alertblocks → money figure alone must convey motivation → result → takeaway, with all body text ignored.

| Dimension | Weak poster | Strong poster |
|---|---|---|
| Text | Abstract pasted in, 2,000 words | ≤800 words, bullets, claims as block titles |
| Figures | Paper figures shrunk to fit | 1 money figure at full column width, captions = takeaways |
| Headline | Buried in a dense table | One big number + one plot |
| Walk-by test | Must read intro block to get it | Stupidly obvious: claim lands from title + alertblocks alone |

## Step 3 — Template mechanics

```bash
git clone --depth 1 https://github.com/RylanSchaeffer/Stanford-LaTeX-Poster-Template.git /tmp/stanford-poster
mkdir -p <output_dir> && cp /tmp/stanford-poster/{main.tex,poster.bib,beamerthemegemini.sty,beamercolorthemestanford.sty} <output_dir>/
cp -r /tmp/stanford-poster/stanford_logos <output_dir>/
```

Copy only those files — never the template's `.git/` or `demos/` (megabytes of sample PDFs). Then edit `main.tex`:

- **Size** (`main.tex` preamble): `\usepackage[size=custom,width=<W>,height=<H>,scale=1.0]{beamerposter}` — units are **cm** (36×24 in = 91.44×60.96 cm). Bump `scale` (1.0–1.4) to enlarge all fonts uniformly on smaller posters.
- **Columns**: `(N+1)·\sepwidth + N·\colwidth = \paperwidth`. Template default: 3 columns, sep 0.025, col 0.30. Portrait 2-column: sep 0.03, col 0.455.
- **Banner color** (`beamercolorthemestanford.sty`, the `\setbeamercolor{headline}` lines ~44–47): uncomment exactly one — `bg=cardinalred,fg=white` (default here), `bg=paloaltogreen,fg=white`, `bg=white,fg=cardinalred`, or `bg=coolgray,fg=white`.
- **Header**: `\title`, `\author` with `\inst{}`, `\institute`, `\footercontent{<homepage> \hfill <venue> \hfill <email>}`; logo is the tikz overlay node in the body (`stanford_logos/Block_S_2_color.png` — keep aspect ratio, adjust only `height=`).
- **QR codes**: `\usepackage{qrcode}` + `\qrcode[height=5cm]{<url>}` (pure LaTeX, XeLaTeX-safe). Fallback: `qrencode -o qr.png '<url>'` + `\includegraphics`.
- Blocks: `\begin{block}{...}`, `\begin{alertblock}{...}` for the two highlighted blocks, `\heading{...}` for sub-heads inside a block.

## Step 4 — Compile (XeLaTeX, not pdflatex)

```bash
cd <output_dir> && latexmk -xelatex -interaction=nonstopmode main.tex
```

The gemini theme loads **Raleway** and **Lato** via `fontspec`, so plain `pdflatex` fails. On Overleaf: set Compiler → XeLaTeX. Locally, the classic failure is `! I can't find file 'Raleway'.` — fix in order (steps 1–2 verified end-to-end on Brando's Mac, TeX Live 2024, 2026-07-03):

1. `tlmgr install raleway lato` (full TeX Live already ships both — skip if `find $(kpsewhich -var-value TEXMFDIST)/fonts -ipath '*raleway*' -name '*.ttf'` already hits).
2. On macOS the error persists even with the fonts in texmf (CoreText doesn't index texmf trees). Copy them where the OS looks, then recompile:
   ```bash
   find $(kpsewhich -var-value TEXMFDIST)/fonts \( -ipath '*raleway*' -o -ipath '*lato*' \) \( -name '*.ttf' -o -name '*.otf' \) -exec cp {} ~/Library/Fonts/ \;
   ```
   (Linux: target `~/.fonts/` and run `fc-cache -f`.)
3. Last resort: edit the font lines in `beamerthemegemini.sty` to an installed family (e.g. `\setsansfont{Helvetica Neue}`) and say so in the reply.

Report the actual exit code and error tail, never "should compile".

## Step 5 — Visual QA loop (mandatory, ≥1 pass)

```bash
pdftoppm -png -r 40 main.pdf preview   # then Read preview-1.png and actually look
```

Check, fix, recompile, re-look until clean:

- No text overflowing a column bottom or block edge; no overfull warnings that visibly clip.
- Columns roughly balanced (no column ending > ~15% shorter than its neighbors).
- Title fits on 1–2 lines; authors/institutes don't wrap awkwardly; logo undistorted.
- Fonts actually loaded (a silent fallback to Latin Modern is visually obvious — chunkier serifs in headings).
- Money figure legible at the preview resolution — if you can't read its axis labels at 40 dpi zoomed, a human can't from 1.5 m.
- The stupidly-obvious test passes: cover everything but title + alertblocks + money figure and confirm motivation → result → takeaway still land.

## Deliverable

1. The poster project in `<output_dir>` (`main.tex`, `.sty` files, `figures/`, `poster.bib`) plus compiled `main.pdf` — send the PDF and the PNG preview to the user.
2. A summary in the reply: how the paper mapped to the six moves/blocks, which figures were reused vs. rebuilt, poster size + color used (and whether the size was venue-verified or assumed), any `[TODO: ...]` flags (QR URLs, missing numbers), and `git diff --stat` if committed.
3. Remind the user to proof at 100% zoom before printing — colors and figure DPI on screen lie.
4. Run QA per Hard Rule 3 (a second agent reviews `main.tex` + the rendered preview) before reporting done.
