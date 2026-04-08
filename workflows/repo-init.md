# Workflow: Repo Init — Migrating to agents-config

How to onboard an existing or new repo to the `~/agents-config/` three-layer system.

---

## Why migrate

Old pattern: each repo had a monolithic `CLAUDE.md` (or `/init` command) with all rules, machine config, and project docs baked in. This leads to drift, duplication, and stale instructions across repos.

New pattern: global rules and machine/workflow docs live in `~/agents-config/`. Each project's `CLAUDE.md` redirects to agents-config first, then contains only project-specific instructions.

There are two tiers of migration:
- **Minimal** (recommended for most projects): Add the redirect header to `CLAUDE.md`, keep project docs inline, add `agents.md`. This is what most repos need.
- **Full split** (for large projects with 200+ line CLAUDE.md): Split project docs into `docs/agent-docs/` with a project-level `INDEX.md`. See `~/agents-config/README.md` § "Migrating from a Monolithic CLAUDE.md" for the full split procedure.

This checklist covers the **minimal** tier.

---

## Migration checklist

### 1. Add the redirect header to the project's `CLAUDE.md`

The **first line** of the project's `CLAUDE.md` must be:

```
# Claude Code: read `~/agents-config/INDEX_RULES.md` for all agent documentation and routing.
```

This ensures Claude Code loads global rules before project-specific docs.

### 2. Add `agents.md` for Codex / other agents

Create `agents.md` in the project root:

```
# Codex / other agents: read `~/agents-config/INDEX_RULES.md` for all agent documentation and routing.
# Then read `~/PROJECT/CLAUDE.md` for project-specific instructions.
```

Replace `PROJECT` with the actual project directory name.

### 3. Remove stale init patterns

Remove from the project's `CLAUDE.md`:
- Old `@/dfs/...` or `@/path/to/...` references that pointed to cluster-specific CLAUDE.md copies
- Duplicated machine-specific instructions that now live in `~/agents-config/machine/`
- Duplicated workflow instructions (QA, experiments, git worktrees) that now live in `~/agents-config/workflows/`
- Any `/init` slash command definitions that were bootstrapping what agents-config now handles

### 4. Keep project-specific content

The project's `CLAUDE.md` should still contain:
- Project overview and architecture
- Build / test / run commands specific to the project
- Dataset and file format conventions
- Environment variables specific to the project
- Key entry points
- Experiment-specific details (Harbor adapters, metrics, etc.)

### 5. Verify home-level symlinks exist

```bash
# These should already exist (one-time setup):
ls -la ~/CLAUDE.md      # → ~/agents-config/CLAUDE.md
ls -la ~/agents.md      # → ~/agents-config/agents.md

# If missing or stale (backs up existing non-symlink files, then force-creates symlinks):
[ -f ~/CLAUDE.md ] && [ ! -L ~/CLAUDE.md ] && mv ~/CLAUDE.md ~/CLAUDE.md.bak
[ -f ~/agents.md ] && [ ! -L ~/agents.md ] && mv ~/agents.md ~/agents.md.bak
ln -sf ~/agents-config/CLAUDE.md ~/CLAUDE.md
ln -sf ~/agents-config/agents.md ~/agents.md
```

### 6. Test the chain

After migration, verify the full routing chain works:
1. `~/CLAUDE.md` → redirects to `~/agents-config/INDEX_RULES.md`
2. `~/agents-config/INDEX_RULES.md` → global rules + doc routing
3. `~/project/CLAUDE.md` → first line is the redirect header, then project docs
4. `~/project/agents.md` → exists and redirects to both `INDEX_RULES.md` and `CLAUDE.md`
5. Agent loads the right machine config for current environment

---

## Migrated repos

Track repos that have completed migration:

- [x] `~/veribench/` — migrated 2026-04-02
- [ ] `~/veribench-dt/` — pending
- [x] `~/veri-veri-bench/` — migrated 2026-04-07
- [x] `~/agentic-nl-fl-maths/` — migrated 2026-04-07
