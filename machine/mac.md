# Machine: Mac — macOS (Apple Silicon)

**Shell: zsh** (`~/.zshrc`). Read `~/.zshrc` for paths, envs, aliases, and tool locations.

## Behavioral Constraints

- **No CUDA.** Do not attempt vllm, sglang, or bitsandbytes — Linux-only. Run those on cluster.
- **Docker Desktop must be running.** If you see `Cannot connect to the Docker daemon`, open Docker Desktop and wait for it to start.
- **Check arch with** `sysctl -n hw.optional.arm64`. `uname -m` may lie under Rosetta.

## Setup

```bash
# Clone agents-config if not present
git clone git@github.com:brando90/agents-config.git ~/agents-config 2>/dev/null || true

# Symlink Claude Code settings (model=claude-fable-5-1, effortLevel=max)
mkdir -p ~/.claude
ln -sf ~/agents-config/claude-code-settings.json ~/.claude/settings.json

# Install the canonical Claude and Codex instruction entry points.
ln -sf ~/agents-config/CLAUDE.md ~/CLAUDE.md
mkdir -p ~/.codex
ln -sf ~/agents-config/AGENTS.md ~/.codex/AGENTS.md
ln -sf ~/agents-config/AGENTS.md ~/AGENTS.md       # optional compatibility
ln -sf ~/agents-config/AGENTS.md ~/agents.md       # legacy home-level compatibility
```

### Lid Never Sleeps

If Brando says this Mac should never sleep, especially when the lid closes, load
[`~/agents-config/machine/mac-never-sleep-lid.md`](mac-never-sleep-lid.md)
before acting.
The core setting is `pmset disablesleep 1`; do not rely on Amphetamine or
`caffeinate` assertions alone for lid-close behavior. If the live lid flag stays
enabled, do not claim lid-close behavior is solved until Amphetamine
Closed-Display Mode is enabled and verified explicitly. Never store the Mac
login password in plaintext.

## Trusted AI Agent Setup

For full-trust local AI-agent setup on each Mac, first use [`~/agents-config/machine/macos-ai-apps/ai_agent_automatable_setup_codex_clauded.md`](macos-ai-apps/ai_agent_automatable_setup_codex_clauded.md), then complete [`~/agents-config/machine/macos-ai-apps/manual_macos_permissions_checklist_ai_apps.md`](macos-ai-apps/manual_macos_permissions_checklist_ai_apps.md). These docs deliberately avoid bypassing macOS TCC/SIP or creating permanent passwordless `sudo`.

## Tools

### Vibe (Mistral) + Leanstral

Historical Vibe/Leanstral setup used Mistral provider keys and a direct Python client.
It is not an approved agent workflow under Hard Rule 9 in
[`~/agents-config/INDEX_RULES.md`](../INDEX_RULES.md). Route new large language model
(LLM) experiment work through the authenticated `clauded` or `codex exec`
command-line interfaces (CLIs), using Hard Rule 8's workload tier. Do not restore
provider-key exports or write direct provider calls from this old setup.

### Agent board (which agent is in which tmux window)

One page listing every agent session — local Claude Code (personal `cc` and Vals `ccv` configs), local Codex (`cxd`), and the jobs running in byobu/tmux sessions on the SNAP nodes — with the **same eight columns in every table**: `tmux | Agent | Id | Where | Model+effort | Task | Expt | Last` (personal table first, then Vals, Codex, SNAP). **Where** is the fully expanded working directory — the `/Users/<you>` prefix says which laptop, a DHCP hostname does not; SNAP rows are `node:/lfs/…`. **Expt** is the `experiments/<NN_name>` directory the agent's own recent actions and prose reference most (last 200 mentions in cwd, user/assistant text and tool inputs; tool outputs are ignored so a `cat CLAUDE.md` does not count), a runner-up beneath when it has at least half as many, `-` when the session never referenced one; SNAP rows use the job's experiment dir; cached per transcript in `~/.agent-board/expts.json`. **Every table reads in your terminal's tab order** (Brando 2026-09-04): a tab's position is the birth time of the oldest process on the tty its tmux client is attached to — a terminal app spawns one shell per tab and lists tabs in the order they were opened — so the board reads top-to-bottom like the Cursor integrated terminal and re-derives itself whenever a tab opens or closes. Do **not** use the tty *number*: ptys are recycled, and on 2026-09-04 session 3 held `ttys022` while session 6 held `ttys025` although 6's tab was opened eight minutes earlier, which mis-ordered the Vals table. The sort key is tab position alone and the sort is stable, so rows with no tab of their own (SNAP jobs, exited sessions) keep their table's existing order at the bottom instead of being reshuffled. Code lives in this repo; the runtime is per machine.

- Install / re-install on any Mac (idempotent; SNAP nodes need nothing, the Mac polls them over ssh):
  `bash ~/agents-config/scripts/agent_board_install.sh` — writes the two launchd jobs (`com.brando.agentboard` renders `~/.agent-board/board.html` every 20 s with `--snap`; `com.brando.agentboard.summarize` tops up one-line session summaries every 5 min via `claude -p --model claude-sonnet-5`), adds the `board` / `board-open` zsh aliases, and registers `scripts/agent_session_register.sh` as a Claude Code `SessionStart` hook in `~/.claude` and `~/.claude-vals`.
- View: `board` (terminal, last 24 h) · `board-open` (browser, auto-refreshes) · errors in `~/.agent-board/agentboard.err`.
- Phone: `python3 ~/agents-config/scripts/agent_board_phone.py` installs a dedicated private Tailscale connection after `brew install tailscale`; see [`~/agents-config/machine/mac-agent-board-phone.md`](mac-agent-board-phone.md) for sign-in, Home Screen access, and stopping. Serve only the single board file, never the runtime directory. The page stacks rows on phones and warns when its snapshot is more than 90 seconds old.
- **Freshness contract (Brando 2026-09-04): every column shows the CURRENT state, derived from the newest evidence — never the first occurrence in a transcript.** The render already runs every 20 s, so a stale cell is a bug in how the value is read, not a cadence problem. Concretely: model and effort come from the *tail* of the transcript (`current_model()`), because `/model` and `/effort` mid-session rewrite those fields in later lines and a head-only scan reported `fable5` for a session already switched to `opus`. When adding a column, ask what makes it go stale and read the end, not the beginning; a column that cannot be kept true does not belong on the board.
- **Bringing sessions back after a restart or a dead tmux server (2026-09-08):** a killed `claude` process loses nothing but itself — the conversation is the transcript under `~/.claude*/projects/<cwd-slug>/<id>.jsonl`. `python3 ~/agents-config/scripts/agent_board.py --resume-dead` (a week back by default; the `board` alias pins `--hours 24`, so pass `--hours 168` with it) lists every interactive transcript with no process behind it; `--resume-dead <id> [<id>…]` or `--resume-dead all` opens one tmux window per session in the tmux session you run it from (else the first one, else a new detached `recovered`), `cd`s to the session's own cwd and types `clauded --resume <id>` (`clauded-vals` for `ccv`) into it. Nothing reaches the model until you type in that window; `--dry-run` prints the tmux commands, `--fork` adds `--fork-session` (new id, original transcript untouched). What does not survive the process: the session-only `/effort` override (re-run it), background agents, the old window mapping. Live sessions and finished one-shots are refused by name, an id given twice (a prefix and its full form) opens once, only UUIDs are ever typed into the shell, and when the process table cannot be read (a live session would look dead and get forked) nothing is resumed at all; the exit code is 1 whenever any pick did not open. On 2026-09-06 a restart with the lid closed killed nine idle sessions (five `cc`, four `ccv`); all came back this way.
- Where the tmux column comes from: Claude Code's own per-process registry `~/.claude*/sessions/<pid>.json` (`"tmux":"8:@8.%8"` = session:window.pane) — exact, no inference; Codex threads are matched to their `codex` process by start time (rollout `session_meta`); SNAP rows show the tmux session name on that node (`tmux attach -t <name>` there). `cursor` / `chatgpt` / `vscode` mark an app terminal outside tmux; `—` means no live process (`board --hours 168 --resume-dead <id>` brings it back, see below; by hand `clauded --resume <id>` from its cwd); `one-shot` means a `claude -p` job that has finished — its answer is the transcript, there is nothing to resume, and it was never waiting on you (read from the `"entrypoint":"sdk-cli"` stamp on its records; interactive sessions carry `cli`, the desktop app `claude-desktop`). One row per **live process**, not per session: `claude --resume <id>` run in a second window is a second process appending to the same transcript, so it gets its own row naming the other window and carrying its pid — two forks of one conversation, keep one.
- Source: `~/agents-config/scripts/agent_board.py` (`--hours`, `--all`, `--html`, `--snap`, `--summarize`).
