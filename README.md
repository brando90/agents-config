# Agent-Config: Modular Documentation Architecture for Multi-Agent Coding Workflows

A modular, agent-agnostic documentation system for AI coding agents (Claude Code, Codex, and beyond). Designed for scalability and context-window efficiency.

As codebases scale past 30-50k LOC (lines of code), monolithic agent instruction files (a single `CLAUDE.md` or `agents.md`) waste context window on irrelevant details and don't generalize across agents. This repo implements a three-layer architecture that solves both problems.

**Designed by [Brando Miranda](https://brando90.github.io/brandomiranda/) (Stanford CS PhD).** Inspired by [Yegor Denisov-Blanch](https://x.com/yegordb)'s insight that modular documentation is essential for multi-agent workflows at scale.

**Contributions welcomed and encouraged!** Open a [GitHub Issue](https://github.com/brando90/agents-config/issues), start a [Discussion](https://github.com/brando90/agents-config/discussions), or submit a PR (pull request).

---

## The Three-Layer Architecture

```
←────── Layer 1: Entry Points ────────→   ←── Layer 2 ──→   ←── Layer 3: Scoped Docs ──→
agent-config flow (shared env — abbreviating ~/agents-config/ as ~/ac/ for width):

       ~/                ~/ac/                  ~/ac/                ~/ac/
┌──────────────┐   ┌──────────────────┐
│ ~/CLAUDE.md  │──▸│ ~/ac/CLAUDE.md   │   ┌────────────────────┐   ┌──────────────────────┐
│              │   │                  │   │                    │   │ ~/ac/machine/        │
│ ~/agents.md  │──▸│ ~/ac/agents.md   │──▸│~/ac/INDEX_RULES.md │──▸│ ~/ac/workflows/      │
│              │   │                  │   │                    │   │ ~/ac/writing/        │
│              │   │                  │   │                    │   └──────────────────────┘
└──────────────┘   └──────────────────┘   └────────────────────┘
   (symlinks)       "read ~/agents-config/INDEX_RULES.md"  (rules + routing)  (loaded on demand)

Project repo flow (e.g., ~/vb/ — layers span two repos):

┌────────────────────┐
│ ~/vb/CLAUDE.md     │──▸ ~/agents-config/INDEX_RULES.md  # shared env context
│                    │──▸ ~/vb/docs/agent-docs/INDEX.md  # repo-specific docs
├────────────────────┤
│ ~/vb/agents.md     │──▸ ~/agents-config/INDEX_RULES.md  # shared env context
│                    │──▸ ~/vb/docs/agent-docs/INDEX.md  # repo-specific docs
└────────────────────┘

~/agents-config/ (~/ac/) outline:
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ CLAUDE.md        ← Layer 1 entry; text ref ──▸ INDEX_RULES.md                            │
│ agents.md        ← Layer 1 entry; text ref ──▸ INDEX_RULES.md                            │
│ INDEX_RULES.md   ← Layer 2 global rules + doc routing; refs ──▸ machine/, workflows/,     │
│                  writing/                                                                  │
│ README.md        ← repo docs (you are here)                                              │
│ machine/         ← Layer 3: per-machine configs (mac.md, snap.md, sherlock.md, …)        │
│ workflows/       ← Layer 3: reusable workflows (qa-correctness.md, git-worktrees.md, …)  │
│ writing/         ← Layer 3: reusable writing guides (ml_research_writing.md, …)           │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

**Layer 1 — Agent-specific entry points.** `CLAUDE.md` (for Claude Code) and `agents.md` (for Codex) live in the repo root. Their header lines bootstrap or refresh `~/agents-config/` and direct the agent to `~/agents-config/INDEX_RULES.md`. From the home directory, `~/CLAUDE.md` and `~/agents.md` are filesystem symlinks to these files, so the agent finds the same entry point regardless of where it's launched.

**Layer 2 — Tiered rules & doc routing.** `INDEX_RULES.md` contains two things: (1) rules organized into three tiers — **Hard Rules** (every response, never skip: no secrets, QA gating, TLDR, config refresh), **Trigger Rules** (mandatory when triggered: agents-config edits, PRs, GPU jobs, Mega QA, LaTeX edits for ML papers), and **Guidelines** (best practices: anchored paths, context efficiency) — and (2) doc routing that groups docs by topic with concise path-based "references" — file paths written as text (e.g., `~/agents-config/machine/mac.md`) that tell the agent where to look — so the agent only loads what's relevant to the current task.

**Layer 3 — Modular scoped docs.** Individual markdown files organized by domain. Each is self-contained and only loaded when relevant. Machine configs, workflow guides, writing guides, and other scoped docs you choose to add.

### Why this exists

1. **Context window efficiency.** An agent working on a Python formatting issue doesn't need your GPU cluster docs. The index lets it pick only what's relevant.
2. **Multi-agent compatibility.** Claude Code, Codex, and future agents all read from the same doc set. Only Layer 1 differs per agent.
3. **Scalability.** Adding a new scoped doc is one file + one line in the index. No monolithic file to maintain.
4. **Secrets stay out of the repo.** Machine docs reference existing config files (`~/.ssh/config`, `~/keys/`, `~/.zshrc`) rather than duplicating secrets. Nothing sensitive is tracked.

---

## Directory Structure

```
agents-config/
├── README.md                    ← you are here
├── INDEX_RULES.md               ← Layer 2: global rules + doc routing
├── CLAUDE.md                    ← Layer 1: Claude Code entry point
├── agents.md                    ← Layer 1: Codex / other agents entry point
├── LICENSE                      ← Apache 2.0
│
├── init_no_passwords_snap_kinit.md              ← one-time keytab setup for passwordless SSH to SNAP
├── cursor_ssh_kerberos_todo.md                  ← Cursor SSH + Kerberos design notes & TODO tracking
├── todo_infinite_reauth_kinit_server_side.md    ← TODO: server-side auto-renewal (eliminate krbtmux/reauth)
│
├── machine/
│   ├── ampere1.md               ← SNAP ampere1 node
│   ├── mercury1.md              ← SNAP mercury1 node (10x A4000-16GB)
│   ├── mercury2.md              ← SNAP mercury2 node (10x A4000-16GB)
│   ├── snap.md                  ← Stanford SNAP cluster
│   ├── snap-init.md             ← first-time setup & verification for new SNAP nodes
│   ├── mac.md                   ← local macOS dev
│   ├── sherlock.md              ← Stanford Sherlock HPC
│   └── marlowe.md               ← Stanford Marlowe cluster
│
├── workflows/
│   ├── qa-correctness.md        ← cross-agent QA review (correctness + structural)
│   ├── qa-structural.md         ← structural QA reference (metrics, checks)
│   ├── expts-and-results.md     ← experiment structure and results reporting
│   ├── dfs-job-watcher.md       ← DFS job queue for SNAP (submit from one node, run on any)
│   ├── git-worktrees.md         ← worktree isolation for parallel agents
│   ├── repo-init.md             ← migrating projects to this pattern
│   ├── tweprints.md             ← tweet thread format
│   └── blog-posts.md            ← SAIL-style blog posts
│
├── writing/
│   └── ml_research_writing.md   ← ML research paper writing guide for `.tex` edits
│
└── tests/
    └── dummy_experiment/        ← workflow validation (tiny MLP + W&B)
```

---

## Quick Start

```bash
# Clone to your home directory
git clone https://github.com/brando90/agents-config.git ~/agents-config

# Symlink entry points from home dir
ln -s ~/agents-config/CLAUDE.md ~/CLAUDE.md
ln -s ~/agents-config/agents.md ~/agents.md

# Claude Code will automatically read CLAUDE.md → INDEX_RULES.md
# Codex will automatically read agents.md → INDEX_RULES.md
```

---

## New Server Setup

Setting up a new SNAP node? See [`machine/snap-init.md`](machine/snap-init.md) -- copy-paste prompt that checks/fixes all symlinks, auth, tools, keys, and GPUs on a fresh SNAP node.

**Important convention:** On SNAP, all project directories under `~/` (LFS) must be **symlinks** to their canonical location on `/dfs/scratch0/<user>/`. For example, `~/veribench` → `/dfs/scratch0/brando9/veribench`. This ensures every server sees the same repo state. Never clone or copy repos directly to LFS. See [`machine/snap.md`](machine/snap.md) for details.

---

## Remote Access (Claude Remote Control & Codex)

### Claude Remote Control — setup

Remote Control (RC) lets you hand off a Claude Code session to your phone or another device via `claude.ai/code`. It requires a **full claude.ai login** — long-lived env vars like `CLAUDE_CODE_OAUTH_TOKEN` block RC.

#### Mac (zsh + Cursor)

Cursor injects `CLAUDE_CODE_OAUTH_TOKEN` into its terminal env. tmux/byobu sessions started from Cursor inherit it, silently blocking RC.

**One-time fix** — add to `~/.zshrc`:

```bash
# Strip Cursor-injected CLAUDE_CODE_OAUTH_TOKEN inside tmux/byobu — blocks RC
if [ -n "$TMUX" ]; then
  unset CLAUDE_CODE_OAUTH_TOKEN
fi
```

Also make sure `CLAUDE_CODE_OAUTH_TOKEN` is NOT exported anywhere in `~/.zshrc` or `~/.zprofile`:

```bash
# Check:
grep -n 'CLAUDE_CODE_OAUTH_TOKEN' ~/.zshrc ~/.zprofile 2>/dev/null
# Any uncommented export lines → comment them out
```

Then auth (one-time):

```bash
claude auth logout
claude auth login        # signs in via browser
claude auth status --text  # verify: "Claude Max Account", no env overrides
claude remote-control    # success = Environment ID + claude.ai/code URL
```

#### SNAP servers (bash + DFS)

On SNAP, shell config lives at `/dfs/scratch0/<user>/.bashrc` (shared across all nodes via symlink). Fix it **once on DFS** and all servers get it.

**Step 1 — Remove `CLAUDE_CODE_OAUTH_TOKEN` from `.bashrc`:**

```bash
DFS="/dfs/scratch0/brando9"

# Find it
grep -n 'CLAUDE_CODE_OAUTH_TOKEN' "${DFS}/.bashrc"

# Comment it out (if found)
sed -i 's/^export CLAUDE_CODE_OAUTH_TOKEN/#export CLAUDE_CODE_OAUTH_TOKEN/' "${DFS}/.bashrc"
```

**Step 2 — Add tmux guard to `.bashrc`:**

Add this block to `${DFS}/.bashrc` (works for krbtmux, tmux, byobu):

```bash
# Strip CLAUDE_CODE_OAUTH_TOKEN inside tmux/byobu/krbtmux — blocks Remote Control
if [ -n "$TMUX" ]; then
  unset CLAUDE_CODE_OAUTH_TOKEN
fi
```

**Step 3 — Auth (one-time, from any server):**

```bash
source ~/.bashrc
claude auth logout
claude auth login
# No browser on server — copy the URL, open on Mac/phone, sign in, paste code back
claude auth status --text  # verify: "Claude Max Account", no env overrides
```

**Step 4 — Share auth across all nodes via DFS:**

Claude stores credentials in `~/.claude/`. On SNAP, `$HOME` is per-server LFS, so auth is per-server by default. Fix by symlinking `~/.claude/` to DFS:

```bash
# On the FIRST server (after claude auth login succeeds):
mv ~/.claude "${DFS}/.claude"
ln -sfn "${DFS}/.claude" ~/.claude

# On every OTHER server (or in new-node setup):
rm -rf ~/.claude
ln -sfn "${DFS}/.claude" ~/.claude
```

**Step 5 — Start RC:**

```bash
# For persistent sessions, use krbtmux first:
/afs/cs/software/bin/krbtmux
/afs/cs/software/bin/reauth

# Then start RC inside the tmux session:
claude remote-control
# Open claude.ai/code on phone/Mac to connect
```

### Codex — no RC equivalent (use tmux)

Codex CLI has no `remote-control` command. Auth is via **ChatGPT login** (interactive) or **API key** (automation). Persistence over SSH uses tmux:

```bash
# Start a persistent Codex session
tmux new -As codex
codex  # sign in with ChatGPT when prompted, or set OPENAI_API_KEY

# Reconnect later from any device
ssh <server> -t 'tmux attach -t codex'
```

### Server rollout checklist

```
[ ] Comment out CLAUDE_CODE_OAUTH_TOKEN in DFS .bashrc (one edit, all servers)
[ ] Add tmux guard (unset inside TMUX) to DFS .bashrc
[ ] Remove primaryApiKey from ~/.claude/config.json (forces API mode, blocks RC)
[ ] claude auth login (once, from any server — DFS shares it)
[ ] Symlink ~/.claude/ → DFS on each server
[ ] Verify: claude auth status --text (no env overrides)
[ ] Accept workspace trust: run `claude` in the working directory, accept the trust dialog, then exit
[ ] Start: claude remote-control
[ ] Mac: add tmux guard to ~/.zshrc, verify RC works in tmux
[ ] For Codex: choose ChatGPT login or API key, run inside tmux
```

### Troubleshooting Remote Control

RC can fail silently for several reasons. Use this diagnostic sequence:

**1. Check env vars in your current shell:**

```bash
echo "TOKEN=${CLAUDE_CODE_OAUTH_TOKEN:-NOT_SET}"
echo "API_KEY=${ANTHROPIC_API_KEY:-NOT_SET}"
claude auth status --text
```

- If `TOKEN` is set → it overrides OAuth login and blocks RC. Fix: `unset CLAUDE_CODE_OAUTH_TOKEN`
- If auth status says `Auth token: CLAUDE_CODE_OAUTH_TOKEN` → same problem, token is taking priority
- If auth status says `Claude Max Account` → auth is fine, problem is elsewhere

**2. "Long-lived tokens are limited to inference-only":**

RC requires a browser-based OAuth login. This error means Claude is using either:
- `CLAUDE_CODE_OAUTH_TOKEN` env var (even if commented out in `.bashrc`, your current shell may still have it from before the fix)
- `primaryApiKey` in `~/.claude/config.json`

Fix:
```bash
# Remove API key from config
echo '{}' > ~/.claude/config.json

# Unset env var
unset CLAUDE_CODE_OAUTH_TOKEN

# Re-auth via browser
claude auth logout && claude auth login
```

**3. "Workspace not trusted":**

Claude must accept the workspace trust dialog before RC can start. Run `claude` (not `claude remote-control`) in the target directory, accept the trust prompt, then exit and retry `claude remote-control`.

**4. Cursor SSH / IDE-injected tokens:**

Cursor (and similar IDEs) inject `CLAUDE_CODE_OAUTH_TOKEN` into their terminal environment. This token persists for the lifetime of the SSH connection — even after you comment it out of `.bashrc`. Every terminal tab and child process inherits it.

Fix: **Reconnect the SSH extension** (or restart the IDE remote session) after editing `.bashrc`. Alternatively, run `unset CLAUDE_CODE_OAUTH_TOKEN` in each terminal before using `claude`.

**5. Full diagnostic one-liner:**

```bash
unset CLAUDE_CODE_OAUTH_TOKEN && echo '{}' > ~/.claude/config.json && claude auth status --text && claude remote-control
```

### Verify node setup

After setup, see [`machine/snap-init.md`](machine/snap-init.md) for a paste-into-Claude-Code prompt that checks paths, symlinks, RC auth, tools, keys, and GPUs.

---

## DFS Job Queue (Running Experiments Across SNAP Nodes)

SNAP has no Slurm — you SSH into individual nodes. The DFS job queue lets you submit experiment scripts from **any one node** and have watchers on the other nodes automatically pick them up and run them. You don't need to SSH into each server, set up environments, or babysit processes.

**How it works:**

1. Each SNAP node runs a **watcher daemon** (in tmux or via `clauded`). The daemon polls `~/dfs/job_queue/pending/` every 15 seconds.
2. You (or an agent) **drop a script** into `pending/` from any node. Because `~/dfs/` is on the shared DFS, every node sees it immediately.
3. The first watcher to see the job **atomically claims it** (NFS-safe hardlink protocol — no double-execution even with multiple nodes racing) and moves it to `running/`.
4. The watcher **executes the script**, inheriting the host's environment (`CUDA_VISIBLE_DEVICES`, API keys, etc.), with a 4-hour timeout that kills the entire process tree to free GPUs.
5. When it finishes, the job moves to `completed/` (exit 0) or `failed/` (non-zero or timeout). Logs go to `logs/`.

**The key idea:** You log into one server, submit jobs, and walk away. The other servers are already listening. No coordinator, no scheduler, no manual SSH — just a shared directory and a simple protocol.

```
~/dfs/job_queue/
    pending/      ← drop jobs here (from any node)
    running/      ← claimed by a watcher (job.sh___<hostname>)
    completed/    ← exit 0
    failed/       ← exit != 0 or timeout
    logs/         ← per-job stdout+stderr
```

**Code:** [`ultimate-utils/py_src/uutils/job_scheduler_uu/`](https://github.com/brando90/ultimate-utils/tree/main/py_src/uutils/job_scheduler_uu) (scheduler, submitter, tmux launcher).
**Full usage guide:** [`workflows/dfs-job-watcher.md`](workflows/dfs-job-watcher.md) (start/stop commands, submit examples, atomic claim details).

---

## How to Integrate with Your Project Repos

Each project repo should have **two entry points** (`~/your-project/CLAUDE.md` for Claude Code, `~/your-project/agents.md` for Codex) that point to **two indexes**: the home-level `~/agents-config/INDEX_RULES.md` (environment context) and the project's own `~/your-project/docs/agent-docs/INDEX.md` (project-specific docs).

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
- `~/agents-config/INDEX_RULES.md`

Read the project-level agent index for project-specific docs:
- `~/your-project/docs/agent-docs/INDEX.md`
```

### Fork and customize

1. Fork this repo
2. Fill in `~/agents-config/machine/` with your actual machine specs (non-sensitive info). Reference existing config files (`~/.ssh/config`, `~/keys/`) for secrets — don't duplicate them.
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
| **Already in agent-config** | Drop it (`~/agents-config/` provides it) | Machine specs, SSH config, general workflow rules (QA gating, worktrees), global rules (no secrets, verify before push) |
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
- `~/agents-config/INDEX_RULES.md`

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
These were used to pull in shared context from a cluster-level CLAUDE.md. Agent-config replaces this — the shared context now lives in `~/agents-config/machine/` and `~/agents-config/workflows/`. Drop the `@` reference.

**Machine-specific sections** (GPU setup, cluster paths, Docker auth):
These belong in `~/agents-config/machine/*.md`, not in individual projects. If a machine doc doesn't exist yet, create one in agent-config.

**Experiment-specific sections** (e.g., "Harbor x VeriBench Experiment 35"):
These are project-specific and should go into `~/my-project/docs/agent-docs/`. For large experiment sections, give them their own file (e.g., `~/my-project/docs/agent-docs/experiment-35.md`).

**SOTA model ID lookups** (e.g., "web-search for current models before each run"):
This is a workflow convention. If it applies across projects, add it to `~/agents-config/workflows/`. If project-specific, keep it in `~/my-project/docs/agent-docs/conventions.md`.

### Migration checklist

For each project, verify:
- [ ] `~/my-project/CLAUDE.md` contains only the two-reference format (under 10 lines)
- [ ] `~/my-project/docs/agent-docs/INDEX.md` exists and lists all project doc files
- [ ] No secrets, API keys, or tokens appear in any doc file
- [ ] No hardcoded machine specs (reference `~/agents-config/machine/` instead)
- [ ] Old `~/my-project/CLAUDE.md.bak` has been deleted
- [ ] Agent can still find build/test commands by reading the project INDEX

---

## Initialization Guides

- **[Passwordless SSH to SNAP (Kerberos keytab)](init_no_passwords_snap_kinit.md)** — One-time setup so SSH and Cursor never prompt for a password on SNAP servers. Uses a Kerberos keytab + launchd auto-renewal. See also: [Cursor SSH + Kerberos TODO](cursor_ssh_kerberos_todo.md) for the original design notes.
- **[TODO: Infinite server-side Kerberos renewal](todo_infinite_reauth_kinit_server_side.md)** — Eliminate `krbtmux`/`reauth` by auto-renewing server-side tickets via keytab + cron. Covers tmux, byobu, Cursor, and background jobs.

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
  author = {Brando Miranda and Claude (Anthropic) and Codex (OpenAI) and Cursor (Anysphere)},
  title = {Agent-Config: A Modular, Agent-Agnostic Documentation Architecture for Multi-Agent Coding Workflows},
  year = {2026},
  howpublished = {\url{https://github.com/brando90/agents-config}},
}
```

We list Claude (Anthropic), Codex (OpenAI), and Cursor (Anysphere) as co-authors because this system was designed collaboratively between human and AI agents. While AI co-authorship is not yet widely accepted in academic venues, we believe transparency about AI contributions is important and reflects the future of human-AI collaboration.

---

## Acknowledgments

We thank [Yegor Denisov-Blanch](https://x.com/yegordb) for the original insight about modular, agent-agnostic documentation for multi-agent coding workflows, which inspired this project. (We plan to ask Yegor if he'd like to be listed as a co-author — pending his response.)
