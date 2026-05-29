---
name: research-launch-stack
description: Create a Kesh-style research launch bundle for a paper, dataset, benchmark, or project. Use when Codex is asked for a paper launch stack, PR/advertisement package, tweprint plus website, project page like HourVideo/Grafting/GPIC, blog-ready release draft, saved launch links, asset manifest, or an end-to-end publishing/promo workflow from a LaTeX paper or research repo.
---

# Research Launch Stack

Turn a paper repo into a coordinated launch package: project page, Kesh-style tweprint, optional blog draft, saved links, figure/media manifest, and a reviewable launch brief.

## Quick Start

1. Read the target repo instructions first, then inspect the paper source, README, figures, existing website/blog conventions, and release status.
2. Load `references/kesh-style-launch.md` when you need the saved Kesh/HourVideo/Grafting/GPIC examples, output schema, and style checklist.
3. Build a source-grounded launch brief before drafting public copy. Every headline number or claim must point to a paper/source file.
4. Produce the bundle in the target repo's convention:
   - `launch/<YYYY_MM_DD>/launch_brief.md`
   - `launch/<YYYY_MM_DD>/links.md`
   - `launch/<YYYY_MM_DD>/asset_manifest.md`
   - `tweets/<MM_DD_YYYY>/<paper>_tweprint.txt`
   - project page updates, usually `docs/index.html` for GitHub Pages repos
   - optional `launch/<YYYY_MM_DD>/blog_draft.md`
5. Verify the artifacts before commit: markdown title/TLDR, saved links, source-grounded claims, tweet character counts, figure paths, local website render where applicable, and the repo's normal QA.

## Operating Rules

- Copy Kesh's craft, not his wording, HTML, CSS, screenshots, or media.
- Save third-party reference links, but do not commit raw third-party downloads unless permission is explicit.
- Do not post to X, deploy a website, or publish externally without final user authorization.
- If facts are missing, write `TODO(source needed): ...` instead of inventing a number.
- For LaTeX papers, prefer `00_abstract.tex`, `01_introduction.tex`, evaluation/result sections, figure references, and the compiled PDF as the first fact sources.
- For websites, preserve the repo's existing framework and visual language unless the page is clearly a placeholder.

## VeriBench Pilot

For the first VeriBench paper launch test, use:

- Paper source: `~/veribench/paper_latex/NeurIPS_2026_VeriBench`
- Experiment folder convention: `~/veribench/experiments/<NN>_<name>/`
- Blog/project-site pilot repo: `~/veribench-blog`

Start by creating an experiment folder in `~/veribench/experiments/` that records the source paper path, launch goals, reference links, output checklist, and exact prompt a future agent should run with this skill.
