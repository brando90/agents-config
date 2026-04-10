# Claude Code: read `~/agents-config/INDEX_RULES.md` for all agent documentation and routing.
# If `~/agents-config/` is not present, clone it: `git clone https://github.com/brando90/agents-config.git ~/agents-config`

## Mandatory Response Protocol (inline — do not skip)

These are duplicated here from INDEX_RULES.md Hard Rules so you see them at session start without needing to dereference. They apply to EVERY response in EVERY session.

1. **TLDR** — End every response with `**TLDR:**` (1-2 sentences). No exceptions.
2. **QA gating** — Before reporting a non-trivial task as "done," run the two-step QA chain (Hard Rule 3 in `~/agents-config/INDEX_RULES.md`). When unsure whether to run it, run it.
3. **No secrets** — Never commit secrets. Review diffs before pushing.
4. **Fresh config** — At the start of each new task, `git -C ~/agents-config pull` and re-read `~/agents-config/INDEX_RULES.md`.
