# Workflow: QA Structural — Anti-Degradation Refactoring Gate

**TLDR:** A pre-merge structural review focused on preventing the
"agent refactor that quietly degrades the codebase" failure mode
(over-abstraction, dead helpers, half-finished migrations,
silently-broken contracts). Pair with `qa-correctness.md` — correctness
QA proves the diff *works*; structural QA proves the diff doesn't
*rot the repo*.

Motivated by two complementary findings:

1. **SlopCodeBench** (Orlanski et al., 2026, arXiv:2603.24755): agent code
   degrades monotonically — erosion rises in 80% of trajectories, verbosity
   in 89.8%. Prompt-side interventions lower the intercept ~34% but not the
   degradation rate.

2. **RAMP** (Denisov-Blanch, Agarwal, Azaletskiy et al., ASE 2026): repos
   with committed AI config (rules, standards, architecture docs) see ~3.3x
   less complexity growth and ~3.4x less warning increases. The L1→L2 gap
   (nothing vs. basic config) is the biggest jump. 80% of AI config is
   set-and-forget.

This gate combines both: check config first (RAMP), then measure and fix
code quality (SlopCodeBench).

**This file is the reference definition of structural QA checks.** The QA
reviewer dispatched per [`qa-correctness.md`](qa-correctness.md) handles both
correctness and structural quality in a single pass. This document defines
what structural QA checks entail — the phases, metrics, and hard rules. The
reviewer's QA prompt includes the core structural checks; this file provides
the full detail and motivation.

## Default Behavior

**The QA reviewer (dispatched per qa-correctness.md) includes structural checks
in its pass on any repo with substantial source code.** Structural checks are
skipped for markdown-only or config-only repos. The underlying experiment is
still unvalidated, so the reviewer should report `SKIP` when the repo or task
does not fit.

---

## When to Run

- After every non-trivial feature addition or extension, before the next
  implementation iteration begins.
- After multiple agent-driven iterations on the same codebase (3+ rounds).
- When you notice god functions growing, duplication spreading, or erosion
  increasing.

## When to Skip

- Markdown-only or config-only repos (no meaningful source code to measure).
- Trivial changes (typo fixes, comment edits, single-line config changes).
- User explicitly says "skip structural QA."
- The task was itself a refactoring task (don't recurse).

---

## Structural QA Phases

The QA reviewer should follow these phases for the structural portion of its
review. See [`qa-correctness.md`](qa-correctness.md) for the dispatch mechanism.

### Phase -1: Configuration Audit (RAMP-motivated)

Before touching code, check whether the repo has committed AI config artifacts
that RAMP associates with ~3x less quality degradation. The L1→L2 gap is the
largest observed difference in RAMP's data.

Check for: (1) Rules file (CLAUDE.md, .cursorrules, copilot-instructions.md,
agents.md) with actionable directives, (2) Coding standards with conventions,
(3) Architecture docs with module boundaries/data flow, (4) Agent definitions
with roles/tool restrictions (Level 3), (5) Workflow coordination (Level 4).

Report RAMP level (L1/L2/L3/L4). If L1: flag as #1 recommendation —
recommend creating rules file + coding standards. Since 80% of AI config is
never modified after commit, emphasize getting it right first time.
Then proceed to Phase 0 (config gaps don't block code assessment).
If L2+: note level and proceed.

### Phase 0: Measure Baseline (SlopCodeBench-motivated)

1. Run radon cc -s -a -n B . — filter to CC > 10.
2. Erosion = sum(mass(f) for CC>10) / sum(mass(f) for all f),
   where mass(f) = CC(f) * sqrt(SLOC(f)).
3. Verbosity = |flagged_lines UNION clone_lines| / total_LOC.
   Use ast-grep/linter + clone detection (jscpd, duplo, pylint duplicate-code).
   Union with deduplication, not sum.

Exclude tests, docs, generated code, vendored deps.
If tools unavailable, estimate and flag as "estimated."

### Phase 1: Audit (do NOT fix yet)

1. God functions (CC > 10 or >60 lines) — prioritize by mass, highest first.
   (Note: duplication is where committed config helps most — 33% at L1 vs
   near-zero at L2+ per RAMP.)
2. Structural duplication across files.
3. Verbose anti-patterns: single-use vars, identity wrappers, defensive checks
   for impossible states, unnecessary casts, 3+ nesting, if/elif ladders,
   silent except blocks, obvious-restatement comments, unused imports, dead code.
4. Architectural dead-ends — flag only, for human review.

### Phase 2: Refactor Plan

For each item (except dead-ends): extract but don't over-extract, deduplicate
via abstraction, replace ladders with tables, delete don't comment out, preserve
public interface, minimize diff, budget ~100 lines of diff per item max.

### Phase 3: Execute

Priority: highest-mass god functions > duplication > anti-patterns.
Run tests after each change. Revert and skip if tests break.

### Phase 4: Measure & Report

Report:
- RAMP level + missing artifacts + config quality notes
- Erosion (before -> after)
- Verbosity (before -> after)
- Highest-CC function (before -> after)
- Diff size, functions extracted, duplications removed, anti-patterns fixed
- Items skipped and why
- Architectural dead-ends flagged

### Hard Rules

- Zero functional changes. Skip if unsure.
- No new deps. No new source files unless extracting a module.
- New AI config files (rules, standards) are the exception to no-new-files.
- Run tests. Flag as "unverified" if you cannot.
- Do not touch test files (except shared test utilities).
- No abstractions for single-use cases. Respect diff budget.
- Config recommendations are recommendations — team decides content.

---

## Detailed Structural Report Format

```
VERDICT: PASS | IMPROVED | SKIP
RAMP_LEVEL: [L1 | L2 | L3 | L4]
CONFIG_GAPS: [list or "none"]
CONFIG_QUALITY_NOTES: [brief notes on existing config quality, or "n/a"]
EROSION_BEFORE: [score]
EROSION_AFTER: [score]
VERBOSITY_BEFORE: [score]
VERBOSITY_AFTER: [score]
GOD_FUNCTIONS_FIXED: [count]
DUPLICATIONS_REMOVED: [count]
ANTIPATTERNS_FIXED: [count]
ARCH_DEADENDS_FLAGGED: [count]
SUMMARY: [1-2 sentences]
```

- **PASS** — metrics are healthy, no refactoring needed.
- **IMPROVED** — found degradation, applied refactoring, metrics improved.
- **SKIP** — no substantial source code to measure (e.g., markdown-only repo).

Use this detailed block when a task explicitly asks for structural metrics or
when the reviewer wants to keep internal structural notes. The required
outward-facing QA verdict is the combined block in `qa-correctness.md`.

---

## QA Integration

The QA reviewer dispatched per [`qa-correctness.md`](qa-correctness.md) handles
both correctness and structural quality in a single pass. This document defines
the structural checks and metrics; the dispatch mechanism lives in
qa-correctness.md.

The reviewer's combined verdict includes a `STRUCTURAL:` line:

```
VERDICT: PASS | FAIL | FIXED
CRITICAL_ISSUES: [count]
MAJOR_ISSUES: [count]
FIXES_APPLIED: [count]
STRUCTURAL: PASS | IMPROVED | SKIP
SUMMARY: [1-2 sentences]
```

See [`qa-correctness.md`](qa-correctness.md) for the full cross-agent review
protocol.

---

## Background: Why This Exists

Two papers motivate this gate:

**SlopCodeBench** (what degrades and why prompts aren't enough):
- God functions accumulate branches (e.g., main() growing from 84 to 1099
  lines, CC 29 to 285 over 8 checkpoints)
- Structural duplication accounts for 66% of verbosity growth
- These patterns pass tests but make each subsequent iteration harder
- Prompt-only interventions (anti_slop, plan_first) shift the intercept
  ~34% but the degradation slope is unchanged

**RAMP** (why committed config matters):
- Repos without AI config (L1) see ~96% complexity growth vs. ~29% at L2+
- Static-analysis warnings: ~45% at L1 vs. ~13% at L2+
- Duplication: ~33% at L1 vs. near-zero at L2+
- Velocity gains (~26% more commits) are identical regardless — agents
  accelerate everyone; config determines who pays the quality price
- 80% of AI config is set-and-forget — initial quality matters

The correctness QA gate catches bugs. This structural QA gate catches decay
(SlopCodeBench) and missing defenses (RAMP). Together they form a more
complete quality chain.

For the full analysis and experiment design, see
`~/agents-config/experiments/00_refactor_qa_gate/analysis.md`.
