# Workflow: QA Correctness — 3-Model Cross-Agent Review

## Default Behavior

**After completing your task, dispatch all three reviewers in parallel before reporting done.**

This is the default, not opt-in. Every agent that finishes work should spawn
reviewers. Multiple independent models catch different mistakes so the human
doesn't have to manually review everything.

This is step 1 of the QA chain. On repos with substantial source code, follow it
with `~/agents-config/workflows/qa-structural.md` unless that workflow's skip
conditions apply.

### Review models

Three models review every non-trivial change **in parallel**:

| Reviewer | Dispatch command | Role |
|----------|-----------------|------|
| **Claude Code (CC)** | self-review (same process) | Context-rich reviewer — wrote the code, knows intent |
| **Codex** | `codex exec --full-auto "$QA_PROMPT"` | Independent cross-agent reviewer |
| **Gemini CLI** | `gemini -p "$QA_PROMPT"` | Independent cross-model reviewer (different model family) |

If an agent is unavailable (not installed, auth error, sandbox failure), fall
back to the next available agent. The minimum viable review is **1 model** — but
always attempt all 3. Use the highest-capability model or reasoning mode
available for each (e.g., extended thinking for CC self-review).

For unattended review runs in a trusted isolated environment:
- Codex reviewer: `codex exec --full-auto`
- Claude Code reviewer: `clauded -p` (alias for `claude --dangerously-skip-permissions`)
- Gemini reviewer: `gemini -p` (uses cached credentials)

If skip-permissions mode is not appropriate for your environment, do not treat
Claude Code as an unattended reviewer; run the same prompt in interactive
`claude` instead.

Skip review ONLY for trivial changes (typo fixes, comment edits, single-line config changes).

---

## How to Dispatch Reviewers

### Step A: Define the review prompt

```bash
QA_PROMPT="Review all changes in this directory since the last commit on main. \
Flag critical and major issues: logic errors, missing edge cases, incorrect behavior, \
inconsistencies with project agent docs (for example ~/your-project/docs/agent-docs/, if present). \
Do NOT apply fixes — report only. \
End with exactly: \
VERDICT: PASS | FAIL \
CRITICAL_ISSUES: [count] \
MAJOR_ISSUES: [count] \
SUMMARY: [1-2 sentences] \
If everything looks correct, use PASS with all counts set to 0."
```

> **Note on verdict format change:** Individual reviewers now report **PASS or
> FAIL only** (no FIXED). Fixes are applied in the aggregation step by the
> initial agent if needed — this prevents conflicting edits from parallel
> reviewers.

### Step B: Dispatch all 3 reviewers in parallel

Run all three simultaneously. Each reviewer produces an independent verdict.

#### 1. CC self-review

The initial agent (the one that performed the task) runs the QA prompt against
its own changes using extended thinking / highest-capability reasoning mode.

```bash
# If you ARE Claude Code — self-review inline (no subprocess needed).
# If you ARE Codex — dispatch CC:
clauded -p "$QA_PROMPT" || claude -p "$QA_PROMPT"
```

#### 2. Codex review

```bash
codex exec --full-auto "$QA_PROMPT"
```

#### 3. Gemini review

```bash
gemini -p "$QA_PROMPT"
```

**Fallback behavior:** If any reviewer fails (not installed, auth error, sandbox
issue), log the failure and continue with the remaining reviewers. The `||`
pattern works for chaining fallbacks:

```bash
# Example: try Codex, fall back to CC self-review
codex exec --full-auto "$QA_PROMPT" || claude -p "$QA_PROMPT"
# Example: try Gemini, fall back to CC self-review
gemini -p "$QA_PROMPT" || claude -p "$QA_PROMPT"
```

The minimum viable review is **1 model**. Always attempt all 3.

### Step C: Aggregate verdicts (initial agent decides)

The agent that performed the original task (the "initial agent") reads all
three verdicts and makes the **final decision**. This agent has the most context
— it wrote the code and knows the intent.

**Aggregation rules:**

| CC | Codex | Gemini | Final verdict |
|----|-------|--------|---------------|
| PASS | PASS | PASS | **PASS** — unanimous, proceed |
| PASS | PASS | FAIL | **Initial agent reviews Gemini's concerns** → PASS or FAIL |
| PASS | FAIL | PASS | **Initial agent reviews Codex's concerns** → PASS or FAIL |
| FAIL | PASS | PASS | **Initial agent re-examines own finding** → PASS or FAIL |
| FAIL | FAIL | * | **FAIL** — 2+ failures, escalate |
| FAIL | * | FAIL | **FAIL** — 2+ failures, escalate |
| * | FAIL | FAIL | **FAIL** — 2+ failures, escalate |

**When reviewing a single dissenting reviewer:**
- Read the specific issues they flagged
- If the concern is valid → apply a minimal fix, change final verdict to FIXED
- If the concern is a false positive → explain why in the aggregation summary, keep PASS
- If unsure → treat as FAIL, escalate to human

**Aggregation prompt (for the initial agent):**

```
You performed a task. Three reviewers (including yourself) reviewed the changes.
Here are their verdicts:

CC self-review: {verdict, critical_issues, major_issues, summary}
Codex review:   {verdict, critical_issues, major_issues, summary}
Gemini review:  {verdict, critical_issues, major_issues, summary}

Synthesize these into a final verdict. Rules:
- If 2+ reviewers say FAIL → final is FAIL.
- If exactly 1 reviewer says FAIL → examine their specific concerns.
  If the concern is valid, apply a MINIMAL fix and use FIXED.
  If it is a false positive, explain why and use PASS.
  If unsure, use FAIL and escalate.
- If any reviewer flagged CRITICAL_ISSUES > 0, treat it as real until
  you can specifically disprove it.

End with:
FINAL_VERDICT: PASS | FAIL | FIXED
CRITICAL_ISSUES: [total confirmed count]
MAJOR_ISSUES: [total confirmed count]
FIXES_APPLIED: [count]
REVIEWERS_AVAILABLE: [count out of 3]
DISSENT: [which reviewer(s) disagreed, if any, and resolution]
SUMMARY: [1-2 sentences]
```

### Fallback: fewer than 3 reviewers available

If only 2 reviewers are available:
- Both PASS → PASS
- Both FAIL → FAIL
- Disagreement → initial agent decides (same logic as above)

If only 1 reviewer is available:
- Use that single verdict directly (original pre-Gemini behavior)

---

## Reviewer Rules

The reviewer MUST follow these principles:

1. **Fix, don't rewrite.** If the code works but could be "better", leave it alone. Only fix things that are wrong.
2. **Minimal changes only.** A 2-line fix is better than a 50-line refactor that happens to also fix the bug.
3. **Don't overcomplicate what was already committed.** Even if the original approach was suboptimal, if it's correct and simple, keep it.
4. **Correctness over elegance.** Always.
5. **If unsure, leave it and flag it** rather than making a speculative change.

---

## Verdict Formats

### Individual reviewer verdict (each of the 3 reviewers)

```
VERDICT: PASS | FAIL
CRITICAL_ISSUES: [count]
MAJOR_ISSUES: [count]
SUMMARY: [1-2 sentences]
```

Individual reviewers report only — they do **not** apply fixes. This prevents
conflicting edits from parallel reviewers.

- **PASS** — no issues found.
- **FAIL** — found issues. Listed in summary.

### Aggregated final verdict (from the initial agent)

```
FINAL_VERDICT: PASS | FAIL | FIXED
CRITICAL_ISSUES: [total confirmed count]
MAJOR_ISSUES: [total confirmed count]
FIXES_APPLIED: [count]
REVIEWERS_AVAILABLE: [count out of 3]
DISSENT: [which reviewer(s) disagreed, if any, and resolution]
SUMMARY: [1-2 sentences]
```

Do not omit this block, even on PASS. The caller should relay it in the final
QA summary.

- **PASS** — all reviewers agree (or dissent was a false positive). Nothing changed.
- **FIXED** — a dissenting reviewer found a valid issue; the initial agent applied a minimal fix.
- **FAIL** — 2+ reviewers failed, or a critical issue couldn't be resolved. Escalate to human.

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
