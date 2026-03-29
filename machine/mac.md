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
