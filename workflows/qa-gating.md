# Workflow: Cross-Agent QA Review (Opt-In)

<!-- TODO: define scoring criteria for QA pass/fail -->

A protocol for using a second AI agent to review code before pushing or creating a PR.

---

## When to Trigger

This is **opt-in only.** The human must explicitly request it. Do not auto-trigger.

Good times to use QA gating:
- Before creating a PR for a complex change
- Before pushing to a shared branch
- When the primary agent made architectural decisions you want a second opinion on
- When you explicitly ask: "have Codex review this" or "cross-agent review"

---

## How It Works

1. **Primary agent** completes its code edits (e.g., Claude Code writes a feature).
2. **Human** reviews the diff and decides a second opinion would be valuable.
3. **Human** spawns a second agent of a different type in the same repo (or worktree).
4. **Reviewer agent** audits the diff, looking for:
   - Logic errors or edge cases
   - Security issues (injection, secrets, auth bypass)
   - Missing error handling at system boundaries
   - Unintended side effects
   - Style/convention violations per project rules
5. **Reviewer agent** reports findings. It does NOT make edits unless asked.
6. **Human** is always the final reviewer. The QA agent's findings are advisory.

---

## Review Prompt Template

Paste this to the reviewer agent:

```
Review the changes on this branch vs main. Check for:
1. Logic errors or edge cases that would cause bugs
2. Security issues (injection, secrets, auth bypass)
3. Missing error handling at system boundaries
4. Unintended side effects or regressions
5. Convention violations per this project's CLAUDE.md / agents.md

Do NOT make edits. Report findings as a numbered list with file:line references.
If everything looks good, say so.
```

---

## Cross-Agent Pairings

| Primary Agent | Reviewer Agent | Why |
|:--------------|:---------------|:----|
| Claude Code | Codex | Different model, different blind spots |
| Codex | Claude Code | Same reasoning |
| Claude Code (Sonnet) | Claude Code (Opus) | Stronger model for architecture review |

---

## Important

- The human is always the final reviewer. QA gating is advisory, not a gate.
- The reviewer agent should NOT push, commit, or create PRs. Read-only review.
- If the reviewer finds issues, the primary agent (or human) fixes them.
- This is not a substitute for CI/CD, tests, or human code review.
