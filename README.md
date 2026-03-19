# agent-config

A modular, agent-agnostic documentation system for AI coding agents.

As codebases scale past 30-50k LOC, monolithic agent instruction files (a single `CLAUDE.md` or `agents.md`) waste context window on irrelevant details and don't generalize across agents. This repo implements a three-layer architecture that solves both problems.

**Designed by [Brando Miranda](https://brando90.github.io/brandomiranda/) (Stanford CS PhD).** Inspired by [Yegor Denisov-Blanch](https://x.com/yegordb)'s insight that modular documentation is essential for multi-agent workflows at scale.

---

## The Three-Layer Architecture

```
Layer 1: Agent Entry Points          Layer 2: Shared Index           Layer 3: Scoped Docs
┌──────────────┐                     ┌──────────────────┐           ┌─────────────────────────┐
│ claude.md    │──┐                  │                  │     ┌────▸│ machine/public/snap.md  │
│ (Claude Code)│  │                  │   INDEX.md       │     │     │ machine/public/mac.md   │
└──────────────┘  │    "read         │                  │─────┤     │ machine/public/...      │
                  ├───▸ INDEX.md"    │  Global Rules    │     │     ├─────────────────────────┤
┌──────────────┐  │                  │  QA Gating       │     ├────▸│ workflows/byobu.md      │
│ agents.md    │──┘                  │  Doc Registry    │     │     │ workflows/git-worktrees │
│ (Codex, etc.)│                     │                  │     │     │ workflows/qa-gating.md  │
└──────────────┘                     └──────────────────┘     │     ├─────────────────────────┤
                                                              └────▸│ conventions/coding.md   │
                                                                    │ conventions/prompts.md  │
                                                                    └─────────────────────────┘
```

**Layer 1 — Agent-specific entry points.** Thin pointer files that each agent natively reads. `claude.md` for Claude Code, `agents.md` for Codex. Each one says: "Read `INDEX.md`." One line. No logic.

**Layer 2 — Shared agent-agnostic index.** `INDEX.md` is the master routing table. It lists all available docs by topic with one-line descriptions so the agent only loads what's relevant to the current task. It also contains global rules (QA gating, critical constraints) that always apply.

**Layer 3 — Modular scoped docs.** Individual markdown files organized by domain. Each is self-contained and only loaded when relevant. Machine configs, workflow guides, coding conventions.

### Why this exists

1. **Context window efficiency.** An agent working on a Python formatting issue doesn't need your GPU cluster docs. The index lets it pick only what's relevant.
2. **Multi-agent compatibility.** Claude Code, Codex, and future agents all read from the same doc set. Only Layer 1 differs per agent.
3. **Scalability.** Adding a new machine, workflow, or convention is one file + one line in the index. No monolithic file to maintain.
4. **Public/private separation.** Templates and conventions are public. Actual IPs, SSH configs, and secrets stay in gitignored `private/` dirs.

---

## Directory Structure

```
agent-config/
├── README.md                    ← you are here
├── INDEX.md                     ← Layer 2: master routing table
├── claude.md                    ← Layer 1: Claude Code entry point
├── agents.md                    ← Layer 1: Codex / other agents entry point
├── LICENSE                      ← Apache 2.0
├── .gitignore
│
├── machine/
│   ├── public/                  ← templates with <PLACEHOLDERS> (tracked)
│   │   ├── TEMPLATE.md
│   │   ├── ampere1.md
│   │   ├── snap.md
│   │   ├── mac.md
│   │   ├── sherlock.md
│   │   └── marlowe.md
│   └── private/                 ← real configs with actual values (gitignored)
│       ├── .gitkeep
│       └── EXAMPLE.md
│
├── workflows/
│   ├── byobu-agents.md          ← parallel agent sessions with byobu
│   ├── git-worktrees.md         ← worktree isolation for parallel agents
│   ├── qa-gating.md             ← cross-agent review protocol
│   └── clauded-usage.md         ← `clauded` alias and skip-permissions usage
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

Each project repo (e.g., `veribench`, `harbor`) should have its own `docs/agent-docs/INDEX.md` with project-specific documentation. The home-level `agent-config` covers environment, machine, and personal convention context that spans all projects.

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
2. Fill in `machine/private/` with your actual machine configs (gitignored)
3. Customize `conventions/` for your team's standards
4. Add your own workflow docs

---

## Quick Start

```bash
# Clone to your home directory
git clone https://github.com/brando90/agent-config.git ~/agent-config

# Create private machine configs (gitignored, never pushed)
cp machine/public/TEMPLATE.md machine/private/my-server.md
# Edit with your actual IPs, paths, etc.

# Claude Code will automatically read claude.md → INDEX.md
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

## Security: Public/Private Boundary

This is a **public repo**. Never include real IPs, SSH paths, API keys, or internal server details in tracked files. All machine templates in `machine/public/` use `<PLACEHOLDER>` markers.

Sensitive configs go in `machine/private/`, which is gitignored. Copy a template from `machine/public/` to `machine/private/` and fill in your actual values — they'll never be committed.

---

## Citation

This repo is open source under the [Apache 2.0 License](LICENSE).

```bibtex
@misc{miranda2026agentconfig,
  author = {Brando Miranda and Claude (Anthropic)},
  title = {Agent-Config: A Modular, Agent-Agnostic Documentation Architecture for Multi-Agent Coding Workflows},
  year = {2026},
  howpublished = {\url{https://github.com/brando90/agent-config}},
}
```

We list Claude (Anthropic) as co-author because this system was designed collaboratively between human and AI. While AI co-authorship is not yet widely accepted in academic venues, we believe transparency about AI contributions is important and reflects the future of human-AI collaboration.

---

## Acknowledgments

We thank [Yegor Denisov-Blanch](https://x.com/yegordb) for the original insight about modular, agent-agnostic documentation for multi-agent coding workflows, which inspired this project. (We plan to ask Yegor if he'd like to be listed as a co-author — pending his response.)
