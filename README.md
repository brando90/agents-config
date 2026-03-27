# Agent-Config: Modular Documentation Architecture for Multi-Agent Coding Workflows

A modular, agent-agnostic documentation system for AI coding agents (Claude Code, Codex, and beyond). Designed for scalability and context-window efficiency.

As codebases scale past 30-50k LOC (lines of code), monolithic agent instruction files (a single `CLAUDE.md` or `agents.md`) waste context window on irrelevant details and don't generalize across agents. This repo implements a three-layer architecture that solves both problems.

**Designed by [Brando Miranda](https://brando90.github.io/brandomiranda/) (Stanford CS PhD).** Inspired by [Yegor Denisov-Blanch](https://x.com/yegordb)'s insight that modular documentation is essential for multi-agent workflows at scale.

**Contributions welcomed and encouraged!** Open a [GitHub Issue](https://github.com/brando90/agents-config/issues), start a [Discussion](https://github.com/brando90/agents-config/discussions), or submit a PR (pull request).

---

## The Three-Layer Architecture

```
←────── Layer 1: Entry Points ────────→   ←── Layer 2 ──→   ←─── Layer 3: Scoped Docs ───→
       ~/           ~/agent-config/        ~/agent-config/                ~/vb/ (repo)
┌──────────────┐   ┌──────────────────┐       (~/ac/)
│ ~/CLAUDE.md  │──▸│ ~/ac/CLAUDE.md   │   ┌────────────────────┐   ┌───────────────────────┐
│              │   │                  │   │                    │   │ ~/vb/CLAUDE.md        │  # text ref ──▸ both INDEX's
│ ~/agents.md  │──▸│ ~/ac/agents.md   │──▸│~/ac/INDEX_RULES.md │──▸│ ~/vb/agents.md        │  # text ref (same, for Codex)
│              │   │                  │   │                    │   │ ~/vb/docs/agent-docs/ │  # project-scoped docs
│              │   │                  │   │                    │   └───────────────────────┘
└──────────────┘   └──────────────────┘   └────────────────────┘
   (symlinks)       "read INDEX_RULES.md"  (rules + routing)    (loaded on demand)

~/agent-config/ (~/ac/) outline:
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ CLAUDE.md        ← Layer 1 entry; text ref ──▸ INDEX_RULES.md                            │
│ agents.md        ← Layer 1 entry; text ref ──▸ INDEX_RULES.md                            │
│ INDEX_RULES.md   ← Layer 2 global rules + doc routing; refs ──▸ machine/, workflows/     │
│ README.md        ← repo docs (you are here)                                              │
│ machine/         ← Layer 3: per-machine configs (mac.md, snap.md, sherlock.md, …)        │
│ workflows/       ← Layer 3: reusable workflows (qa-gating.md, git-worktrees.md, …)       │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

**Layer 1 — Agent-specific entry points.** `CLAUDE.md` (for Claude Code) and `agents.md` (for Codex) live in the repo root. Their content is a single line directing the agent to `~/agent-config/INDEX_RULES.md`. From the home directory, `~/CLAUDE.md` and `~/agents.md` are filesystem symlinks to these files, so the agent finds the same entry point regardless of where it's launched.

**Layer 2 — Global rules & doc routing.** `INDEX_RULES.md` contains two things: (1) global rules that always apply (never commit secrets, verify before pushing, QA gating, etc.) and (2) doc routing that groups docs by topic with concise path-based "references" — file paths written as text (e.g., `~/agent-config/machine/mac.md`) that tell the agent where to look — so the agent only loads what's relevant to the current task.

**Layer 3 — Modular scoped docs.** Individual markdown files organized by domain. Each is self-contained and only loaded when relevant. Machine configs, workflow guides, and other scoped docs you choose to add.

### Why this exists

1. **Context window efficiency.** An agent working on a Python formatting issue doesn't need your GPU cluster docs. The index lets it pick only what's relevant.
2. **Multi-agent compatibility.** Claude Code, Codex, and future agents all read from the same doc set. Only Layer 1 differs per agent.
3. **Scalability.** Adding a new scoped doc is one file + one line in the index. No monolithic file to maintain.
4. **Secrets stay out of the repo.** Machine docs reference existing config files (`~/.ssh/config`, `~/keys/`, `~/.zshrc`) rather than duplicating secrets. Nothing sensitive is tracked.

---

## Directory Structure

```
agent-config/
├── README.md                    ← you are here
├── INDEX_RULES.md               ← Layer 2: global rules + doc routing
├── CLAUDE.md                    ← Layer 1: Claude Code entry point
├── agents.md                    ← Layer 1: Codex / other agents entry point
├── LICENSE                      ← Apache 2.0
├── .gitignore
│
├── machine/
│   ├── ampere1.md
│   ├── snap.md
│   ├── mac.md
│   ├── sherlock.md
│   └── marlowe.md
│
├── workflows/
│   ├── git-worktrees.md         ← worktree isolation for parallel agents
│   ├── qa-gating.md             ← cross-agent review protocol
│   └── expts-and-results.md     ← experiment structure and results reporting
```

---

## Quick Start

```bash
# Clone to your home directory
git clone https://github.com/brando90/agents-config.git ~/agent-config

# Symlink entry points from home dir
ln -s ~/agent-config/CLAUDE.md ~/CLAUDE.md
ln -s ~/agent-config/agents.md ~/agents.md

# Claude Code will automatically read CLAUDE.md → INDEX_RULES.md
# Codex will automatically read agents.md → INDEX_RULES.md
```

---

## How to Integrate with Your Project Repos

Each project repo should have **two entry points** (`~/your-project/CLAUDE.md` for Claude Code, `~/your-project/agents.md` for Codex) that point to **two indexes**: the home-level `~/agent-config/INDEX_RULES.md` (environment context) and the project's own `~/your-project/docs/agent-docs/INDEX.md` (project-specific docs).

Project docs live in the repo so they're versioned with the code and available to anyone who clones it.

```
~/your-project/
├── CLAUDE.md                         ← points to BOTH indexes
├── agents.md                         ← same for Codex
├── docs/
│   └── agent-docs/
│       ├── INDEX.md                  ← project-specific doc routing
│       ├── architecture.md           ← how the codebase is structured
│       ├── eval-pipeline.md          ← evaluation workflow docs
│       └── conventions.md            ← project-specific conventions
├── src/
└── tests/
```

Your project's `~/your-project/CLAUDE.md` looks like:

```markdown
# Project: your-project

Read the home-level agent index for environment context:
- `~/agent-config/INDEX_RULES.md`

Read the project-level agent index for project-specific docs:
- `~/your-project/docs/agent-docs/INDEX.md`
```

### Fork and customize

1. Fork this repo
2. Fill in `~/agent-config/machine/` with your actual machine specs (non-sensitive info). Reference existing config files (`~/.ssh/config`, `~/keys/`) for secrets — don't duplicate them.
3. Add your own workflow docs

---

## Migrating from a Monolithic CLAUDE.md

If you've been using Claude Code's `/init` command, each project already has a CLAUDE.md with project overview, build commands, architecture docs, and conventions all in one file. This section explains how to migrate that content into the three-layer architecture.

### What migration looks like

**Before** — monolithic CLAUDE.md (200+ lines, everything in one file):
```
my-project/
└── CLAUDE.md    ← project overview, build commands, architecture, conventions, etc.
```

**After** — modular docs with shared environment context:
```
~/my-project/
├── CLAUDE.md                         ← 5-line reference to both indexes
├── agents.md                         ← same reference for Codex
└── docs/agent-docs/
    ├── INDEX.md                      ← project doc routing
    ├── overview.md                   ← project overview + key entry points
    ├── build-and-dev.md              ← setup, build, test commands
    ├── architecture.md               ← codebase structure + key patterns
    └── conventions.md                ← project-specific conventions
```

### Step-by-step migration

#### 1. Back up your old CLAUDE.md

```bash
cd ~/my-project
cp CLAUDE.md CLAUDE.md.bak
```

#### 2. Triage the content

Read through your old CLAUDE.md and sort each section into one of these buckets:

| Bucket | Where it goes | Examples |
|:-------|:-------------|:---------|
| **Project-specific** | `~/my-project/docs/agent-docs/*.md` | Project overview, architecture, build commands, test commands, key entry points, dataset structure, experiment conventions |
| **Already in agent-config** | Drop it (`~/agent-config/` provides it) | Machine specs, SSH config, general workflow rules (QA gating, worktrees), global rules (no secrets, verify before push) |
| **Cross-references to other repos** | `~/my-project/docs/agent-docs/` or drop | `@/path/to/other/CLAUDE.md` references — replace with a reference in your project INDEX.md if still needed |
| **Stale/outdated** | Drop it | Old experiment notes, deprecated commands, hardcoded model IDs that have changed |

#### 3. Create the project docs directory and split the content

```bash
mkdir -p ~/my-project/docs/agent-docs
```

Split your old CLAUDE.md into focused files. A typical project needs 2–4 files. **Don't over-split** — if your old CLAUDE.md was under 80 lines, a single `~/my-project/docs/agent-docs/overview.md` with everything is fine.

**Suggested split for a typical research project:**

- **`overview.md`** — Project purpose (1–3 sentences), environment variables, key entry points
- **`build-and-dev.md`** — Setup, build, test, and lint commands
- **`architecture.md`** — Directory structure, core components, key patterns
- **`conventions.md`** — Only if there are project-specific rules (file naming, experiment layout, etc.)

#### 4. Create the project INDEX.md

```markdown
# INDEX.md — my-project

Load only the docs relevant to your current task.

## Docs

- [`overview.md`](overview.md) — project purpose, env vars, entry points
- [`build-and-dev.md`](build-and-dev.md) — setup, build, test commands
- [`architecture.md`](architecture.md) — codebase structure and key patterns
```

#### 5. Replace CLAUDE.md with the two-reference format

```markdown
# Project: my-project

Read the home-level agent index for environment context:
- `~/agent-config/INDEX_RULES.md`

Read the project-level agent index for project-specific docs:
- `~/my-project/docs/agent-docs/INDEX.md`
```

Optionally create `~/my-project/agents.md` with the same content for Codex compatibility.

#### 6. Delete the backup

Once you've verified the migration, remove the backup:
```bash
rm ~/my-project/CLAUDE.md.bak
```

### Handling common patterns in old CLAUDE.md files

**`@/path/to/other/CLAUDE.md` references** (e.g., `@/dfs/scratch0/brando9/CLAUDE.md`):
These were used to pull in shared context from a cluster-level CLAUDE.md. Agent-config replaces this — the shared context now lives in `~/agent-config/machine/` and `~/agent-config/workflows/`. Drop the `@` reference.

**Machine-specific sections** (GPU setup, cluster paths, Docker auth):
These belong in `~/agent-config/machine/*.md`, not in individual projects. If a machine doc doesn't exist yet, create one in agent-config.

**Experiment-specific sections** (e.g., "Harbor x VeriBench Experiment 35"):
These are project-specific and should go into `~/my-project/docs/agent-docs/`. For large experiment sections, give them their own file (e.g., `~/my-project/docs/agent-docs/experiment-35.md`).

**SOTA model ID lookups** (e.g., "web-search for current models before each run"):
This is a workflow convention. If it applies across projects, add it to `~/agent-config/workflows/`. If project-specific, keep it in `~/my-project/docs/agent-docs/conventions.md`.

### Migration checklist

For each project, verify:
- [ ] `~/my-project/CLAUDE.md` contains only the two-reference format (under 10 lines)
- [ ] `~/my-project/docs/agent-docs/INDEX.md` exists and lists all project doc files
- [ ] No secrets, API keys, or tokens appear in any doc file
- [ ] No hardcoded machine specs (reference `~/agent-config/machine/` instead)
- [ ] Old `~/my-project/CLAUDE.md.bak` has been deleted
- [ ] Agent can still find build/test commands by reading the project INDEX

---

## Security

This is a **public repo**. Never commit API keys, tokens, passwords, or private IPs. Machine docs should reference existing config files (`~/.ssh/config`, `~/keys/`, `~/.zshrc`) for sensitive details rather than duplicating them. Reusable templates should use `<PLACEHOLDER>` markers.


---

## Related Work

The AI coding agent ecosystem is growing fast. Here's how `agents-config` relates to existing tools:

**Multi-Agent Orchestration** — [Ruflo](https://github.com/ruvnet/ruflo) (21.9K stars), [Agent Orchestrator](https://github.com/ComposioHQ/agent-orchestrator) (4.9K), [Emdash](https://github.com/generalaction/emdash) (2.8K), and [Gas Town](https://github.com/steveyegge/gastown) (12.6K) focus on *running* multiple agents — spawning, coordinating, and merging their work. `agents-config` is complementary: it standardizes the *documentation* agents read, not how they're orchestrated.

**Parallel Agent Execution** — [parallel-code](https://github.com/johannesjo/parallel-code) (387 stars) and [parallel-worktrees](https://github.com/SpillwaveSolutions/parallel-worktrees) run agents side-by-side in git worktrees. Our [`workflows/git-worktrees.md`](workflows/git-worktrees.md) describes the same pattern as portable documentation, including an example that combines worktrees with byobu.

**CLAUDE.md Templates & Best Practices** — [claude-code-templates](https://github.com/davila7/claude-code-templates) (23.2K stars), [claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) (19K), [claude-code-showcase](https://github.com/ChrisWiles/claude-code-showcase) (5.5K), and [claude-md-templates](https://github.com/abhishekray07/claude-md-templates) (95) provide example `CLAUDE.md` files and configurations. These are Claude-specific. `agents-config` is agent-agnostic (Layer 1 adapts per agent; Layers 2–3 are shared) and uses doc routing instead of a monolithic file.

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
