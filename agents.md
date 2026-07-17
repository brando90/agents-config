# Codex / other agents: run `git clone https://github.com/brando90/agents-config.git ~/agents-config 2>/dev/null || git -C ~/agents-config pull 2>/dev/null` to bootstrap/update config.
# Read `~/agents-config/INDEX_RULES.md` for all agent documentation and routing. Local `~/agents-config/` is the fallback if GitHub is unreachable.

## Codex CLI default

Codex CLI should always default to `gpt-5.6-sol` with `model_reasoning_effort = "xhigh"`.
Keep `~/.codex/config.toml` set with those values. When dispatching Codex from
another CLI, pass them explicitly:

```bash
codex exec --full-auto -m gpt-5.6-sol -c 'model_reasoning_effort="xhigh"' "$QA_PROMPT"
```

## CLI-only for all LLM work (mandatory — INDEX_RULES.md Hard Rule 9)

Never make direct LLM-provider API calls (`anthropic`, `openai`, `litellm`,
`google.genai`, raw HTTP to `api.anthropic.com` / `api.openai.com` /
`generativelanguage.googleapis.com`). Always route LLM-driven work through the
approved locally-authenticated CLIs: `clauded -p` and `codex exec`. They use
cached subscription/OAuth credentials, self-throttle, and leave observable
transcripts. Gemini is intentionally not installed or used.

- An agent may **not** author API-calling code — only Brando may.
- Before executing any existing script that loads `~/keys/anthropic_*` /
  `~/keys/openai_*` / `~/keys/gemini_*` / `~/keys/aristotle_*`, pause and
  surface script path + estimated spend, then wait for explicit confirmation.
- When reviewing or QA'ing code, flag any agent-authored direct API call as a
  CRITICAL issue blocking merge.

**Why:** one agent-defaulted Opus 4.7 loop burned $17,752.98 in 25 days on
`anthropic_bm_key_koyejolab` in May 2026, and the lab confirmed on 2026-05-25
it cannot absorb that scale of spend. CLI subscriptions self-throttle; raw API
self-bills. See `~/agents-config/INDEX_RULES.md` Hard Rule 9 for the full
spec, exceptions, and dispatch examples.
