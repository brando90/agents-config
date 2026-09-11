# Workflow: QA — Proportionate Review

**TLDR:** Quality assurance (QA) uses deterministic checks for routine prose and one review round for substantive changes. Prefer a capable reviewer from the other company, allow a disclosed smaller-model fallback for ordinary changes, preserve strongest-model acceptance for critical changes, and run Mega QA only when Brando requests it.

> **Design: A1 builds → appropriate QA tier.** The builder picks the lightest tier that covers the risk. When a reviewer is dispatched, that reviewer finds AND fixes issues; when the task is routine writing/docs, deterministic checks plus self-review are the intended QA.

## Hard Rule: CLI-only, no API keys

**Any model QA dispatch ALWAYS runs through the locally-logged-in CLIs: `codex` and `claude` / `clauded`.** These CLIs authenticate via their own cached local credentials (subscription / OAuth). They are what Brando has approved for agent QA.

**Never fall back to application programming interface (API) keys or extra paid credits.** Do not set `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, or similar to make review work. Use the bounded procedure below for every reviewer dispatch. Cached subscription authentication is required; an already-running conversation does not prove a fresh invocation can run. Suggest interactive login separately only when authentication is actually the problem.

## Review fallback and acceptance

This is the canonical reviewer-selection procedure for Hard Rule 8, Tier 2 and each requested Mega QA stage. **Select the acceptance requirements before calling models.** A smaller reviewer is an explicit exception to strongest-model defaults, not a change to builder settings.

| Change being reviewed | Eligible acceptance review |
|---|---|
| Ordinary behavior changes, routine scripts, or shared workflow guidance without the critical effects below | Prefer the strongest opposite-company model; one suitable smaller reasoning model from that company may substitute when it cannot run. |
| Security/authentication, permissions or spending controls, evaluation/scoring integrity, substantive scientific claims/results, uncertain correctness, or shared rules controlling review, permissions, spending or publication | A strongest-model reviewer is required. A smaller critic may inform the work but cannot approve it or fill a required stage. |
| Benchmark reference data (gold answers, labels, theorem statements, oracle outputs) | Trigger Rule 43: **both Claude and Codex at their strongest tier** must check each accepted change. A same-company fallback cannot waive this requirement. |

Every explicitly requested Mega QA acceptance stage retains its strongest-model floor; use the critical fallback path even for an otherwise ordinary change.

Classify by consequences, not file extension: editing a security rule in Markdown is critical. If the boundary is uncertain, use the critical requirements. Mixed ordinary and critical changes inherit the critical requirements unless their review and acceptance can actually be separated. An explicit user-required reviewer/model/effort or other stricter project gate remains required; do not silently replace it. Reassess the classification when findings or fixes change the risk. A smaller review becomes advisory for newly critical scope; obtain the required acceptance review within the remaining original attempt budget, or leave acceptance pending.

**Bounded decision order:**

1. Start with the designated strongest model from the other company (Codex `gpt-6-astra` / `ultra`; Claude `claude-fable-5-1` / `max`). For a requested builder/self-review stage, start with the builder's strongest model instead. Read the actual response and review coverage; a successful process exit alone is not a review.
2. On failure, record the attempted model, error and established scope. An ambiguous credit/usage error means **that attempt failed**, not that all models at the company are exhausted. Explicit shared-account exhaustion, missing authentication, or a provider outage makes a smaller-model attempt inappropriate. For a recoverable request/tool/context error, repair it without dropping review coverage or weakening security, then retry once. Do not change model merely to address a broken command or missing file. If a failed reviewer left partial edits or findings, inspect and preserve them before continuing; failure is not a clean starting point.
3. The failing company gets **at most one additional invocation per stage**, used either for that repair/retry or for the strongest suitable remaining reasoning model on the same subscription. For ordinary changes, prefer this smaller opposite-company reviewer over returning to the builder's company. Choose from models evidenced as supported by the installed client/account; use supported reasoning effort, sufficient context and the tools needed for the whole review. A floating alias such as `opus` is not capability evidence: resolve and record its actual model identifier. Do not guess a succession of model names or treat more effort as making a smaller model equivalent. Where quota scope is ambiguous, this one actual review attempt can establish availability; do not spend a separate trivial probe plus a full review.
4. If the ordinary review still lacks an eligible result, dispatch the strongest model from the other working approved subscription in a **fresh context**; it may be the builder's company. For critical changes, go directly to this strongest-model substitute after an unrecoverable failure, unless the required company/model itself is mandatory. Do not automatically add an advisory smaller-model call: use one only when its limited critique is useful within the same attempt budget, and mark it advisory. Never count it as critical acceptance. Maximum **three invocations per required stage** (primary, optional one retry/alternative, one strongest-model substitute), not an unbounded model ladder.
5. Stop when an eligible review succeeds. On exhausted attempts, or an unmet mandatory company/model gate, report the completed checks and outstanding acceptance requirement. Useful editing and deterministic verification may continue, but **do not merge, publish, or claim the protected change accepted** until the required review exists. Renew attempts only after relevant new evidence (for example a quota reset or repaired login) or an explicit user request.

A review that identifies defects is a valid review, not an availability failure: resolve its findings rather than searching for a model that will say PASS. Failed invocations and substitutes are attempts within the same requested review stage; only a completed eligible review fulfills it, and these attempts do not authorize extra rounds. A fresh same-company review adds a second examination but does not establish cross-company independence. Different companies can still share mistakes; none of these choices guarantees no regression.

**Record the review evidence.** Alongside the existing verdict block, report the builder and actual reviewer model identifiers, reasoning efforts, role (`acceptance` or `advisory`), ordinary/critical/reference classification, reviewed commit or diff, fallback reason and known failure scope, tests/coverage limits, and any unmet gate. Report unverified model metadata as unverified; do not infer it from an alias or claim a downgraded run used the strongest model. Any required model or effort remains an unmet acceptance gate if its actual value cannot be established or does not satisfy the requirement. Compare requested and actual model/effort; evidence of an unexpected model or effort substitution requires rechecking eligibility, not silently accepting the requested settings.

**Independent critique, then reconciliation.** Give the reviewer the requirements, relevant source, exact diff/base, and test evidence before supplying the builder's defense or another reviewer's conclusions. Ask for concrete counterexamples and evidence. The builder records each material finding as fixed, rejected with evidence, or unresolved, then verifies accepted fixes against requirements and deterministic checks. Preserve the original diff/commit so speculative reviewer edits can be compared or reverted. If needed, use a brief evidence-based clarification within the existing round; do not launch a new full review or an open-ended debate. Agreement alone is not evidence, and a final PASS cannot erase an unresolved earlier finding.

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

**Round budget (Brando 2026-08-20 — "otherwise I run out of tokens").** The default shape is ONE
review round and done: builder X → opposite-CLI reviewer Y → X applies the fixes → X verifies the
fixes with deterministic checks (tests, compile, targeted grep) → done. A FAIL/FIXED verdict with
actionable findings does NOT trigger an automatic re-review; fixing the findings and passing the
deterministic checks closes the round. Escalate to a SECOND round (X → Y → X → Y → X → done) only
when the change is genuinely among the hardest — eval/scoring integrity, security/auth surfaces,
or first-round findings whose fixes are themselves risky. Never run more than two rounds unless
Brando explicitly asks (that territory is Mega QA, which only he invokes).

### Tier 3 — Mega QA (manual-only, by Brando)

Use only when **Brando himself** says "mega QA", "super QA", "extra careful QA", "deep QA", "final QA", "pre-arXiv QA", "pre-submission QA", or similar. **Mega QA never auto-triggers and is never agent-selected** — not on `git push`/merge to `main`, not from file-path heuristics, not from a project QA-gate hook, and not because an agent judges the moment high-stakes (end-of-day, pre-merge, pre-sleep included). A hook that gates pushes to `main` must default to the lightest proportionate tier (Tier 0/1 for docs/prose, Tier 2 single-round for code/behavior/claims) and must **never** escalate to the mega chain on its own; mega is opt-in only via Brando's explicit request (or an opt-in he himself set, such as a `[mega-qa]` commit-message tag or an env flag). Run the sequential multi-model chain in the Mega QA section.

### Paper-writing rule of thumb

Routine wording/style edits are Tier 1. Escalate to Tier 2 only if the edit changes a factual claim, headline framing, theorem/proof status, dataset/result number, citation support, table/figure content, or final/pre-submission readiness. Uncertainty about taste stays Tier 1; uncertainty about truth goes Tier 2.

## How to Dispatch

Use this section only for Tier 2 or Tier 3. Tier 1 uses deterministic checks, not model dispatch.

### Step 1: Define the review prompt

Set `QA_BASE` to the task's original base commit and `QA_PATHS` to its explicitly owned paths before constructing the prompt. Keep that base fixed across attempts and stages, including reviews after publication; current `HEAD` or `main` may already contain the implementation.

```bash
QA_PROMPT="Review the complete change from original base $QA_BASE to the current
working tree within these owned paths: $QA_PATHS. Include committed and
uncommitted changes, plus new files in scope; do not review only the latest
commit or the diff against HEAD.

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
If everything looks correct, use PASS with all counts 0.

TL;DR: Review correctness and structure, apply minimal necessary fixes,
verify them deterministically, and return the verdict block above."
```

### Step 2: Dispatch the reviewer

Choose the next eligible invocation with [Review fallback and acceptance](#review-fallback-and-acceptance); these are primary commands, **not an automatic shell fallback chain**. Inspect model errors and review findings separately.

```bash
# If Claude Code built the change, start with Codex:
codex exec --approve-for-me -m gpt-6-astra -c 'model_reasoning_effort="ultra"' "$QA_PROMPT"

# If Codex built the change, start with Claude Code:
clauded --model claude-fable-5-1 --effort max -p "$QA_PROMPT"
```

Pass any selected smaller model and its supported effort explicitly using the same client flags; record the actual model and why it is eligible. Do not change global configuration for a one-stage fallback.

For unattended review runs in a trusted isolated environment:
- Codex reviewer: `codex exec --approve-for-me -m gpt-6-astra -c 'model_reasoning_effort="ultra"'`
- Claude Code reviewer: `clauded --model claude-fable-5-1 --effort max -p` (alias for `claude --dangerously-skip-permissions`)

If skip-permissions mode is not appropriate for your environment, do not treat
Claude Code as an unattended reviewer; run the same prompt in interactive
`claude` instead.

### Only one company is available

A fresh strongest-model review from that company is allowed when the acceptance requirements permit it. Report the missing company diversity. This does not satisfy Trigger Rule 43 or an explicit required cross-company/model gate. Follow the same attempt budget; do not restart the budget by relabeling a failed run as self-review.

Do not turn Tier 1 writing polish into model QA; it already includes self-review and deterministic checks.

---

## Reviewer Rules

The reviewer MUST follow these principles:

1. **Fix, don't rewrite.** If the code works but could be "better", leave it alone. Only fix things that are wrong.
2. **Minimal changes only.** A 2-line fix is better than a 50-line refactor that happens to also fix the bug.
3. **Don't overcomplicate what was already committed.** Even if the original approach was suboptimal, if it's correct and simple, keep it.
4. **Correctness over elegance.** Always.
5. **If unsure, leave it and flag it** rather than making a speculative change.
6. **You are empowered to fix issues within your assigned ownership.** Record each finding and its evidence before making a minimal fix; when assigned a read-only review, report it for the builder to fix. The builder checks the resulting diff and verifies the fix.

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
- **FAIL** — found unresolved issues. The builder may fix and verify them within the existing round; escalate when they cannot be resolved or an acceptance gate remains unmet.

Do not omit this block, even on PASS. The caller should relay it in the final
QA summary.

---

## Mega QA — Sequential Multi-Model Chain

> **Trigger:** Brando himself says "mega QA", "super QA", "extra careful QA",
> "deep QA", or similar. This is **manual-only** — it never runs automatically
> and an agent never selects it: not on `git push`/merge to `main`, not from
> file-path heuristics, not from a project QA-gate hook, and not from an
> agent's own judgment that the moment is high-stakes. A push-gate hook may
> require Tier 1/2 QA, but only Brando's explicit request invokes the mega
> chain (token budget: multi-round chains are expensive).

When Brando invokes it, run all available models **sequentially**. Each model
does full QA (correctness + structural, with authority to fix), then the next
model reviews the improved code. No parallel writes, no aggregation — just a
chain.

### Chain order

The builder reviews in the **middle** (it knows the code intent best and can
verify the first reviewer's changes). Default is 3 stages, **Claude + Codex
only** (Brando 2026-08-19: Google reviewers — Gemini bot / Antigravity —
removed from the QA protocol): one independent reviewer, then the builder/self
review, then the non-builder CLI again **in a fresh context** as the final
clean-eyes pass. If a CLI is unavailable, the per-stage fallback applies
(use the canonical selection procedure and preserve required acceptance gates). If
the user requests more rounds, cycle the chain in fresh contexts.

| Builder | Chain (default 3 stages) |
|---|---|
| CC built | Codex → **CC** → Codex (fresh context) |
| Codex built | CC → **Codex** → CC (fresh context) |

### How to run

```bash
# Example: CC built the code

# Stage 1: dispatch Codex as first independent reviewer
codex exec --approve-for-me -m gpt-6-astra -c 'model_reasoning_effort="ultra"' "$QA_PROMPT"

# Stage 2: CC (the builder) reviews Codex's changes — knows the intent best
# Run the QA prompt inline (self-review with best model)
```

Each reviewer uses the same `$QA_PROMPT` from Step 1 above. Each one sees the
code as improved by the previous reviewer.

### Configuring rounds

Default is **3 stages** with Codex and Claude Code (see Chain order above).
The user can request more rounds ("mega QA xN"); cycle the chain, using a
fresh context each time.

- If CC built: "mega QA" → Codex → CC → Codex (3 stages)
- If CC built: "mega QA x2" → the chain twice (6 stages)
- If Codex built: swap CC and Codex positions in the examples above.

Each stage uses the same QA prompt and verdict format. The final report includes
the last reviewer's verdict, resolution of earlier material findings, and the
state of all required acceptance gates.

### Per-stage fallback

Apply [Review fallback and acceptance](#review-fallback-and-acceptance) separately to each requested stage. A successful eligible substitute completes that stage; a failed invocation or advisory critique does not. Complete the requested number of stages only while eligible subscription reviewers can run, and report missing diversity or incomplete stages explicitly. Repeated strongest-model self-review is permitted only where the task's acceptance rules permit it; it cannot satisfy a mandatory other-company check. Do not add stages merely because a fallback occurred.

### When Brando typically invokes it

These are moments **Brando** may choose to type "mega QA" — they are context for
him, never justification for an agent to start the chain itself:

- End of work day / before sleep — let it run overnight
- Before merging to main or a shared branch
- After a long multi-commit feature branch
- Reviewing the overall state of a repo (not just the latest changes)

### Verdict

The last reviewer returns the standard verdict. The builder reports acceptance
only after all material findings are resolved, required checks pass, and the
company/model requirements are met. A later PASS cannot overwrite an earlier
unresolved issue or a missing mandatory review.

---

## When to Skip Review

- Typo fixes, comment-only edits, and strictly nonbehavioral configuration edits may use Tier 0/1. A single line is not an exemption: behavior changes, critical controls, benchmark reference data, and explicitly required reviews retain their consequence-based review requirements. Deterministic checks still apply.
- User explicitly says "skip review" or "no QA."
- The task was itself a review task (don't recurse — reviewers don't dispatch reviewers).

---

## When Human Review is Still Needed

- Reviewer returns FAIL with **critical** findings the builder cannot fix (a FAIL whose findings
  the builder CAN fix is closed by fixing them + deterministic verification — see Round budget;
  it does not by itself demand a human or another review round).
- Changes touch security-critical code (auth, secrets, permissions).
- Changes modify evaluation metrics or scoring logic.
- Merging to main or a shared branch requires existing user authorization;
  Trigger Rule 46 supplies standing authorization for remote-worker landings
  once its review and merge requirements pass. Follow an explicit instruction
  to leave work unmerged or unpushed.
