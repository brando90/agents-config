# Agent-Config: Modular Documentation Architecture for Multi-Agent Coding Workflows

A modular, agent-agnostic documentation system for AI coding agents (Claude Code, Codex, and beyond). Designed for scalability and context-window efficiency.

As codebases scale past 30-50k LOC (lines of code), monolithic agent instruction files (a single `CLAUDE.md` or `agents.md`) waste context window on irrelevant details and don't generalize across agents. This repo implements a three-layer architecture that solves both problems.

**Designed by [Brando Miranda](https://brando90.github.io/brandomiranda/) (Stanford CS PhD).** Inspired by [Yegor Denisov-Blanch](https://x.com/yegordb)'s insight that modular documentation is essential for multi-agent workflows at scale.

**Contributions welcomed and encouraged!** Open a [GitHub Issue](https://github.com/brando90/agents-config/issues), start a [Discussion](https://github.com/brando90/agents-config/discussions), or submit a PR (pull request).

---

## The Three-Layer Architecture

```
←──── Layer 1: Entry Points ────→              ← Layer 2 →              ← Layer 3 →

From ~/            agents-config/
┌──────────────┐   ┌──────────────┐
│ ~/CLAUDE.md  │──▸│ CLAUDE.md    │            ┌─────────────┐            ┌──────────────┐
│              │   │              │            │             │            │ machine/     │
│ ~/agents.md  │──▸│ agents.md    │───────────▸│  INDEX.md   │───────────▸│ workflows/   │
│              │   │              │            │             │            │ conventions/ │
└──────────────┘   └──────────────┘            │ Global      │            └──────────────┘
  (symlinks)       "read INDEX.md"             │ Rules       │
                                               │ Doc Groups  │
                                               └─────────────┘

From any project repo (also Layer 1):
┌──────────────┐
│ CLAUDE.md    │───────────▸ ~/agents-config/INDEX.md    (shared)
│              │───────────▸ docs/agent-docs/INDEX.md    (project)
├──────────────┤
│ agents.md    │───────────▸ ~/agents-config/INDEX.md
│              │───────────▸ docs/agent-docs/INDEX.md
└──────────────┘
```

**Layer 1 — Agent-specific entry points.** `CLAUDE.md` (for Claude Code) and `agents.md` (for Codex) live in the repo root. Their content is one line: "Read `INDEX.md`." From the home directory, `~/CLAUDE.md` and `~/agents.md` are filesystem symlinks to these files, so the agent finds the same routing regardless of where it's launched.

**Layer 2 — Shared agent-agnostic index.** `INDEX.md` is the master routing table. It groups docs by topic with concise path-based pointers so the agent only loads what's relevant to the current task. It also contains the global rules that always apply.

**Layer 3 — Modular scoped docs.** Individual markdown files organized by domain. Each is self-contained and only loaded when relevant. Machine configs, workflow guides, coding conventions.

### Why this exists

1. **Context window efficiency.** An agent working on a Python formatting issue doesn't need your GPU cluster docs. The index lets it pick only what's relevant.
2. **Multi-agent compatibility.** Claude Code, Codex, and future agents all read from the same doc set. Only Layer 1 differs per agent.
3. **Scalability.** Adding a new machine, workflow, or convention is one file + one line in the index. No monolithic file to maintain.
4. **Secrets stay out of the repo.** Machine docs reference existing config files (`~/.ssh/config`, `~/keys/`, `~/.zshrc`) rather than duplicating secrets. Nothing sensitive is tracked.

---

## Directory Structure

```
agent-config/
├── README.md                    ← you are here
├── INDEX.md                     ← Layer 2: master routing table
├── CLAUDE.md                    ← Layer 1: Claude Code entry point
├── agents.md                    ← Layer 1: Codex / other agents entry point
├── LICENSE                      ← Apache 2.0
├── .gitignore
│
├── machine/
│   ├── public/                  ← public machine docs + templates (tracked)
│   │   ├── TEMPLATE.md
│   │   ├── ampere1.md
│   │   ├── snap.md
│   │   ├── mac.md
│   │   ├── sherlock.md
│   │   └── marlowe.md
│
├── workflows/
│   ├── byobu-agents.md          ← parallel agent sessions with byobu
│   ├── git-worktrees.md         ← worktree isolation for parallel agents
│   ├── qa-gating.md             ← cross-agent review protocol
│   ├── clauded-usage.md         ← `clauded` alias and skip-permissions usage
│   └── expts-and-results.md     ← experiment structure and results reporting
│
├── conventions/
│   ├── general-coding.md        ← commit, branch, PR conventions
│   └── agent-prompt-builder-rules.md  ← meta-rules for writing agent prompts
│
└── examples/
    └── project-level-setup/     ← how a project repo integrates with agent-config
        ├── CLAUDE.md            ← points to both home + project indexes
        ├── agents.md            ← same for Codex
        └── docs/agent-docs/
            ├── INDEX.md
            └── architecture.md
```

---

## How to Use This with Your Project Repo

Each project repo (e.g., [`beyond-scale-language-data-diversity`](https://github.com/brando90/beyond-scale-language-data-diversity), `harbor`) should have its own `docs/agent-docs/INDEX.md` with project-specific documentation. The home-level `agent-config` covers environment, machine, and personal convention context that spans all projects.

### Step 1: Add a project-level entry point

In your project repo, create `CLAUDE.md` (or `agents.md`):

```markdown
# Project: my-project

Read the home-level agent index for environment context:
- `~/agent-config/INDEX.md`

Read the project-level agent index for project-specific docs:
- `docs/agent-docs/INDEX.md`
```

### Step 2: Create project-specific docs

```
my-project/
├── CLAUDE.md                         ← points to both indexes
└── docs/agent-docs/
    ├── INDEX.md                      ← project routing table
    ├── architecture.md               ← how the codebase is structured
    ├── testing.md                    ← how to run tests
    └── deployment.md                 ← deployment procedures
```

See `examples/project-level-setup/` for a complete working example.

### Step 3: Fork and customize

1. Fork this repo
2. Fill in `machine/public/` with your actual machine specs (non-sensitive info). Reference existing config files (`~/.ssh/config`, `~/keys/`) for secrets — don't duplicate them.
3. Customize `conventions/` for your team's standards
4. Add your own workflow docs

---

## Quick Start

```bash
# Clone to your home directory
git clone https://github.com/brando90/agents-config.git ~/agent-config

# Symlink entry points from home dir
ln -s ~/agent-config/CLAUDE.md ~/CLAUDE.md
ln -s ~/agent-config/agents.md ~/agents.md

# Fill in your machine doc (non-sensitive specs, point to ~/.ssh/config etc. for secrets)
cp ~/agent-config/machine/public/TEMPLATE.md ~/agent-config/machine/public/my-server.md

# Claude Code will automatically read CLAUDE.md → INDEX.md
# Codex will automatically read agents.md → INDEX.md
```

---

## How to Integrate with Your Project Repos

Each project repo should have **two entry points** (`CLAUDE.md` for Claude Code, `agents.md` for Codex) that point to **two indexes**: the home-level `~/agent-config/INDEX.md` (environment context) and the project's own `docs/agent-docs/INDEX.md` (project-specific docs).

Project docs live in the repo so they're versioned with the code and available to anyone who clones it.

```
your-project/
├── CLAUDE.md                         ← points to BOTH indexes
├── agents.md                         ← same for Codex
├── docs/
│   └── agent-docs/
│       ├── INDEX.md                  ← project-specific routing table
│       ├── architecture.md           ← how the codebase is structured
│       ├── eval-pipeline.md          ← evaluation workflow docs
│       └── conventions.md            ← project-specific conventions
├── src/
└── tests/
```

Your project's `CLAUDE.md` looks like:

```markdown
# Project: your-project

Read the home-level agent index for environment context:
- `~/agent-config/INDEX.md`

Read the project-level agent index for project-specific docs:
- `docs/agent-docs/INDEX.md`
```

See `examples/project-level-setup/` for a complete working example with both `CLAUDE.md` and `agents.md`.

---

## Security

This is a **public repo**. Never commit API keys, tokens, passwords, or private IPs. Machine docs should reference existing config files (`~/.ssh/config`, `~/keys/`, `~/.zshrc`) for sensitive details rather than duplicating them. Reusable templates should use `<PLACEHOLDER>` markers.

> **For teams that need a private layer:** You could add a gitignored `machine/private/` directory with full machine configs containing real values. We removed this to keep the default setup minimal — most single-user setups don't need it since machine docs can just point to existing config files.

---

## Related Work

The AI coding agent ecosystem is growing fast. Here's how `agents-config` relates to existing tools:

**Multi-Agent Orchestration** — [Ruflo](https://github.com/ruvnet/ruflo) (21.9K stars), [Agent Orchestrator](https://github.com/ComposioHQ/agent-orchestrator) (4.9K), [Emdash](https://github.com/generalaction/emdash) (2.8K), and [Gas Town](https://github.com/steveyegge/gastown) (12.6K) focus on *running* multiple agents — spawning, coordinating, and merging their work. `agents-config` is complementary: it standardizes the *documentation* agents read, not how they're orchestrated.

**Parallel Agent Execution** — [parallel-code](https://github.com/johannesjo/parallel-code) (387 stars) and [parallel-worktrees](https://github.com/SpillwaveSolutions/parallel-worktrees) run agents side-by-side in git worktrees. Our `workflows/` docs (byobu, git-worktrees) describe the same patterns but as portable documentation rather than tooling.

**CLAUDE.md Templates & Best Practices** — [claude-code-templates](https://github.com/davila7/claude-code-templates) (23.2K stars), [claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) (19K), [claude-code-showcase](https://github.com/ChrisWiles/claude-code-showcase) (5.5K), and [claude-md-templates](https://github.com/abhishekray07/claude-md-templates) (95) provide example `CLAUDE.md` files and configurations. These are Claude-specific. `agents-config` is agent-agnostic (Layer 1 adapts per agent; Layers 2–3 are shared) and uses a routing index instead of a monolithic file.

**Curated Lists** — [awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) (29.2K stars) and [awesome-claude-md](https://github.com/josix/awesome-claude-md) (159) catalog plugins, skills, and example configs across the ecosystem.

| Concern | Orchestration tools | Template repos | `agents-config` |
|:--------|:-------------------|:---------------|:-----------------|
| Runs agents | Yes | No | No |
| Provides agent docs | Sometimes | Yes (Claude-only) | Yes (agent-agnostic) |
| Scales past monolithic files | N/A | No | Yes (three-layer index) |
| Secrets stay out of repo | No | No | Yes (reference existing config files) |

---

## Citation

This repo is open source under the [Apache 2.0 License](LICENSE).

```bibtex
@misc{miranda2026agentconfig,
  author = {Brando Miranda and Claude (Anthropic)},
  title = {Agent-Config: A Modular, Agent-Agnostic Documentation Architecture for Multi-Agent Coding Workflows},
  year = {2026},
  howpublished = {\url{https://github.com/brando90/agents-config}},
}
```

We list Claude (Anthropic) as co-author because this system was designed collaboratively between human and AI. While AI co-authorship is not yet widely accepted in academic venues, we believe transparency about AI contributions is important and reflects the future of human-AI collaboration.

---

## Acknowledgments

We thank [Yegor Denisov-Blanch](https://x.com/yegordb) for the original insight about modular, agent-agnostic documentation for multi-agent coding workflows, which inspired this project. (We plan to ask Yegor if he'd like to be listed as a co-author — pending his response.)
