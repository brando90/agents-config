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
```

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
