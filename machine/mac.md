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

# Symlink Claude Code settings (model=opus, effortLevel=high)
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

Daily driver stays Claude Code. Vibe is kept as an *experimental* tool for cert-judge benchmarks and parallel/cheap Lean proof attempts.

- Binary: `~/.local/bin/vibe` (install: `uv tool install mistral-vibe`)
- API key: `MISTRAL_API_KEY` loaded from `~/keys/mistral_api_key.txt` (exported in `~/.zshrc` next to `OPENAI_API_KEY`)
- Lean agent enabled: `~/.vibe/config.toml` → `installed_agents = ["lean"]` (TUI equivalent: `/leanstall`)
- Run Leanstral: `vibe --agent lean` — uses free `labs-leanstral-2603` endpoint (traffic logged by Mistral; don't paste private prompts)
- For cert-judge experiments prefer the bundled `mistralai` Python SDK directly: `client.chat.complete(model="labs-leanstral-2603", ...)` — slots into `experiments/00_overall_cert_judge_metric_with_properties/main_overall_judge_score.py` alongside the Claude judge
- Announcement: <https://mistral.ai/news/leanstral> · Install docs: <https://docs.mistral.ai/mistral-vibe/introduction/install>

**Recheck if** *(verified 2026-05-02, vibe 2.9.3)*: `vibe` major-version bump · `labs-leanstral-2603` switches from free-launch to metered · successor model ships (Leanstral-2 etc.) · Leanstral leaves the labs/preview endpoint (production name will differ).

### Agent board (which agent is in which tmux window)

One page listing every agent session — local Claude Code (personal `cc` and Vals `ccv` configs), local Codex (`cxd`), and the jobs running in byobu/tmux sessions on the SNAP nodes — with the **same seven columns in every table**: `tmux | Agent | Id | Where | Model+effort | Topic | Last`. Code lives in this repo; the runtime is per machine.

- Install / re-install on any Mac (idempotent; SNAP nodes need nothing, the Mac polls them over ssh):
  `bash ~/agents-config/scripts/agent_board_install.sh` — writes the two launchd jobs (`com.brando.agentboard` renders `~/.agent-board/board.html` every 20 s with `--snap`; `com.brando.agentboard.summarize` tops up one-line session summaries every 5 min via `claude -p --model claude-sonnet-5`), adds the `board` / `board-open` zsh aliases, and registers `scripts/agent_session_register.sh` as a Claude Code `SessionStart` hook in `~/.claude` and `~/.claude-vals`.
- View: `board` (terminal, last 24 h) · `board-open` (browser, auto-refreshes) · errors in `~/.agent-board/agentboard.err`.
- Where the tmux column comes from: Claude Code's own per-process registry `~/.claude*/sessions/<pid>.json` (`"tmux":"8:@8.%8"` = session:window.pane) — exact, no inference; Codex threads are matched to their `codex` process by start time (rollout `session_meta`); SNAP rows show the tmux session name on that node (`tmux attach -t <name>` there). `cursor` / `chatgpt` / `vscode` mark an app terminal outside tmux; `—` means no live process (`claude --resume <id>` continues it).
- Source: `~/agents-config/scripts/agent_board.py` (`--hours`, `--all`, `--html`, `--snap`, `--summarize`).
