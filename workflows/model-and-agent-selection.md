# Selecting models and agent harnesses for experiments

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/model-and-agent-selection.md>

**TLDR:** For new, unpinned model-calling workloads, select the evaluated system by relevant measured quality and total task cost. Use existing evidence first, validate judges for their actual role, and spend only on the smallest authorized comparison that informs the next decision. Preserve frozen experiments, required acceptance models and funding limits.

Brando requested this guidance on 10-22-2026 for artificial-intelligence judges, evaluations and other foundation-model (FM) calls. It concerns selecting and evaluating existing systems, not assuming that model training is feasible or needed. Read with [Hard Rule 8](../rules/safety-and-models.md#hard-rule-8), [Guideline 19](../rules/research.md#guideline-rule-19) and the project's scientific protocol.

## Select for the decision and capability

1. **Name the role and decision.** Separate the solver being measured, a single-call judge, an agent judge, a generator, the coordinating agent and a required reference reviewer. State the capability needed and the existing quality criterion or hypothesis. A cheap weak solver cannot establish that a benchmark resists the strongest relevant agents.
2. **Compare complete systems.** Record model/version, harness/version, reasoning effort, prompts, tools, context limits, stopping/retry policy, time/token limits, repetitions and fallback routing. Agent trajectory length can reverse a ranking based on token prices. A model served with fallback assistance is a different condition from that model alone.
3. **Use current, relevant primary evidence.** Prefer the project's existing matched-domain receipts, then official benchmark methods and results. Record source URLs, retrieval date, coverage and setting differences. Save user-provided screenshots and decision prompts in the experiment with provenance. Leaderboard names, branding, price and maximum effort are not substitutes for measured capability; missing coverage is unknown, not a zero or a loss.
4. **Choose quality at an affordable total cost.** Shortlist systems for which no comparable candidate is both better and cheaper, accounting for uncertainty. Among systems meeting the task's justified quality requirement, prefer lower expected total cost and suitable latency. If the purpose is to test the best available performance, select a credible strong panel for that capability instead of maximizing score per dollar alone. Explain any needed expensive comparator.

Public starting points include [Vibe Code](https://www.vals.ai/benchmarks/vibe-code), [Terminal-Bench](https://www.vals.ai/benchmarks/terminal-bench-4) and [SWE-bench Multimodal](https://www.vals.ai/benchmarks/swebench-multimodal). They cover different capabilities and harnesses; recheck their current versions and methods at selection time. This workflow deliberately does not enshrine today's winning model or prices as permanent defaults.

## Validate judges for judging

A coding or agent leaderboard can suggest candidates, but does not establish a judge's validity. Use relevant existing human-rated or independently checked cases with the actual rubric, prompt, input format and aggregation. Report absolute agreement/error and signed bias as well as association, failure/refusal and missing-output rates, and repeatability where repeats exist. Bias means mean judge score minus mean human/reference score; positive bias is leniency.

Inspect consequential errors such as false acceptance and false rejection where the available labels support them. Keep authorship and model-family overlap visible: company diversity and agreement between models do not prove correctness. Separate choosing a judge on validation data from assessing it on untouched test data; disclose reuse and selection effects. Preserve a sealed test set, and treat an already permitted reuse as reused evidence. Unavailable human agreement remains unavailable. Follow the [statistics workflow](statistics-reporting.md#judge-human-agreement-checklist); do not create extra model calls or human-label work merely to fill reporting fields.

## Reuse evidence, then run a bounded comparison if needed

Before new spending, state what decision existing results or zero-call analysis cannot resolve. If an authorized pilot is needed, predeclare a representative task set, exact systems, meaningful quality criteria, cost allowance, failure handling and continue/stop rule in the existing protocol. Use the same cases across candidates when a paired comparison answers the question. Preserve task/domain coverage and keep selection data separate from final evaluation claims.

Estimate the whole workload: tasks × systems × repeats, expected calls/trajectory lengths, token charges, tools/sandboxes, judging, retries, failed or ambiguous calls and outstanding reservations. Reconcile actual pilot charges before expansion. Existing project funding routes, shared ledgers, concurrent-run gates and narrower attempt limits govern; this guide neither grants spending permission nor adds an approval step when the work is already authorized.

A successful pilot or cheap proxy is a selection result, not a completed full evaluation. Once a manifest is frozen, complete its declared cells within its original limits and retain all failed or missing cells. Change model, effort, harness, judge, prompt, subset or fallback policy only as a prospective version/amendment; do not silently alter an active condition or retry until success. Required benchmark-reference acceptance and measured solver difficulty remain separate gates.

## Report coverage and uncertainty; validate subset estimates

Keep three quantities distinct: standard deviation across repeated scores (variability), standard error or a confidence interval for the expected score (estimation uncertainty), and prediction error when estimating unrun tasks. State sample/repetition counts and the independent unit. A displayed zero error bar is not proof of certainty. The [Vals methodology](https://www.vals.ai/methodology) is one example whose error bars require this distinction.

For a capability index, publish its task/benchmark weights, versions, component coverage and missingness policy. Show measured full-set, measured subset and estimated full-set scores separately; silently averaging only available benchmarks makes systems incomparable. Weighted uncertainty must account for relevant dependence between components.

Validated subsets or item response theory (IRT) can reduce evaluation cost when sufficient task-by-system response data exist. Compare simple representative subsets first; select/fix the method without using the final test systems. Test transfer across held-out model families, harnesses and later dates, reporting absolute prediction error and signed bias alongside ranking agreement. Validate an adaptive selection/stopping policy as a whole. No universal 0.1-percentage-point guarantee follows from IRT or a high correlation. Predicted failure on an unrun task is not measured benchmark resistance.

Primary references: [tinyBenchmarks](https://arxiv.org/abs/2402.14992), [Efficient Benchmarking of AI Agents](https://arxiv.org/abs/2603.23749), and [Vals Index methods](https://www.vals.ai/benchmarks/vals_index). These motivate options, not automatic permission to replace a project's required full-set or acceptance procedure.

## Minimal decision record

Add a short section to the existing experiment protocol/results, rather than creating another planning layer:

- Role, capability, question and decision; criterion and its source.
- Candidate model-and-harness settings, evidence URLs/date and transfer limitations.
- Chosen configuration, expected total cost, existing budget/route and why a cheaper alternative is insufficient or preferable.
- Pilot/subset scope and selection versus test split, or why existing evidence suffices.
- Actual model/fallback receipt, measured quality/cost/uncertainty, missingness and the next decision.

Global coordinator defaults, explicit user model choices, required reviewer families and frozen scientific pins retain precedence. For a fixed required model, optimize scheduling and eligible work rather than silently substituting another model. New unfrozen workloads need an evidence-based choice; neither always selecting the most expensive model nor always selecting the cheapest satisfies this workflow.
