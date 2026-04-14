# Claude Code: run `git clone https://github.com/brando90/agents-config.git ~/agents-config 2>/dev/null || git -C ~/agents-config pull 2>/dev/null` to bootstrap/update config.
# Read `~/agents-config/INDEX_RULES.md` for all agent documentation and routing. Local `~/agents-config/` is the fallback if GitHub is unreachable.

## Behavioral Rules

- **Just do it** — When Brando gives a direct instruction (send email, run command, etc.), execute it immediately. Do not ask for confirmation, offer alternatives, or create drafts when "send" was requested. Only pause for truly destructive/irreversible actions on shared systems.
- **No unnecessary drafts** — If told to "send" an email, send it. Only create a draft if explicitly asked for a draft.

## Mandatory Response Protocol (inline — do not skip)

These are duplicated here from `~/agents-config/INDEX_RULES.md` so you see the highest-priority rules at session start without needing to dereference. Hard Rules apply to EVERY response in EVERY session; triggered rules apply when their stated condition is met.

1. **TLDR** — End every response with `**TLDR:**` (1-2 sentences). No exceptions.
2. **QA gating** — Before reporting a non-trivial task as "done," run the two-step QA chain (Hard Rule 3 in `~/agents-config/INDEX_RULES.md`). When unsure whether to run it, run it.
3. **No secrets** — Never commit secrets. Review diffs before pushing.
4. **Fresh config** — At the start of each new task, `git -C ~/agents-config pull` and re-read `~/agents-config/INDEX_RULES.md`.
5. **LaTeX writing** — When editing `.tex` files for ML research papers, read `~/agents-config/writing/ml_research_writing.md` first. Follow its persona, abstract structure, and writing rules.
