# Subscription plans for heavy jobs

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/subscription-plan-routing.md>

**TLDR:** For token-heavy generic work, use an eligible existing subscription through the [plan router](../tools/plan-router/README.md), using the eligible default recorded in private account state. Select a tested model and effort to fit the task; scientific model pins remain binding. Personal account state belongs in [agent-sync](https://github.com/brando90/agent-sync/blob/main/assistants/subscription-plans.md).

## Trigger and selection

Use this workflow for bulk reading, drafting, code analysis, document comparison, experiment analysis, and other bounded jobs that can consume substantial model context. Give the job its inputs, acceptance checks, permitted outputs and a workspace. Quick answers and account actions do not require a separate model job. Keep one writer per workspace and inspect the returned artifact before using it.

Google consumer-plan assistant dispatch is currently held: [Google's FAQ](https://antigravity.google/docs/faq) excludes wrapping native `agy` in a third-party assistant and warns of account suspension. Direct user scripting and assistant orchestration are different scopes. A successful test does not resolve that restriction. Keep the consumer Google route off pending the account owner's explicit risk decision; no API billing is enabled as a replacement.

Use the installed router on the host holding the native sign-ins. Account state and supported models are local configuration, never an assumption from this public example. Select from the enabled, verified catalog:

| Predicted difficulty | Generic default | Alternatives after verification |
|---|---|---|
| Easy or bulk | Gemini 3.8 Flash, low | Sonnet 5.5, low or medium |
| Medium | Gemini 4 Argon, medium | Carbon, medium |
| Hard or high stakes | Argon, high | Carbon or Opus 5.5, high |
| Multiple dependent steps | Orchestrator (Argon), native default effort | Orchestrator (Carbon) |

The predictor is a transparent local keyword heuristic. Override its estimate when the job warrants it. A catalog entry is enabled only after a bounded native task succeeds. These checks establish access and prompt transport at that time; they are not comparative quality benchmarks. Hydrogen and GPT-OSS are selectable when verified, rather than automatic defaults. Orchestrator exposes no independent effort switch; use its exact native ID.

Explicit research models, frozen experiment configurations and frontier-only requirements override these generic defaults. `trustworthy-theorem-judges` requires frontier models. Use `--frontier-only` for generic work with that constraint; a pinned research job uses its specified `--plan` and model and does not silently switch. No deprecated Gemini CLI: Google runs through native `agy`.

## Commands

After an installation has configured its native clients and private account observations:

```bash
ROUTER="$HOME/.local/lib/plan-router/router.py"
CONFIG="$HOME/.config/plan-router/config.json"
python3 "$ROUTER" --config "$CONFIG" models --plan personal-agy
python3 "$ROUTER" --config "$CONFIG" status --refresh
python3 "$ROUTER" --config "$CONFIG" run --generic \
  --prompt-file ./job.md --workspace ./workspace
# Override the heuristic for a consequential task.
python3 "$ROUTER" --config "$CONFIG" run --generic --difficulty hard \
  --frontier-only --prompt-file ./job.md --workspace ./workspace
# Exact selection keeps this plan and model pinned.
python3 "$ROUTER" --config "$CONFIG" run --plan personal-agy \
  --model gemini-4-argon-high --prompt-file ./job.md --workspace ./workspace
```

`--model` accepts an exact verified ID or an unambiguous configured family; `--effort` must match an offered variant. Without `--generic`, the configured model remains pinned. Explicit `--plan` also preserves its model unless an explicit model or effort override is given. `--allow-fallback` requires `--generic` and permits only finite preflight fallback to configured eligible accounts. No automatic replay follows a started request, timeout, error or partial write.

## Meter and scope

`status` returns one row per plan/account, local per-model token/job counts and quota windows. Models sharing a native allowance pool show that shared pool, not invented per-model allowances. Native quota refresh converts remaining percentages to used percentages; admission stops at 80% weekly used or 100% short-window used. Stale observations stop admission. Refresh before dispatch because other applications share the plan.

For a native client with no percentage meter, remaining allowance is unknown. An explicitly approved Claude/Codex/Cursor/Grok native route can use bounded jobs with native authentication checked each time and vendor quota enforcement; known fresh quota limits still block. A verified successful bounded request can authorize one subsequent bounded request when that route is explicitly configured for it. Only another completed request renews that admission; failures and timeouts do not. Native subscription limits still apply. This is not an allowance estimate or a vendor billing switch.

Use existing authorized account profiles and wrappers. Keep sponsor scope, client identity and billing evidence current. The router scrubs inherited provider keys and requires an expiring subscription-only attestation. It does not purchase credits, change billing or use a paid API fallback. Cursor models that require paid Additional Usage remain off without that spending authorization. Separate provider keys, when explicitly authorized for another job, are outside this subscription workflow.

Receipts retain actual selected route/model/effort, selection reason, timestamps, status and available native token counters. Token counters are local usage records, not billing totals. Inspect native model metadata for scientific reporting. A returned answer or exit code alone does not establish correctness; run the job's acceptance checks.

**TLDR-end:** [Subscription routing] Use a tested native subscription for heavy generic work; choose by difficulty, preserve research pins, refresh the shared allowance meter and verify the result.
