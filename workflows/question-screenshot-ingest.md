# Workflow: Q Go Screenshot Question Ingest
**TLDR:** When the user sends screenshots with the exact trigger phrase `Q go`, preserve the images, transcribe the handwritten question, create a numbered root-level `questions/<NN>_<slug>/` packet, open a GitHub issue, run Mega QA, commit, push to `main`, and verify the remote ref. This workflow turns rough screenshot questions into durable experiment-ready research prompts without touching unrelated dirty files.

## Trigger

Use this workflow when the user sends one or more screenshots and includes the
phrase `Q go`.

Default target is the current project repo. If the repo has no `questions/`
folder, create one at the repo root.

## Required Directory Shape

Create the next sequential folder:

```text
questions/
├── README.md
└── <NN>_<short_slug>/
    ├── README.md
    ├── transcription.md
    ├── pre_prompt.md
    ├── PROTOCOL.md
    ├── coding_agent_prompt.md
    ├── issue.md
    └── assets/
        ├── photo_1.jpg
        └── photo_2.jpg
```

Use `00_`, `01_`, and so on. Keep source image filenames stable and boring:
`photo_1.jpg`, `photo_2.jpg`, etc.

## Required Content

- `questions/README.md`: index of all question packets, trigger reminder, and
  link to the GitHub issue for each packet.
- Packet `README.md`: compact goal, confidence, importance, source artifact
  paths, file list, and GitHub issue link.
- `transcription.md`: direct transcription of handwriting plus uncertainty
  notes. For copyrighted printed material, preserve equations and short context
  but summarize long prose instead of copying full passages.
- `pre_prompt.md`: sharpened research interpretation and future-agent plan.
- `PROTOCOL.md`: locked scientific question, metrics, pass/fail criteria,
  preconditions, abort rules, and deliverables before any expensive run.
- `coding_agent_prompt.md`: paste-ready prompt for implementing `expt_v1/`.
- `issue.md`: concise GitHub issue body with source artifacts, compact question,
  tasks, and deliverable.

Every generated markdown file must start with `# Title` and a `**TLDR:**`
block.

## GitHub Issue

Open one GitHub issue in the current repo from `issue.md`.

After creating the issue:

1. Update the packet `README.md` with the issue URL.
2. Update `questions/README.md` with the issue URL.
3. If useful, update `coding_agent_prompt.md` with the issue URL.

## QA And Publish

Run Mega QA at the end because the trigger request usually asks for durable
research scaffolding, not a scratch note.

Before committing:

1. Inspect `git status --short`.
2. Stage only files created or edited for the `Q go` request.
3. Review staged diff for secrets, unrelated changes, bad paths, and broken
   markdown links.
4. Run relevant lightweight checks, at minimum:
   - `git diff --check --cached`
   - file existence checks for all saved images and generated markdown files
   - markdown/link sanity checks if available

Then commit and push to `main`. After pushing, verify:

```bash
git fetch origin main
git rev-parse HEAD
git rev-parse origin/main
```

Report the commit SHA, issue URL, saved image paths, and final QA result.

## Guardrails

- Do not stage or modify unrelated dirty files.
- Do not overwrite an existing numbered question folder.
- Do not run multi-GPU or expensive experiments during ingest; create the
  protocol and prompt only.
- If a central `~/agents-config/` checkout is dirty, use a clean worktree from
  `origin/main` for config edits.
- If direct push to `main` is rejected, push a branch and report the exact
  blocker.
