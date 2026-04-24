# Workflow: QA — Cross-Agent Review

> **Design: A1 builds → A2 does full QA.** The builder dispatches one independent reviewer for full QA (correctness + structural). The reviewer finds AND fixes issues. Fallback: Codex → Gemini CLI → self-review with best model (or CC → Gemini CLI → self-review with best model, if Codex built).

## Hard Rule: CLI-only, no API keys

**QA ALWAYS runs through the locally-logged-in CLIs: `codex`, `claude` / `clauded`, `gemini`.** These CLIs authenticate via their own cached local credentials (subscription / OAuth / `~/.gemini/settings.json`). They are what Brando has logged into and pays for.

**Never fall back to API keys.** Do not set `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, or similar to make QA work. If a CLI returns an auth error ("set GEMINI_API_KEY", "no credentials"), treat it as a **local setup issue**: skip that stage, note the skip in the QA report, and suggest the user re-run the CLI's interactive login (`gemini`, `codex login`, `claude login`). Falling back to API-key paths silently bills pay-per-token instead of using the subscription the user already owns — that is a workflow failure.

Fallback order when a CLI stage fails:
1. Next CLI in the chain.
2. Self-dispatch with the current CLI (repeat the stage).
3. Never use API keys.

This applies to default QA, Mega QA, and any downstream workflow that dispatches a reviewer.

---

## Default Behavior

**After completing your task, dispatch one independent reviewer before reporting done.**

This is the default, not opt-in. Every agent that finishes work should dispatch
a reviewer. An independent model catches mistakes the builder is blind to — so
the human doesn't have to manually review everything.

The reviewer handles both correctness (logic errors, edge cases, broken behavior)
and structural quality (god functions, duplication, anti-patterns) in a single
pass. On repos with substantial source code, the reviewer also runs the
structural checks defined in
[`~/agents-config/workflows/qa-structural.md`](qa-structural.md). On
markdown-only or config-only repos, the reviewer skips structural checks.

Skip review ONLY for trivial changes (typo fixes, comment edits, single-line
config changes).

---

## How to Dispatch

### Step 1: Define the review prompt

```bash
QA_PROMPT="Review all changes in this directory since the last commit on main.

CORRECTNESS: Flag and fix critical and major issues — logic errors, missing
edge cases, incorrect behavior, inconsistencies with project agent docs
(for example ~/your-project/docs/agent-docs/, if present).

STRUCTURAL (skip for markdown-only repos): Check for god functions (CC > 10
or >60 lines), structural duplication, verbose anti-patterns (single-use vars,
identity wrappers, defensive checks for impossible states, 3+ nesting,
if/elif ladders, dead code). Fix what you find. Preserve public interfaces.
Run tests after each change — revert and skip if tests break.

You are empowered to fix issues directly. Apply minimal fixes only.

End with exactly:
VERDICT: PASS | FAIL | FIXED
CRITICAL_ISSUES: [count]
MAJOR_ISSUES: [count]
FIXES_APPLIED: [count]
STRUCTURAL: PASS | IMPROVED | SKIP
SUMMARY: [1-2 sentences]
If everything looks correct, use PASS with all counts 0."
```

### Step 2: Dispatch the reviewer

Try the primary cross-agent reviewer first. If unavailable (not installed, auth
error, sandbox failure), fall through to the next option.

```bash
# If you ARE Claude Code (CC) — dispatch Codex, fall back to Gemini, then self-review:
codex exec --full-auto "$QA_PROMPT" \
  || gemini -p "$QA_PROMPT" \
  || clauded -p "$QA_PROMPT"

# If you ARE Codex — dispatch CC, fall back to Gemini, then self-review:
clauded -p "$QA_PROMPT" \
  || gemini -p "$QA_PROMPT" \
  || codex exec --full-auto "$QA_PROMPT"
```

For unattended review runs in a trusted isolated environment:
- Codex reviewer: `codex exec --full-auto`
- Claude Code reviewer: `clauded -p` (alias for `claude --dangerously-skip-permissions`)
- Gemini reviewer: `gemini -p` (uses cached credentials)

If skip-permissions mode is not appropriate for your environment, do not treat
Claude Code as an unattended reviewer; run the same prompt in interactive
`claude` instead.

### Single-model fallback

If only one model is available (e.g., only Claude Code on Anthropic's default
environment, or only Codex in an OpenAI sandbox), the agent should still run QA
by dispatching **itself** with the QA prompt. Self-review with the best available
model/reasoning mode (e.g., extended thinking, Opus) is always better than no
review. In unattended environments, the fallback chain handles this
automatically — the last option in the `||` chain is always self-dispatch. If
Claude Code must run interactively, use the same QA prompt in `claude` for the
self-review round instead.

---

## Reviewer Rules

The reviewer MUST follow these principles:

1. **Fix, don't rewrite.** If the code works but could be "better", leave it alone. Only fix things that are wrong.
2. **Minimal changes only.** A 2-line fix is better than a 50-line refactor that happens to also fix the bug.
3. **Don't overcomplicate what was already committed.** Even if the original approach was suboptimal, if it's correct and simple, keep it.
4. **Correctness over elegance.** Always.
5. **If unsure, leave it and flag it** rather than making a speculative change.
6. **You are empowered to fix issues.** Apply minimal fixes directly — don't just report.

---

## Verdict Format

The reviewer produces one verdict covering both correctness and structural quality:

```
VERDICT: PASS | FAIL | FIXED
CRITICAL_ISSUES: [count]
MAJOR_ISSUES: [count]
FIXES_APPLIED: [count]
STRUCTURAL: PASS | IMPROVED | SKIP
SUMMARY: [1-2 sentences]
```

- **PASS** — no issues found. Code is correct and structurally healthy.
- **FIXED** — found issues, applied minimal fixes. All fixes described in summary.
- **FAIL** — found issues that couldn't be auto-fixed. Escalate to human.

Do not omit this block, even on PASS. The caller should relay it in the final
QA summary.

---

## Mega QA — Sequential Multi-Model Chain

> **Trigger:** User says "mega QA", "super QA", "extra careful QA", "deep QA",
> or similar. This is opt-in only — never runs automatically.

For high-stakes moments (end of work day, before major merges, before sleep),
run all available models **sequentially**. Each model does full QA (correctness
+ structural, with authority to fix), then the next model reviews the improved
code. No parallel writes, no aggregation — just a chain.

### Chain order

The builder reviews in the **middle** (it knows the code intent best and can
verify the first reviewer's changes). Gemini always does the **final** pass as
clean-eyes reviewer. Default is 3 stages (one per model). If the user requests
more rounds, cycle through the chain again (e.g., 6 rounds = chain × 2, 9
rounds = chain × 3).

| Builder | Chain (default 3 stages) |
|---|---|
| CC built | Codex → **CC** → Gemini |
| Codex built | CC → **Codex** → Gemini |

### How to run

```bash
# Example: CC built the code

# Stage 1: dispatch Codex as first independent reviewer
codex exec --full-auto "$QA_PROMPT"

# Stage 2: CC (the builder) reviews Codex's changes — knows the intent best
# Run the QA prompt inline (self-review with best model)

# Stage 3: Gemini does final clean-eyes pass
gemini -p "$QA_PROMPT"
```

Each reviewer uses the same `$QA_PROMPT` from Step 1 above. Each one sees the
code as improved by the previous reviewer.

### Configuring rounds

Default is **3 stages** (one per available model). The user can request more
rounds — the chain cycles (e.g., × 2 = 6 stages, × 3 = 9 stages). Gemini
always occupies the last stage of each cycle.

- If CC built: "mega QA" → Codex → CC → Gemini (3 stages, × 1)
- If CC built: "mega QA x2" → Codex → CC → Gemini → Codex → CC → Gemini (6 stages)
- If CC built: "mega QA x3" → (Codex → CC → Gemini) × 3 (9 stages)
- If CC built: "mega QA 2 rounds" → Codex → Gemini (2 stages, skip builder middle pass)
- If Codex built: swap CC and Codex positions in the examples above.

Each stage uses the same QA prompt and the same verdict format. The **last
reviewer's verdict** (Gemini in the default chain) is the final verdict.

### Single-model fallback

If only one model is available, run mega QA as **N rounds of self-review** with
the same model. Each round is a fresh dispatch (new context) so the model
re-examines the code with fresh eyes. For example, with only CC available:

- "mega QA" → CC self-review × 3 (each round sees previous round's fixes)
- "mega QA 5 rounds" → CC self-review × 5

This is less powerful than cross-model review but still catches issues that a
single pass misses — each fresh context re-examines with different attention.
If Claude Code must run interactively, do the same repeated rounds in fresh
`claude` sessions instead of unattended `clauded -p`.

### When to use

- End of work day / before sleep — let it run overnight
- Before merging to main or a shared branch
- After a long multi-commit feature branch
- Reviewing the overall state of a repo (not just the latest changes)

### Verdict

The last reviewer in the chain produces the final verdict using the standard
format. No aggregation needed — each reviewer builds on the previous one's
fixes.

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
