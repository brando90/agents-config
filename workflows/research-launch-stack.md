# Workflow: Research Launch Stack
**TLDR:** Use this workflow when Brando asks for a Kesh-style paper launch, publicity package, project page, tweprint, blog post, or "PR/advertisement" stack. The goal is to turn a paper repo into a coordinated launch bundle: project website, tweet thread, blog-ready prose, saved links, figures/media, and a reviewable artifact trail.

This workflow generalizes the pattern in Keshigeyan Chandrasegaran's research launches: a sharp public hook, concrete scale numbers, polished project page, artifact links, visual results, and a thread/blog/site that all point to each other. Copy the structure and craft, not the wording or assets.

---

## Trigger Phrases

Use this workflow when the user says anything like:

- "Make a Kesh-style launch for this paper."
- "Create PR/advertisement stuff for my paper."
- "Make a tweprint + website + blog for this paper."
- "Copy Kesh's style for this release."
- "Create the full launch stack."
- "Make a project page like HourVideo / Grafting / GPIC."

Also load `~/agents-config/workflows/tweprints.md` for the X thread. Load `~/agents-config/workflows/blog-posts.md` for a SAIL/lab-style post, or `~/agents-config/writing/blog/` for Brando's personal blog.

---

## Reference Stack

Save these as links and style references. Do not mirror whole third-party sites into a repo unless the user explicitly asks and the license/permission story is clear.

- Kesh profile: https://keshik6.github.io/
- HourVideo project page: https://hourvideo.stanford.edu/
- HourVideo teaser: https://keshik6.github.io/videos/hourvideo_teaser.mp4
- HourVideo thread: https://x.com/keshigeyan/status/1863652813668225040
- Grafting project page: https://grafting.stanford.edu/
- Grafting blog: https://www.liquid.ai/blog/exploring-diffusion-transformer-designs-via-grafting
- GPIC project page: https://gpic.stanford.edu/
- GPIC thread: https://x.com/keshigeyan/status/2060398262591668315
- GPIC arXiv: https://arxiv.org/abs/2605.30341
- GPIC dataset: https://huggingface.co/datasets/stanford-vision-lab/gpic

Use the references for structural analysis:

1. Lead with the named artifact and category.
2. Surface scale numbers before deep explanation.
3. Put paper/code/data/site/thread/blog links in obvious buttons.
4. Make the first screen visually legible: title, authors, affiliations, links, hero visual.
5. Include an "at a glance" or equivalent visual summary.
6. Show benchmark/results sections as scannable modules.
7. End with BibTeX, acknowledgments, and reusable artifact links.

---

## Output Bundle

For a serious paper launch, produce these artifacts in the target paper repo:

1. `launch/<YYYY_MM_DD>/launch_brief.md`
   - one-page source-of-truth with title, claims, numbers, links, target audience, release status, coauthor handles, and asset checklist.
2. `tweets/<MM_DD_YYYY>/<paper>_tweprint.txt`
   - 4-8 tweet thread, all tweets <=280 characters, Kesh-style hook when appropriate.
3. Project website under the repo's hosting convention.
   - Usually `docs/index.html` for GitHub Pages repos.
   - If an app framework exists, use the existing framework instead.
4. Blog draft when requested.
   - Put it where the repo already keeps posts, or under `launch/<date>/blog_draft.md`.
5. `launch/<date>/links.md`
   - saved canonical links: paper, code, data, project site, thread, blog, demos, videos, figures.
6. `launch/<date>/asset_manifest.md`
   - source figure paths, generated screenshots, videos, thumbnails, alt text, and license/permission notes.

Do not post to X or publish externally without an explicit user instruction at the final step. Draft and stage the launch; keep publishing human-confirmed unless the user has already authorized authenticated posting/deployment.

---

## End-To-End Procedure

1. **Find the repo shape.**
   - Inspect `README`, `docs/`, paper files, figures, build scripts, package metadata, and existing website/blog conventions.
   - If the repo is a GitHub Pages static site, expect `docs/index.html`, `docs/assets/`, and `docs/figs/`.

2. **Extract the launch facts.**
   - Read the abstract, intro, main result tables, figures, and release notes.
   - Build a claim table with exact numbers and source file paths.
   - Mark uncertain claims as TODOs instead of inventing numbers.

3. **Write the launch brief first.**
   - One page, title + TLDR, core audience, key contribution, 3-5 headline numbers, artifact links, coauthor handles, visual plan, and release status.

4. **Build the website like a project page, not a generic blog.**
   - First viewport: project name, literal category, authors, affiliations, action links, and a real figure/video/interactive artifact.
   - Next sections: abstract/TLDR, at-a-glance graphic, benchmark/task/result modules, artifact links, BibTeX, acknowledgments.
   - Use the target repo's existing visual system unless it is clearly broken.
   - Verify desktop and mobile rendering with the Browser/Playwright workflow whenever possible.

5. **Draft the Kesh-style tweprint.**
   - Hook format: named artifact + category, dense scale numbers, compact score/result block, named gap, thread opener.
   - Use figures/media from the website; do not treat the thread as text-only.
   - Save source links and local media notes, but keep third-party raw/media copies out of Git unless permitted.

6. **Draft the blog if requested.**
   - Use the blog workflow for the target outlet.
   - Cross-link the project page and tweprint.
   - Prefer explanatory narrative over paper-section recitation.

7. **Tie the stack together.**
   - Website links to paper/code/data/blog/thread.
   - Thread final tweet links to website/paper/code/data.
   - Blog links to website and thread.
   - Launch brief links to every artifact and TODO.

8. **Verify and QA.**
   - Static site: run a local server, open the page, inspect screenshots at desktop and mobile widths.
   - Docs: check title + TLDR, link inventory, figure paths, character limits, and source-grounding.
   - Run the repo's QA protocol before commit/push.

---

## First Pilot: VeriBench Blog Repo

The first target for this workflow is `ehersch/veribench-blog`.

Observed repo shape:

- GitHub repo: https://github.com/ehersch/veribench-blog
- Local clone path used in the first setup pass: `/Users/sanmikoyejo-mba-1/veribench-blog`
- Static GitHub Pages convention: `docs/index.html`, `docs/assets/site.css`, `docs/figs/`
- Existing page already has VeriBench figures and an interactive example; the launch-stack pass should make it feel more like HourVideo/Grafting: stronger hero, clearer action buttons, at-a-glance benchmark numbers, linked tweprint/blog assets, and a saved launch brief.

For this repo, the likely deliverables are:

1. Update `docs/index.html` and `docs/assets/site.css`.
2. Add `launch/<date>/launch_brief.md`.
3. Add `tweets/<date>/veribench_kesh_style_tweprint.txt`.
4. Add `launch/<date>/links.md` and `asset_manifest.md`.
5. Preview with a local static server and screenshots before committing.

---

## Safety And Attribution

- Do not copy Kesh's wording, HTML, CSS, screenshots, or media wholesale.
- Use public examples as inspiration and cite/save links.
- If raw third-party JSON/media is downloaded for local study, ignore it in Git unless permission is explicit.
- For claims, always link back to exact paper/source files.
- For generated visuals, record the prompt/source and make sure rights are clear.
