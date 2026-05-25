# Claude Code: run `git clone https://github.com/brando90/agents-config.git ~/agents-config 2>/dev/null || git -C ~/agents-config pull 2>/dev/null` to bootstrap/update config.
# Read `~/agents-config/INDEX_RULES.md` for all agent documentation and routing. Local `~/agents-config/` is the fallback if GitHub is unreachable.

## Behavioral Rules

- **Just do it** — When Brando gives a direct instruction (send email, run command, etc.), execute it immediately. Do not ask for confirmation, offer alternatives, or create drafts when "send" was requested. Only pause for truly destructive/irreversible actions on shared systems.
- **No unnecessary drafts** — If told to "send" an email, send it. Only create a draft if explicitly asked for a draft.

## Mandatory Response Protocol (inline — do not skip)

These are duplicated here from `~/agents-config/INDEX_RULES.md` so you see the highest-priority rules at session start without needing to dereference. Hard Rules apply to EVERY response in EVERY session; triggered rules apply when their stated condition is met.

1. **Dual TLDR (top + end)** — Open every response with `**TLDR-start:**` and close with `**TLDR-end:**` (1–2 sentences each). The top one is a fast preview so the user sees a summary in prefix-s / collapsed view. The bottom one is authoritative: write it last, from the actual response content, **ignoring what `TLDR-start` said**. Do not copy-paste between them; if the reasoning in the response changed your conclusion, `TLDR-end` should reflect that. If only one is present, it must be `TLDR-end`. No exceptions.
2. **Verification snapshot** — Immediately after `TLDR-end`, append a `**Snapshot:**` block: ~5–15 lines (cap 25) of the *smallest representative sample of actual artifacts* (rows from a generated dict, file path + size + head/tail, commit URLs, diff --stat, etc.) so the user can visually confirm the work was done. Not a TLDR rewrite. For intangible tasks, show a one-line before/after or a cited file:line. If truly nothing: `**Snapshot:** _(nothing to show — reason)_`.
3. **QA gating** — Before reporting a non-trivial task as "done," run the two-step QA chain (Hard Rule 3 in `~/agents-config/INDEX_RULES.md`). When unsure whether to run it, run it.
4. **No secrets** — Never commit secrets. Review diffs before pushing.
5. **Fresh config** — At the start of each new task, `git -C ~/agents-config pull` and re-read `~/agents-config/INDEX_RULES.md`.
6. **LaTeX writing** — When editing `.tex` files for ML research papers, read `~/agents-config/writing/ml_research/ml_research_writing.md` first. Follow its persona, abstract structure, and writing rules.
7. **Agent CLI freshness** — `SessionStart` in `~/.claude/settings.json` calls `~/agents-config/scripts/auto-update-tools.sh`. Major CLIs: `codex`, `claude` / `clauded`, `gemini`. Example extras: Cursor, Mistral, Harmonic, Axiom, and similar installed tools. If one looks stale, use the right package manager or print the exact update command.
8. **Codex default model** — Codex CLI should always default to `gpt-5.5` with `model_reasoning_effort = "xhigh"`. Keep `~/.codex/config.toml` set with those values, and when dispatching Codex from Claude use `codex exec --full-auto -m gpt-5.5 -c 'model_reasoning_effort="xhigh"' "$QA_PROMPT"`.
9. **CLI-only for LLM calls** — Never *author* and never *silently execute* direct LLM-provider API calls (`anthropic`, `openai`, `litellm`, `google.genai`, raw HTTP to `api.anthropic.com` / `api.openai.com` / `generativelanguage.googleapis.com`). Route all LLM-driven work through `clauded -p` / `codex exec` / `gemini` — they use subscription/OAuth auth and self-throttle. Only Brando may write API-calling code. Before executing any existing script that loads `~/keys/anthropic_*` / `~/keys/openai_*` / `~/keys/gemini_*` / `~/keys/aristotle_*`, pause and surface script path + estimated spend, then wait for explicit confirmation. **Why:** a silent agent default burned $17,752.98 in May 2026 on `anthropic_bm_key_koyejolab` — the lab cannot absorb that scale of spend. Full text: `~/agents-config/INDEX_RULES.md` Hard Rule 9.
