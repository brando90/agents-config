# Workflow: QA — Proportionate Review

**TLDR:** QA is mandatory for non-trivial work, but model-reviewer dispatch is not. Use deterministic checks for routine prose/docs, one independent reviewer for code/behavior or claim/result risk, and Mega QA only when explicitly requested.

> **Design: A1 builds → appropriate QA tier.** The builder picks the lightest tier that covers the risk. When a reviewer is dispatched, that reviewer finds AND fixes issues; when the task is routine writing/docs, deterministic checks plus self-review are the intended QA.

## Hard Rule: CLI-only, no API keys

**Any model QA dispatch ALWAYS runs through the locally-logged-in CLIs: `codex`, `claude` / `clauded`, `gemini`.** These CLIs authenticate via their own cached local credentials (subscription / OAuth / `~/.gemini/settings.json`). They are what Brando has logged into and pays for.

**Never fall back to API keys.** Do not set `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, or similar to make QA work. If a CLI returns an auth error ("set GEMINI_API_KEY", "no credentials"), treat it as a **local setup issue**: skip that stage, note the skip in the QA report, and suggest the user re-run the CLI's interactive login (`gemini`, `codex login`, `claude login`). Falling back to API-key paths silently bills pay-per-token instead of using the subscription the user already owns — that is a workflow failure.

Fallback order when a CLI stage fails:
1. Next CLI in the chain.
2. Self-dispatch with the current CLI (repeat the stage).
3. Never use API keys.

This applies to any workflow that dispatches a reviewer.

---

## QA Tiers

**Pick the QA tier before reporting done.** The goal is enough verification, not maximum agent traffic.

### Tier 0 — trivial

Use for typo fixes, comment-only edits, one-line formatting fixes, or no-op file moves. Review the diff and stop.

### Tier 1 — lightweight deterministic QA

Use for routine prose polish, paper wording edits, README/doc edits, markdown-only logs, and small config-doc updates that do not change behavior or shared policy.

Required checks:
- Self-review the diff against the user's request.
- Run `git diff --check`.
- Run the relevant deterministic check: LaTeX compile/render for `.tex`, link/path grep for docs, targeted grep for banned/risky phrases, or formatting/lint checks if available.

Do not dispatch a fallback model reviewer for Tier 1 just because another reviewer stalled. If a previous model QA stalls during routine writing polish, kill it, record that it was skipped, and finish with deterministic checks.

### Tier 2 — independent reviewer QA

Use when changes affect code behavior, scripts, infra/auth, packaging/deployment, data/results, experiments, generated artifacts, nontrivial shared workflows/rules, or paper claims/numbers/tables/citations/experimental conclusions. Also use Tier 2 when the agent is uncertain about scientific or behavioral correctness.

For Tier 2, dispatch one independent reviewer before reporting done. The reviewer handles correctness (logic errors, edge cases, broken behavior, inconsistencies with project docs) and structural quality in a single pass. On repos with substantial source code, the reviewer also runs the structural checks defined in [`~/agents-config/workflows/qa-structural.md`](qa-structural.md). On markdown-only or config-only repos, structural checks are skipped, but correctness and consistency review still apply.

### Tier 3 — Mega QA

Use only when the user says "mega QA", "super QA", "extra careful QA", "deep QA", "final QA", "pre-arXiv QA", "pre-submission QA", or similar. Run the sequential multi-model chain in the Mega QA section.

### Paper-writing rule of thumb

Routine wording/style edits are Tier 1. Escalate to Tier 2 only if the edit changes a factual claim, headline framing, theorem/proof status, dataset/result number, citation support, table/figure content, or final/pre-submission readiness. Uncertainty about taste stays Tier 1; uncertainty about truth goes Tier 2.

## How to Dispatch

Use this section only for Tier 2 or Tier 3. Tier 1 uses deterministic checks, not model dispatch.

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
codex exec --full-auto -m gpt-5.5 -c 'model_reasoning_effort="xhigh"' "$QA_PROMPT" \
  || gemini -p "$QA_PROMPT" \
  || clauded -p "$QA_PROMPT"

# If you ARE Codex — dispatch CC, fall back to Gemini, then self-review:
clauded -p "$QA_PROMPT" \
  || gemini -p "$QA_PROMPT" \
  || codex exec --full-auto -m gpt-5.5 -c 'model_reasoning_effort="xhigh"' "$QA_PROMPT"
```

For unattended review runs in a trusted isolated environment:
- Codex reviewer: `codex exec --full-auto -m gpt-5.5 -c 'model_reasoning_effort="xhigh"'`
- Claude Code reviewer: `clauded -p` (alias for `claude --dangerously-skip-permissions`)
- Gemini reviewer: `gemini -p` (uses cached credentials)

If skip-permissions mode is not appropriate for your environment, do not treat
Claude Code as an unattended reviewer; run the same prompt in interactive
`claude` instead.

### Single-model fallback

For Tier 2, if only one model is available (e.g., only Claude Code on Anthropic's default environment, or only Codex in an OpenAI sandbox), the agent should still run QA by dispatching **itself** with the QA prompt. In unattended environments, the fallback chain handles this automatically — the last option in the `||` chain is always self-dispatch. If Claude Code must run interactively, use the same QA prompt in `claude` for the self-review round instead.

Do not use single-model fallback to turn Tier 1 writing polish into model QA. Tier 1 already includes self-review plus deterministic checks.

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
codex exec --full-auto -m gpt-5.5 -c 'model_reasoning_effort="xhigh"' "$QA_PROMPT"

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

### Per-stage fallback (coin-flip)

A stage can fail for many reasons: auth/credits exhausted, context-window
overflow, backend 5xx, sandbox-blocked tools, etc. **Never bail.** When a
stage fails, replace that stage with a working CLI:

1. **Coin-flip** among the other CLIs that haven't failed yet (`codex`,
   `clauded`, `gemini`).
2. **Self-dispatch** the agent currently driving the chain if no other CLI
   works (it's already authed and running, so it's guaranteed available).
3. Always complete the planned number of stages — count substitutions toward
   the count, do not skip.

The driving agent is always available, so the worst case is **N×
self-review of the same model** (e.g., CC → CC → CC). That is still useful:
each stage is a fresh context that re-examines previous fixes with
different attention. Cross-model is preferred but not required.

Example (CC built; Gemini out of credits at stage 3):

- Stage 1: Codex (worked) → Stage 2: CC self (worked) → Stage 3: coin-flip
  picks Codex (worked) ⇒ chain done in 3 stages: Codex → CC → Codex.
- If Codex also failed at stage 3: fall through to self → CC → CC → CC.

Single-model from the start (only CC available): chain is CC self-review × N
out of the box; same logic, fewer choices.

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
