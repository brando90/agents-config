# Pi to Claude Code endpoint (OpenAI-style)

**Doc link:** <https://github.com/brando90/agents-config/blob/main/experiments/04_pi_claude_endpoint/README.md>

**TLDR:** A small stdlib Python server that speaks the OpenAI chat format and answers each request by running one Claude Code call (through the account launcher that checks the signed-in account, no fallback). Pi lists it as a custom model. Text only: requests with `tools` are refused, so agentic Pi runs use Pi's own `claude-accounts` provider (`../../config/pi/claude-accounts/README.md`) instead.

## What it is
- `server.py`: `POST /v1/chat/completions` (also `stream: true`), `GET /v1/models`, `GET /healthz`. Models: `claude-opus-5-5`, `claude-fable-5-1`, `claude-sonnet-5-5`, `claude-haiku-4-5`.
- Backend: `--claude-cmd ~/.pi/agent/claude-account-bin/vals-claude-code` (or `stanford-claude-code`, `personal-claude-code`). The launcher checks email and org before any call and never falls back to another payer. `--backend echo` is a test backend with no model call.
- Which coworker: it reaches Claude Code, not the `ultimate_brando9` agent process, which is not a callable server.

## Safety
- No keys, tokens or private links in this repo. Binds `127.0.0.1` only by default.
- Every `/v1` call needs `Authorization: Bearer <token>`; `/healthz` returns only `{"ok": true}`. Constant-time compare. The server refuses to start if the token file is not mode 600 or is under 32 characters.
- Token lives outside Git. `gen_token.sh` writes it (mode 600, never printed). Locations (not the token): snap shared disk `/dfs/scratch0/brando9/.config/pi-claude-endpoint/token`, linked from `~/.config/pi-claude-endpoint/token`; copies belong in the same path in the home on Sherlock and FarmShare (not shared with snap) and on the Macs once SSH works. Mode 600 everywhere.

## Run
```bash
sh gen_token.sh /dfs/scratch0/brando9/.config/pi-claude-endpoint/token    # once
python3 server.py --port 18300 --claude-cmd ~/.pi/agent/claude-account-bin/vals-claude-code
```
Pi: merge `pi-models-snippet.json` into `~/.pi/agent/models.json` (`apiKey` is `!cat <token file>`), then `pi --provider ultimate-claude-endpoint --model claude-opus-5-5 --no-tools -p "..."`.

## Test
`python3 -m unittest tests/test_server.py` (echo backend: auth, models, chat, stream, tool refusal, token-file mode).

## Verified 10-29-2026 on skampere1
- Pi 1.4.0 with a models.json holding the snippet, echo backend: `pi --offline --provider ultimate-claude-endpoint --model claude-opus-5-5 --no-tools --no-session -p "Say hello"` returned `ECHO: [user] Say hello` (server log: `POST /v1/chat/completions 200`). Without the token: 401.
- Claude backend: not yet verified. Claude Code is signed out on skampere1 for all three accounts, so the server answers 502 `login check failed, no fallback`. Fix: sign in the account once, e.g. `CLAUDE_CONFIG_DIR=~/.claude-vals claude auth login` (Vals work only), then re-run the same Pi command.

## Local on the coworker's own computer (10-29-2026)
- Pi 1.4.0 installed in `~/pi-local` (`npm install --prefix ~/pi-local @earendil-works/pi-coding-agent`); `PI_CODING_AGENT_DIR=~/pi-local/agent` holds the snippet as `models.json`. Token at `~/.config/pi-claude-endpoint/token` (mode 600, not in Git).
- Pi needs `NO_PROXY=127.0.0.1,localhost` when the shell sets an HTTP proxy, otherwise Pi reports `Connection error.`
- Verified with the echo backend: no token 401, token 200, and `pi --offline --provider ultimate-claude-endpoint --model claude-opus-5-5 --no-tools --no-session -p "Say hello"` returned `ECHO: [user] Say hello` through the server.
- Claude backend on this computer: not verified. A child `claude -p` of the coworker's run is not signed in (`Not logged in`), so the server answers 502 `Not logged in`; the coworker's own model access is not passed to child processes. It works once Claude Code is signed in on this computer (`claude auth login`, the account Brando picks).
- Judge use: a judge call is a plain chat completion, so the same endpoint works as a judge (`model` + `messages`, no tools).
- Carries: text in, text out, `stream: true`. Does not carry: Pi's tool calls (refused with 400), images, other models than the four listed.

## Technical report
- Decision: stdlib-only server, text-only, token file, one `claude -p` per request with `--tools ""`, `--setting-sources ""`, `--strict-mcp-config`, no session persistence, so nothing from the host's settings, skills or MCP servers leaks into a call.
- Why tools are refused: faithfully carrying Pi's tool calls needs the proposal-only transport that `config/pi/claude-accounts` already implements.
- Credit: cc opus 5.5 xhigh.
