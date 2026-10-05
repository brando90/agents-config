# Investigate broadly and complete the authorized task

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/broad-investigation.md>

**TLDR:** Combine relevant local evidence, current official documentation, upstream source and authorized live checks before declaring a problem blocked. Recover from failed searches or commands and carry the user's objective through verification without making the user supply discoverable facts.

User instruction, 09-24-2026. Applies to every agent, project and host. This implements [Trigger Rule 62](../INDEX_RULES.md) and complements the existing decision and recovery rules.

## Start from the intended outcome

**Investigate the user's problem, not only the command they happened to type.** If a requested spelling or subcommand does not exist, inspect the installed command-line interface (CLI) help and find the supported operation. A request to list runs should result in a run listing or a precisely diagnosed access failure, not an answer that an alias is unsupported.

Resolve available context yourself: the selected executable, package version or source revision, execution host, configuration path, environment overrides and relevant project instructions. Read only the configuration fields needed for diagnosis; do not print complete credential files. Expand shorthand paths to actual absolute paths when reporting them.

“Load only relevant docs” is a context-management rule, not a prohibition on investigating outside the current repository. Inspect relevant sibling repositories, installed packages, service documentation and authorized remote hosts when the evidence leads there. Widen searches by hypothesis and likely location; do not indiscriminately dump a home directory or private records into context.

## Use complementary sources

**Use current primary sources whenever behavior, commands or capabilities are uncertain.** Do not wait for Brando to supply a website or explain a third-party tool.

1. Inspect local help, configuration selection, logs and the installed implementation. Determine what is actually running.
2. Open relevant links supplied by the user. Search the official documentation and upstream repository for the operation, exact non-secret error and installed version. Search the web when needed; prefer official documentation, source, release notes and maintainer discussions for technical conclusions.
3. If a page reader fails, try the official site's Markdown representation, documentation index, sitemap, raw repository file or another available read-only retrieval tool. A retrieval-tool error is not evidence that the underlying page or solution does not exist.
4. Where authorized and useful, check the actual service with read-only metadata or status requests. Keep public documentation, client implementation and deployed behavior distinct; resolve disagreements with versioned source and live evidence.
5. Batch independent checks in parallel when supported. Delegate independent bounded investigations when explicitly authorized by the user or applicable instructions. Keep dependent operations, mutations and shared-resource ownership ordered.

Never include credentials, private endpoint addresses, account identifiers or unpublished internal model names in public search queries. Public research does not authorize publishing private evidence or contacting collaborators.

## Keep moving through recoverable failures

**A failed attempt should change the next diagnostic step.** Distinguish syntax, installation, configuration selection, authentication, permissions, network access, service availability and an unsupported feature. Use another relevant source or authorized route when the first one fails; do not repeat identical attempts without a reason they could succeed.

**Prefer connectors and the agent's own browser before using Brando's computer (10-02-2026).** First use working purpose-built connectors or the Codex/ChatGPT desktop app's in-app browser, kept in the background. Existing reliable, non-interactive command-line routes are also appropriate because they do not interrupt his work. Verify the intended service account and workspace in the selected route. If a connector is unavailable, fails, uses the wrong account, or lacks the required operation, try the agent-owned browser before the personal browser or native desktop apps. Do not repeat a known failed route just to satisfy the ordering.

**Completion remains the goal.** When these routes cannot complete the authorized task, continue through the least disruptive available computer-use fallback. Briefly state the concrete reason for the fallback and keep any desktop interaction minimal; prefer background window actions and avoid stealing focus, moving the pointer or altering the clipboard while Brando is working when the tools support that. Preserve active user input and do not compete with him for a window. A preference for connectors is not a reason to abandon work, bounce mechanical steps to Brando, or wait for redundant permission. Respect explicit deferrals, stronger task-specific restrictions and required tool confirmations; ask only for a genuinely human-only step or missing authority. Verify the requested result. Browser access and connector authorization are separate facts; neither establishes the other.

Apply reversible fixes already authorized by the task, preserve the prior state where needed and rerun the check that demonstrates the user's requested outcome. State consequential assumptions while continuing useful independent work. Ask only for information or authority that cannot be recovered from the authorized context and genuinely gates the remaining action.

Broad investigation does not authorize new spending, personal experiment funding, changing scientific settings, overwriting another owner's work or bypassing access controls. Respect project-specific funding and execution rules. Metadata discovery must not silently turn into a paid inference test.

- **When external fetches fail** — Follow [broad investigation](../workflows/broad-investigation.md) before declaring the resource unavailable: try relevant official Markdown, indexes, raw source or another authorized reader, and distinguish a tool failure from an access restriction. Record meaningful attempts and failure modes beside the work, capture reachable metadata and complete independent parts. Ask the user for missing material only if it remains essential and unavailable through authorized alternatives. Mark unresolved sections honestly; **never fabricate the missing content** or bypass access controls. Historical example: `experiments/03_youtube_transcript_takeaway_loop/`.

**Desktop/cloud connector use:** Follow [connector tandem verification](../workflows/codex-connector-tandem.md): identify the exact runtime, discover its tools and verify the source account/workspace with a bounded read in each destination. A shared plugin catalog or relaxed permissions does not establish callable tools. When native tools are absent, transfer only authorized source data through a verified private bridge; label imported-data access separately from native connector access, and keep private receipts out of this public repo.

## Verify and leave reusable knowledge

**Report the verified result and the remaining boundary of the evidence.** Include what was attempted, the decisive observation, any repair, and the check performed afterward. Distinguish local installation, remote access, model catalog visibility, successful inference and completed evaluation; success at one layer does not prove the next.

If work is still blocked, name the failed operation, concrete error and missing dependency or authority. Complete the useful independent parts first. Do not report a vague “cannot access” when the evidence identifies a narrower failure.

Record reusable public procedures and official links in agents-config. Keep credentials, private bootstrap packets, internal routing details and private run evidence in the authorized private store. Record dated observations as observations, not permanent availability guarantees. Update both agent entry points when adding an enduring cross-agent rule.

When another authorized machine already works, apply [verified-host bootstrap](verified-host-bootstrap.md) before rebuilding the setup. Reuse its approved portable configuration and evidence, compare freshness, then verify the destination independently.

For Vals work, continue with [Valkyrie documentation and diagnosis](valkyrie.md).
