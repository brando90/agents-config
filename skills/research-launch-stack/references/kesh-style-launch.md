# Kesh-Style Launch Reference
**TLDR:** Use this as the detailed reference for `$research-launch-stack`: saved exemplar links, output bundle contract, style heuristics, and verification checklist. It supports Kesh-style paper launches without copying third-party wording or assets.

## Reference Links

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

## Launch Pattern

1. Lead with the named artifact and literal category: benchmark, dataset, system, model, or method.
2. Surface scale and result numbers early.
3. Show the capability gap or practical pain point in one compact block.
4. Put paper, code, data, site, thread, blog, and demo links in obvious places.
5. Make the first screen visually legible: title, authors, affiliations, buttons, and a real figure/video/interactive artifact.
6. Include an "at a glance" summary before dense details.
7. End with BibTeX, acknowledgments, artifact links, and reuse instructions.

## Output Bundle

Create the following, adjusted to the target repo:

- `launch/<YYYY_MM_DD>/launch_brief.md`: source-of-truth for title, one-sentence hook, claims, numbers, source paths, audience, release status, coauthor handles, and TODOs.
- `launch/<YYYY_MM_DD>/links.md`: canonical saved links for paper, code, data, project site, thread, blog, demos, videos, figures, and reference examples.
- `launch/<YYYY_MM_DD>/asset_manifest.md`: local figure/video paths, generated screenshots, alt text, license/permission notes, and source provenance.
- `tweets/<MM_DD_YYYY>/<paper>_tweprint.txt`: 4-8 tweets, each <=280 characters, with media notes and source links.
- Website/project page: use the repo's hosting convention, usually `docs/index.html`.
- Optional blog draft: put it in the repo's post convention or `launch/<YYYY_MM_DD>/blog_draft.md`.

## Safety Checklist

- Do not copy third-party HTML/CSS/media or screenshots.
- Do not commit raw downloaded X/oEmbed/video/media artifacts unless permission is explicit.
- Do not publish/post/deploy without final authorization.
- Do not claim paper numbers without source paths.
- Mark uncertain claims as TODOs.

## Verification Checklist

- `git diff --check`
- Markdown title + TLDR for new docs.
- `links.md` includes every external source used.
- Tweet character counts are <=280.
- Figure/media paths in `asset_manifest.md` exist or are marked TODO.
- Website renders locally on desktop and mobile if website files changed.
- Repo-specific QA passes before commit/push.
