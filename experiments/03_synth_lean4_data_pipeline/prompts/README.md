# Prompts — Versioning Discipline

**TLDR:** Every prompt revision lives in its own file `vN_<short_name>.md` with a YAML frontmatter recording why it changed, which CLI / model it was tested with, and what was wrong with the previous version. Asked for explicitly by Eshaan in `#emb` Discord on 2026-05-10 1:47pm.

## Why per-file versioned prompts

The prompt is the most-modified, highest-leverage artifact in this experiment. Without a discipline:

- Subtle changes drift undocumented (e.g., "added line about `native_decide` because v3 was using it for non-trivial proofs" → no record of *why*)
- Prompts get re-tuned for whichever agent the author happened to be using (claude-code vs codex vs gemini-cli) without recording the target — making a prompt that's "good for codex" silently broken when run on `gemini-3-pro-preview`
- Reverts are painful — `git log` shows the change but not the reason

## Frontmatter schema

Every `vN_<short_name>.md` MUST start with:

```yaml
---
parent: vN-1_<short_name>      # or `null` for v0
date: YYYY-MM-DD
author: <human name | agent id>
agentic_cli: <claude-code | codex | clauded | gemini | other>
model_tested: <claude-sonnet-4-6 | gemini-3-pro-preview | gpt-5.5-xhigh | ...>
problem: "What was wrong with the parent version that motivated this change?"
rationale: "Why this specific change is the right fix."
diff_summary: "1-line summary of what changed (additions, deletions, restructure)."
source_url: <optional, if mirrored from another repo>
local_source: <optional, e.g. ~/lean-ebm/experiments/claude_prompt.md>
---
```

Then the prompt body follows after a `---` separator.

## Naming

- `v0_<short_name>.md` — initial version (parent: null)
- `v1_<short_name>.md`, `v2_<short_name>.md`, … — successive revisions
- `<short_name>` is a 1-3-word slug describing what's distinctive about this version (e.g., `tighter_skip_rules`, `add_proof_retries`, `gemini_specific_phrasing`)

## Updating without forking

For tiny edits (typo, single line) you can edit the latest version in place and just bump its `date` field. For anything that meaningfully changes behavior (new section, removed section, retuned numerical thresholds, different downstream agent target) — make a new `vN+1` file.

When in doubt, fork. Disk is cheap; lost rationale isn't.

## Pointer to the active version

The driver script (`scripts/run_pipeline.py`) reads from a symlink `prompts/active.md → prompts/vN_<short_name>.md`. Bumping the active version is one `ln -sf` away. Each pipeline run logs the resolved active version into its result records so we can later correlate "which records came from which prompt."

## See also

- Eshaan's 2026-05-10 1:47pm Discord ask (in `#emb`): "as we change the prompts I assume you are using some agentic coding agent. I recommend we write document the reasons for the prompt change. Eg what problems are we solving with potentially a rationale of your chosen solution. […] Tldr; can we document this going forward? Let me know if you need clarifications."
- Parent design: [`../PLAN.md`](../PLAN.md) § Prompt Strategy
