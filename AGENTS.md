# Codex Agent Entry Point

**TLDR:** Codex must refresh and read `~/agents-config/INDEX_RULES.md`; the response-critical rules are duplicated here so TLDRs, snapshots, QA, and secret safety cannot be missed.

# Codex / other agents: run `git clone https://github.com/brando90/agents-config.git ~/agents-config 2>/dev/null || git -C ~/agents-config pull --ff-only 2>/dev/null` to bootstrap/update config.
# Read `~/agents-config/INDEX_RULES.md` for all agent documentation and routing. Local `~/agents-config/` is the fallback if GitHub is unreachable.

## Mandatory Response Protocol (inline — do not skip)

These rules are duplicated from `~/agents-config/INDEX_RULES.md` so they are visible at session start. They are mirrored in `CLAUDE.md` for Claude Code.

1. **Dual TLDR (top + end)** — Open every response with `**TLDR-start:**` and close with `**TLDR-end:**` (1–2 sentences each). Prefix both with `[proj: task]`; use `[proj]` only when there is no clear task. Write the bottom TLDR last from the actual response; do not copy the opening TLDR.
2. **Verification snapshot** — Immediately after `TLDR-end`, append a `**Snapshot:**` block containing the smallest concrete sample of the artifacts produced (normally 5–15 lines; hard cap 25). If there is nothing tangible, say why.
3. **Proportionate QA** — Before calling non-trivial work done, run the lightest QA tier that covers the risk. Shared rules, code/behavior, and claims/results require an independent reviewer by default.
4. **No secrets** — Never commit secrets. Review the exact staged diff before pushing.
5. **Fresh config** — At the start of each new task, run `git -C ~/agents-config pull --ff-only` and re-read `~/agents-config/INDEX_RULES.md`.
6. **Expand acronyms + jargon on first use** — every response, including ordinary chat, not just reader-facing prose. Write out any abbreviation or project-specific term the first time it appears: `TBH (to be honest)`, `SCSC (Smooth Conjunctive Score for Code verification)`, `the fresh re-run` (rename an opaque in-house label like "Arm 2" rather than just defining it). Short form is fine afterwards within that response. Full text: `~/agents-config/INDEX_RULES.md` Hard Rule 10.

## Research and experiments

For uncertain research/design work, apply [Trigger Rule 50](INDEX_RULES.md): identify the consequential uncertainty and test it cheaply enough to learn. For authorized experiments, follow [Trigger Rule 39](INDEX_RULES.md) and [the experiment workflow](workflows/expts-and-results.md#starting-or-continuing-an-experiment) automatically, including canonical homes, index entries and live records.

## Questions about other agents

For another agent's purpose or progress, read the relevant task context and distinguish current response activity, scheduled follow-ups, and underlying worker/results state. Never use `idle` or a completed turn alone as the overall task status. Keep checks proportionate and read-only unless changes are authorized; state what remains unverified. Full rule: `~/agents-config/INDEX_RULES.md` Trigger Rule 47.

When creating or editing saved automation, scheduled-task, or heartbeat prompts, include a descriptive title, one opening purpose summary, and one closing TLDR covering action, update destination, and the existing stopping condition (or its absence). Preserve operational instructions, target, cadence, model, notification settings, and enabled/paused state in readability-only edits. See `~/agents-config/INDEX_RULES.md` Trigger Rule 36 for summary labels and longer-header exceptions.

## Codex CLI default

Codex CLI should always default to `gpt-6-astra` (GPT-6 Astra) with `model_reasoning_effort = "ultra"` (Codex-only level above `xhigh`/`max`; updated 2026-09-08).
Keep `~/.codex/config.toml` set with those values. When dispatching Codex from
another CLI, pass the master-selected model/effort explicitly; this example is for a strongest-tier review, not the default for every worker:

```bash
codex exec --approve-for-me -m gpt-6-astra -c 'model_reasoning_effort="ultra"' "$QA_PROMPT"
```

Claude Code defaults to `claude-fable-5-1` / `max`. Keep strongest master defaults; choose proportionate execution workers explicitly under Trigger Rule 48. Review selection follows [Hard Rule 8](INDEX_RULES.md) and the canonical [fallback and acceptance procedure](workflows/qa-correctness.md#review-fallback-and-acceptance): prefer the other company's strongest model; ordinary changes may use one disclosed suitable smaller-model fallback before a fresh strongest-model same-company review. Critical changes and requested Mega QA stages retain strongest-model acceptance; benchmark reference data still requires both families at their strongest tier (Trigger Rule 43). Diagnose failure scope, preserve explicit model requirements, and never use provider keys. Record the actual model, effort and unmet gates.

Experiment workloads use regular thinking models such as `claude-sonnet-5` or `gpt-5.6-terra`, escalating when needed or Brando requests it; record exact model identifiers. Human handoff recommendations remain proportionate (Trigger Rule 36). Global model settings are not changed by a temporary review fallback.

## CLI-only for all LLM work (mandatory — INDEX_RULES.md Hard Rule 9)

Never make direct LLM-provider API calls (`anthropic`, `openai`, `litellm`,
`google.genai`, raw HTTP to `api.anthropic.com` / `api.openai.com` /
`generativelanguage.googleapis.com`). Always route LLM-driven work through the
approved locally-authenticated CLIs: `clauded -p`, `codex exec`, and `antigravity`
for general model work. Quality assurance (QA) prefers Claude Code and Codex; other verified subscription clients may serve eligible roles under Rule 48 and the canonical review procedure. Preserve all required families and capability floors. Use cached subscription authentication and observable transcripts. The deprecated Gemini CLI remains unsupported; supported Google-model clients, Cursor-hosted models, Grok and other providers require target-host and billing verification.

- An agent may **not** author API-calling code — only Brando may.
- Before executing any existing script that loads `~/keys/anthropic_*` /
  `~/keys/openai_*` / `~/keys/gemini_*` / `~/keys/aristotle_*`, pause and
  surface script path + estimated spend, then wait for explicit confirmation.
- When reviewing or QA'ing code, flag any agent-authored direct API call as a
  CRITICAL issue blocking merge.

**Why:** one agent-defaulted Opus 4.7 loop burned $17,752.98 in 25 days on
`anthropic_bm_key_koyejolab` in May 2026, and the lab confirmed on 2026-05-25
it cannot absorb that scale of spend. CLI subscriptions self-throttle; raw API
self-bills. See `~/agents-config/INDEX_RULES.md` Hard Rule 9 for the full
spec, exceptions, and dispatch examples.

## Master and remote-worker completion policy

`master agent:` is an optional explicit coordinator designation; also infer the role when already coordinating workers. The master normally keeps strongest/maximum effort, but selects suitable regular execution workers and effort from the task, checks and shared allowance. Before unattended dispatch, budget through review/publication, synchronize and verify the runbook/checkpoint/inputs on the target, and establish a tested remote watchdog with a verified provider-recovery plan. Notify the master and Brando on meaningful quota-risk/handoff/blocker events; preserve scientific model pins and mandatory acceptance. Existing launchers do not implement automatic failover merely because this rule exists. Full contract: [Trigger Rule 48](INDEX_RULES.md) and [reliable dispatch](workflows/reliable-agent-dispatch.md).
