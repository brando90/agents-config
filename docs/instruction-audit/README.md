# Shared instruction compaction and maintenance

**Doc link:** <https://github.com/brando90/agents-config/blob/main/docs/instruction-audit/README.md>

**TLDR:** Startup reading is a short portable entry point plus a compact contract/router. Detailed rules remain mandatory when triggered, with stable rule numbers; large task-specific guides and historical evidence stay on demand.

## Scope and measurements

Audited on 10-04-2026 against commit `2b53349`. The [inventory](inventory.tsv) covers all 223 tracked paths: 219 text files and four binary artifacts. This is a repository-wide content/loading audit, not a claim that every executable or historical experiment was rerun. Exact file sizes below are deterministic byte counts, not sampled estimates or model token counts.

| Startup file or chain | Before (bytes) | After (bytes) | Reduction |
|---|---:|---:|---:|
| AGENTS.md | 23,006 | 4,352 | 81.08% |
| CLAUDE.md | 24,281 | 4,352 | 82.08% |
| INDEX_RULES.md | 193,333 | 19,082 | 90.13% |
| Codex entry + index, once each | 216,339 | 23,434 | 89.17% |
| Claude entry + index, once each | 217,614 | 23,434 | 89.23% |

Actual injected context depends on the client and overlapping global/project files. These are source-byte savings, not measured latency, token savings or instruction-following accuracy. In particular, the index is explicitly read by the agent, not automatically included by each client's native instruction loader. Duplicate entry loading still costs context, but is now small.

## Decisions from the full inventory

- Replace the duplicated startup rule prose in both entry points with identical shared content. Keep ordinary Markdown and explicit read instructions so clients need no shared import syntax.
- Turn INDEX_RULES.md into the always-read contract and all-rule routing table. All 11 hard rules, 59 trigger rules and 11 guidelines retain their IDs and complete detailed bodies in eight topic files under `~/agents-config/rules/`.
- Move the optional machine/workflow/writing catalog to `~/agents-config/CATALOG.md`. Preserve known index anchors and the sign-in route. Reading a link is an explicit next action; an unloaded link is not context.
- Shorten README navigation and move long operator recipes to the setup reference. Preserve relevant section redirects and clearly label obsolete setup notes.
- Keep task-specific workflow, machine and writing guides on demand. Their length serves a concrete procedure; rewriting them wholesale would risk losing constraints for little startup benefit. Keep executable behavior, binary assets and frozen experiment/review evidence intact except the narrowly listed generated-instruction fixes.
- Fix generated Vals Claude profile guidance to follow the shared entry instead of an old summary label, make the Stanford Codex profile refresh fast-forward-only, correct two path/rule-number comments, and document the actual Claude global file in repo onboarding. These edits do not deploy or overwrite any live profile.

The inventory's initial dispositions are audit recommendations, not a final changed-file list. Git records the implemented scope. All audit artifacts live in this folder; permanent shared validation lives in `~/agents-config/scripts/`.

## Policy preservation and clarified conflicts

The [migration manifest](rule-migration.json) records every original rule's content digest and destination. Its seven exact wording changes are recorded individually:

1. Config refresh no longer silently requests reviewer QA or publishes another owner's pending edits.
2. A short pull-request summary may have fewer than five bullets.
3. Credential discovery says to load values transiently without printing them.
4. `Q go` follows the global explicit-review policy; it alone does not request Mega QA. The matching screenshot workflow agrees.
5. The remote-landing headline says requested review; its description makes the verdict conditional and removes the prohibited “QA: not requested” boilerplate.

These resolve contradictions with existing stronger/current rules; they do not introduce a new review tier or spending authorization. The original SNAP task-specific pre-approval exception remains in Rule 51 and is now visible beside the key-loading approval summary. It still does not authorize new agent-authored provider calls, new charges or broader task scope. Required literal dispatch snippets, review-family gates, fixed evaluation budgets, full denominators, sign-in/final-action boundaries and schedule-format exceptions remain in the detailed rules.

Run the migration receipt on this revision to verify all 81 full rule bodies after link relocation and those seven recorded changes:

```bash
python3 docs/instruction-audit/verify_migration.py
```

This compares with the recorded baseline and is specific to this migration; later intentional policy edits can naturally differ. The ordinary maintenance checker below is the ongoing contract.

## Client compatibility

Checked official documentation on 10-04-2026. Heuristics, parser limits and application-specific memory limits are distinct.

| Client | Loading and size guidance | Repository choice |
|---|---|---|
| Codex | Global `$CODEX_HOME/AGENTS.md` (usually `~/.codex/AGENTS.md`); nonempty override takes precedence. Project files accumulate root-to-working-directory. Documented default combined instruction limit is 32 KiB. | Small uppercase entry, explicit index read, no increase to the cap. Verify loaded paths and active profile. |
| Claude Code | User file is `~/.claude/CLAUDE.md`; `~/CLAUDE.md` is an ancestor file. Target under 200 lines per file; imports expand at startup. The automatic MEMORY.md limit is a separate feature. | Keep a small CLAUDE adapter. Do not eagerly import the long rule collection. Preserve local instructions when connecting the global file. |
| Cursor | Project/nested AGENTS.md; native rule files have their own metadata. Guidance recommends focused rules under 500 lines. Its command-line client reads both root entry families. | Same concise body in both entries; no assumption that the client deduplicates them. |
| Antigravity | Current docs support AGENTS.md and GEMINI.md, including global files under `~/.gemini/`. Per-file truncation at 24,000 bytes includes imports; active always-on/global rules also share a token budget. | The portable entry is well below the file cap; leave long detail pages as explicit task reads. Do not assume Claude-style import semantics. |
| Grok Build | Loads both filename families and compatibility rule directories; trusted-project state affects discovery. `grok inspect --json` reports loaded paths and estimated tokens without a model call. | Small consistent adapters; verify discovery on the actual trusted workspace. No invented universal global filename or cap. |

Sources: [Codex discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [OpenAI prompt-maintenance guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra), [Claude memory and instructions](https://code.claude.com/docs/en/memory), [Cursor rules](https://cursor.com/docs/rules), [Cursor command-line loading](https://cursor.com/docs/cli/using), [Antigravity rules](https://antigravity.google/docs/rules), [Grok project rules](https://docs.x.ai/build/features/project-rules.md).

Claude's newer native AGENTS support does not justify deleting CLAUDE.md: older clients and existing layouts still use the latter, and newer discovery defaults can prefer it when present. Client limits can change; verify current documentation before changing an adapter. A line heuristic alone would have approved the old 108-line CLAUDE.md despite its 24,281 bytes.

## Maintenance budgets and checks

These are repository-chosen growth guardrails, not vendor guarantees:

| File | Bytes at most | Whitespace words at most | Lines at most |
|---|---:|---:|---:|
| Each entry point | 6,144 | 1,000 | 200 |
| Index | 24,576 | 3,200 | 250 |

Put a new universal constraint in the compact contract; place task-specific detail in one canonical rule/workflow and add a precise trigger. Do not grow the entry points by copying each new procedure into both. Remove superseded wording, retain stable IDs, and update the matching source and summary together. A needed exception to a local size target should be justified with measured size and loading impact rather than compressing away a safety or scientific requirement.

```bash
python3 scripts/check_instruction_docs.py
python3 scripts/test_instruction_docs.py
python3 docs/instruction-audit/verify_migration.py  # this migration only
bash -n scripts/install_codex_su_node.sh scripts/setup_claude_vals_snap.sh scripts/refresh-agents-config.sh machine/snap_setup.sh
git diff --check
```

The checker verifies shared entry parity, byte/word/line budgets, all 81 numbered rule routes, and relative file/fragment destinations in the new instruction layer. Seven regression cases cover a valid tree, hidden single-line growth, entry drift, missing/duplicate rule IDs, a missing route, broken destinations and fenced examples. No model calls run inside these checks.

## Runtime verification and requested review

Local Codex global instructions resolve through `/Users/brandomiranda/.codex/AGENTS.md` to `/Users/brandomiranda/agents-config/AGENTS.md`; no global override was present. Claude's `/Users/brandomiranda/.claude/CLAUDE.md` imports `/Users/brandomiranda/agents-config/CLAUDE.md`, and `/Users/brandomiranda/CLAUDE.md` is also a nonempty link. The running builder explicitly read the edited branch index; publication alone does not prove already-running sessions reloaded it. Fresh sessions and other hosts must refresh normally.

Installed client versions were checked without model calls. Grok's read-only discovery check reported the project untrusted, so project-rule loading there was not established; trust was not changed. No standalone Antigravity global entry was present in the inspected conventional paths. Repository compatibility does not claim every host has been deployed or authenticated.

Requested light quality assurance: pending one Claude Code `claude-fable-5-1` / `max` review of the implementation. The review will record actual model metadata, exact scope, findings and deterministic reconciliation here before merge.
