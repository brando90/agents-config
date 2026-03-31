# Workflow: QA Structural — Anti-Degradation Refactoring Gate

Motivated by SlopCodeBench (Orlanski et al., 2026, arXiv:2603.24755), which
shows that agent-generated code degrades monotonically under iterative extension:
erosion rises in 80% of trajectories, verbosity in 89.8%. Prompt-side
interventions lower the starting point but not the degradation rate. This gate
is a tooling-side intervention targeting the rate.

**This is the second step of the QA chain.** Run it after
[`qa-correctness.md`](qa-correctness.md) passes.

## Default Behavior

**After correctness QA passes, run the structural QA gate on any repo with
substantial source code (not markdown-only repos like agents-config itself).**

This is opt-in for now — the effectiveness of this gate at bending the
degradation slope is untested. Run it when the codebase has been through
multiple agent-driven iterations and you want to check for structural decay.

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

## How to Dispatch

### If you are Claude Code (CC), dispatch Codex:

```bash
codex exec --full-auto "$(cat <<'PROMPT'
You are a refactoring specialist. Your ONLY job is to improve the structural
quality of the existing codebase. You must NOT add features, change behavior,
or modify any public API. Every test that passed before must pass after.

## Phase 0: Measure Baseline

Before changing anything, compute quantitative baselines. Use actual tools,
not estimates.

1. **Cyclomatic complexity per function.** Run `radon cc -s -a -n B .`
   (or equivalent for your language) to get exact CC scores. Filter to
   functions with CC > 10 (following Radon's established bounds). Note:
   `-n B` shows rank B and above (CC >= 6), giving visibility into
   functions approaching the threshold too.

2. **Structural erosion.** Compute:
   - mass(f) = CC(f) * sqrt(SLOC(f))
   - Erosion = sum(mass(f) for f where CC(f) > 10) / sum(mass(f) for all f)

3. **Verbosity (SlopCodeBench-inspired proxy).**
   - Run ast-grep rules or a linter to identify verbose anti-patterns.
   - Run clone detection (jscpd, duplo, or pylint duplicate-code).
   - Verbosity = |flagged_lines UNION clone_lines| / total_LOC
     (union with deduplication, not sum)

Exclude test files, docs (*.md), generated code, and vendored dependencies.
If tools are unavailable, fall back to manual estimation and flag as "estimated."

## Phase 1: Audit

Identify and list (do NOT fix yet):
1. God functions (CC > 10 or >60 lines) — prioritize by mass, highest first
2. Structural duplication across files
3. Verbose anti-patterns (single-use vars, identity wrappers, defensive
   checks for impossible states, unnecessary casts, 3+ nesting levels,
   if/elif ladders, silent except blocks, obvious-restatement comments,
   unused imports, dead code)
4. Architectural dead-ends (flag only, for human review — do NOT fix)

## Phase 2: Refactor Plan

For each audit item (except architectural dead-ends), state the specific
refactoring. Follow: extract but don't over-extract, deduplicate via
abstraction, replace ladders with tables, delete don't comment out, preserve
public interface, minimize diff, budget ~100 lines of diff per item max.

## Phase 3: Execute

Apply in priority order: highest-mass god functions first, then duplication,
then anti-patterns. Run tests after each significant change. Revert and
skip anything that breaks tests.

## Phase 4: Measure & Report

Recompute Phase 0 metrics. Report before/after comparison table:
erosion, verbosity, highest-CC function, total diff size, counts of
functions extracted / duplications removed / anti-patterns fixed,
items skipped, architectural dead-ends flagged.

## Hard Rules

- Zero functional changes. Skip if unsure.
- No new dependencies.
- No new files unless extracting a module.
- Run tests. Flag as "unverified" if you cannot.
- Do not touch test files (except shared test utilities).
- Do not introduce abstractions for single-use cases.

End with exactly:
VERDICT: PASS | IMPROVED | SKIP
EROSION_BEFORE: [score]
EROSION_AFTER: [score]
VERBOSITY_BEFORE: [score]
VERBOSITY_AFTER: [score]
GOD_FUNCTIONS_FIXED: [count]
DUPLICATIONS_REMOVED: [count]
ANTIPATTERNS_FIXED: [count]
ARCH_DEADENDS_FLAGGED: [count]
SUMMARY: [1-2 sentences]
If the codebase has no substantial source code, use SKIP.
PROMPT
)"
```

### If you are Codex, dispatch Claude Code (CC):

```bash
clauded -p "$(cat <<'PROMPT'
<same prompt as above>
PROMPT
)"
```

If skip-permissions mode is not appropriate for your environment, run the same
prompt in interactive `claude` instead of using the unattended `clauded -p` path.

### Self-dispatch (same agent):

Use the same prompt above with whichever agent you are, dispatching the
highest-capability model available.

---

## Verdict Format

```
VERDICT: PASS | IMPROVED | SKIP
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

The caller should relay this block in the final QA summary alongside the
correctness QA verdict.

---

## The Two-Step QA Chain

The full QA chain after completing a task:

1. **Correctness QA** ([`qa-correctness.md`](qa-correctness.md)) — catch logic
   errors, missing edge cases, broken behavior. Must pass first.
2. **Structural QA** (this doc) — catch degradation: god functions, duplication,
   verbose anti-patterns, architectural dead-ends. Runs after correctness passes.

Both verdicts should be reported together:

```
## QA Summary
CORRECTNESS: PASS | FAIL | FIXED
STRUCTURAL: PASS | IMPROVED | SKIP
```

---

## Background: Why This Exists

SlopCodeBench shows that when agents iteratively extend their own code:
- God functions accumulate branches (e.g., main() growing from 84 to 1099
  lines, CC 29 to 285 over 8 checkpoints)
- Structural duplication accounts for 66% of verbosity growth
- These patterns pass tests but make each subsequent iteration harder
- Prompt-only interventions (anti_slop, plan_first) shift the intercept
  ~34% but the degradation slope is unchanged

The correctness QA gate catches bugs. This structural QA gate catches decay.
Together they form a more complete quality chain.

For the full analysis and experiment design, see
`~/agent-config/experiments/00_refactor_qa_gate/analysis.md`.
