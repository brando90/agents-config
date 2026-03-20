# Workflow: QA Gating — Cross-Agent Review

## Default Behavior

**After completing your task, dispatch a review agent before reporting done.**

This is the default, not opt-in. Every agent that finishes work should spawn a reviewer. The reviewer catches mistakes so the human doesn't have to manually review everything.

Skip review ONLY for trivial changes (typo fixes, comment edits, single-line config changes).

---

## How to Dispatch a Reviewer

### If you are Claude Code (CC), dispatch Codex:

```bash
codex "Review all changes in this directory since the last commit on main. \
Flag critical and major issues: logic errors, missing edge cases, incorrect behavior, \
inconsistencies with docs/agent-docs/ if it exists. \
If you find issues, fix them with MINIMAL changes — do not refactor, do not reorganize, \
do not overcomplicate what is already committed. Prefer the simplest correct fix. \
If everything looks correct, just say VERDICT: PASS."
```

### If you are Codex, dispatch Claude Code (CC):

```bash
clauded -p "Review all changes in this directory since the last commit on main. \
Flag critical and major issues: logic errors, missing edge cases, incorrect behavior, \
inconsistencies with docs/agent-docs/ if it exists. \
If you find issues, fix them with MINIMAL changes — do not refactor, do not reorganize, \
do not overcomplicate what is already committed. Prefer the simplest correct fix. \
If everything looks correct, just say VERDICT: PASS."
```

### If you are CC and Codex is unavailable, dispatch another CC instance:

```bash
clauded -p "Review all changes in this directory since the last commit on main. \
Flag critical and major issues only. Fix with minimal changes. \
Do not refactor or overcomplicate. VERDICT: PASS if clean."
```

---

## Reviewer Rules

The reviewer MUST follow these principles:

1. **Fix, don't rewrite.** If the code works but could be "better", leave it alone. Only fix things that are wrong.
2. **Minimal changes only.** A 2-line fix is better than a 50-line refactor that happens to also fix the bug.
3. **Don't overcomplicate what was already committed.** Even if the original approach was suboptimal, if it's correct and simple, keep it.
4. **Correctness over elegance.** Always.
5. **If unsure, leave it and flag it** rather than making a speculative change.

---

## Verdict Format

The reviewer should end with:

```
VERDICT: PASS | FAIL | FIXED
CRITICAL_ISSUES: [count]
MAJOR_ISSUES: [count]
FIXES_APPLIED: [count]
SUMMARY: [1-2 sentences]
```

- **PASS** — no issues found, nothing changed.
- **FIXED** — found issues and applied minimal fixes. Changes are committed.
- **FAIL** — found issues too complex or risky to auto-fix. Flagged for human.

---

## When to Skip Review

- Typo fixes, comment-only edits, single-line config changes.
- User explicitly says "skip review" or "no QA."
- The task was itself a review task (don't recurse — reviewers don't dispatch reviewers).

---

## When Human Review is Still Needed

- Reviewer returns FAIL.
- Changes touch security-critical code (auth, secrets, permissions).
- Changes modify evaluation metrics or scoring logic.
- Merging to main or any shared branch (human makes final merge decision).
