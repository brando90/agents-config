# Agent-Config: shared instructions for coding agents

**Doc link:** <https://github.com/brando90/agents-config/blob/main/README.md>

**TLDR:** Start at `~/agents-config/INDEX_RULES.md`, then read the relevant topic rules and references. All clients share the same policy.

By [Brando Miranda](https://brando90.github.io/brandomiranda/). [Contributions welcome](https://github.com/brando90/agents-config/issues).

## The Three-Layer Architecture

1. **Entry points:** [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md) mirror critical reminders and direct the agent to refresh and read the index.
2. **Routing:** [INDEX_RULES.md](INDEX_RULES.md) summarizes everyday rules and routes numbered policies to detailed [topic rules](rules/).
3. **Task references:** [CATALOG.md](CATALOG.md) locates machine, workflow, and writing guides. Read relevant details before acting.

Follow Markdown links explicitly; they are not imports. Keep detailed rules in one canonical file.

## Client compatibility

| Client | Instruction discovery and practical guidance |
|---|---|
| [Codex](https://developers.openai.com/codex/guides/agents-md) | Global `$CODEX_HOME/AGENTS.md` (normally `~/.codex/AGENTS.md`) and repository files; observe its instruction budget. |
| [Claude Code](https://code.claude.com/docs/en/memory) | Global `~/.claude/CLAUDE.md` and ancestor/project files. Under 200 lines is a heuristic; imports still consume context. |
| [Cursor](https://cursor.com/docs/cli/using) | The command-line interface reads both root entrypoints; [rules guidance](https://cursor.com/docs/rules) recommends under 500 lines. |
| [Antigravity](https://antigravity.google/docs/rules) | AGENTS.md or GEMINI.md; globals in `~/.gemini/`; 24,000-byte per-rule cap. Import syntax differs from Claude's. |
| [Grok Build](https://docs.x.ai/build/features/project-rules.md) | Reads both entrypoint families and global `~/.grok/` rules. Verify discovery with `grok inspect`. |

Verify installed versions and actual loaded files; pulling or linking does not reload a running agent. The [instruction audit](docs/instruction-audit/README.md) records sources and byte/word counts alongside line heuristics.

## Quick Start

```bash
if [ -d "$HOME/agents-config/.git" ]; then
  git -C "$HOME/agents-config" pull --ff-only
else
  git clone https://github.com/brando90/agents-config.git "$HOME/agents-config"
fi

# Create missing default-profile entry points; preserve every existing file/link.
mkdir -p "$HOME/.codex" "$HOME/.claude"
if [ ! -e "$HOME/.codex/AGENTS.md" ] && [ ! -L "$HOME/.codex/AGENTS.md" ]; then
  ln -s "$HOME/agents-config/AGENTS.md" "$HOME/.codex/AGENTS.md"
fi
if [ ! -e "$HOME/.claude/CLAUDE.md" ] && [ ! -L "$HOME/.claude/CLAUDE.md" ]; then
  printf '%s\n' '# Shared agent instructions' 'Read `~/agents-config/CLAUDE.md` before working; follow its shared-index routing.' > "$HOME/.claude/CLAUDE.md"
fi
```

Preserve existing profile instructions and add routing to `~/agents-config/INDEX_RULES.md` where needed. Use the active profile's paths; verify nonempty files, link targets, and loading in a fresh session.

## Directory Structure

- `rules/`: detailed shared policy; preserve established rule identifiers.
- `machine/`, `workflows/`, `writing/`: focused guides loaded when relevant.
- `scripts/`, `tests/`: working utilities and deterministic checks.
- `experiments/`, `reports/`, `reviews/`: project records and historical evidence.
- `docs/`: human setup reference, architecture audit, and background material.

Keep useful task-scoped references intact. Add procedures to their topic and routing entry, not every startup file.

## Investigating problems and using Valkyrie

Use [broad investigation](workflows/broad-investigation.md), [Valkyrie diagnosis](workflows/valkyrie.md), and [verified-host bootstrap](workflows/verified-host-bootstrap.md) for their respective tasks. Public procedures stay here; credentials and private configuration stay in authorized private storage.

## Reusable macOS AI App Setup

See the [macOS setup guide](machine/macos-ai-apps/ai_agent_automatable_setup_codex_clauded.md).

## New Server Setup

See [server setup reference](docs/setup-reference.md#new-server-setup) and the matching machine guide in [CATALOG.md](CATALOG.md).

## Remote Access (Claude Remote Control & Codex)

Use [maintained remote dispatch](workflows/remote-job-dispatch.md). Earlier setup recipes remain in the [operator reference](docs/setup-reference.md#remote-access-claude-remote-control--codex).

## DFS Job Queue (Running Experiments Across SNAP Nodes)

For the distributed filesystem (DFS) queue on Stanford Network Analysis Project (SNAP) hosts, see [remote job dispatch](workflows/remote-job-dispatch.md) and the [setup reference](docs/setup-reference.md#dfs-job-queue-running-experiments-across-snap-nodes).

### Keeping watchers alive: keytab + cron (no password prompt, ever)

See the [watcher persistence recipe](docs/setup-reference.md#keeping-watchers-alive-keytab--cron-no-password-prompt-ever).

## How to Integrate with Your Project Repos

Use [repo initialization](workflows/repo-init.md). Keep project-specific instructions alongside the project and shared policy here.

## Migrating from a Monolithic CLAUDE.md

See the [migration procedure](docs/setup-reference.md#migrating-from-a-monolithic-claudemd); small files can stay intact.

## Initialization Guides

See [passwordless host access](init_no_passwords_snap_kinit.md) and [server-side credential renewal](todo_infinite_reauth_kinit_server_side.md).

## Security

Public repository: keep secrets and private host details out of commits. Use private configuration references. Model work follows Hard Rule 9 through approved clients and budgets.

## Related Work

[Related projects and historical comparisons](docs/reference/background.md#related-work).

## Citation

[Repository and related-paper citations](docs/reference/background.md#citation). Licensed under [Apache 2.0](LICENSE).

## Acknowledgments

[Design credit and acknowledgments](docs/reference/background.md#acknowledgments), including Yegor Denisov-Blanch's contribution to the original idea.
