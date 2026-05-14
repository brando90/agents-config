# Codex / other agents: run `git clone https://github.com/brando90/agents-config.git ~/agents-config 2>/dev/null || git -C ~/agents-config pull 2>/dev/null` to bootstrap/update config.
# Read `~/agents-config/INDEX_RULES.md` for all agent documentation and routing. Local `~/agents-config/` is the fallback if GitHub is unreachable.

## Codex CLI default

Codex CLI should always default to `gpt-5.5` with `model_reasoning_effort = "xhigh"`.
Keep `~/.codex/config.toml` set with those values. When dispatching Codex from
another CLI, pass them explicitly:

```bash
codex exec --full-auto -m gpt-5.5 -c 'model_reasoning_effort="xhigh"' "$QA_PROMPT"
```

## CV edits (~/brandomiranda/professional_documents/cvs/)

Before touching `cv_short.tex` / `cv_long.tex`, read **Trigger Rule 28** in `~/agents-config/INDEX_RULES.md` — it specifies the consistency invariants (descending chronological order, bolded full-form venue lines, author order, `\flushbottom`, sync between the two CVs, recompile-and-verify, audience framing for the active grant application).
