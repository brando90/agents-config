# INDEX_RULES.md — Global Rules & Doc Routing

Load only the docs relevant to your current task.

**Remote fallback:** If `~/agents-config/` is not available locally (e.g., running in a cloud sandbox or on the phone), fetch any needed files from `https://raw.githubusercontent.com/brando90/agents-config/main/`. This applies to this file, all machine docs, all workflow docs, and anything else referenced below.

---

## Hard Rules (every response, never skip)

These rules apply to EVERY agent response and EVERY session. Violating any of these is a failure.

1. **Never commit secrets.** Use environment variables or reference existing config files (`~/keys/`, `~/.ssh/config`).
2. **Verify before pushing.** Review diffs for secrets, unintended changes, broken imports.
3. **Run QA before reporting any non-trivial task as done.** Design: **A1 builds → A2 does full QA.** Dispatch one independent reviewer for full QA (correctness + structural in one pass). The reviewer finds AND fixes issues. Fallback chain: primary cross-agent reviewer → Gemini CLI → self-review with best model. One QA dispatch per user-assigned task, not per commit. Structural checks are skipped for markdown-only repos. When unsure whether to run QA, run it. **Quick dispatch:** `codex exec --full-auto "$QA_PROMPT"` (if CC built) or `clauded -p "$QA_PROMPT"` (if Codex built). See [`workflows/qa-correctness.md`](workflows/qa-correctness.md) for the full protocol and [`workflows/qa-structural.md`](workflows/qa-structural.md) for structural check details.
4. **End every response with a TLDR.** Every response — not just task completion — must end with a `**TLDR:**` line: 1–2 sentences summarizing what was done or decided. This applies to all agents (Claude Code, Codex, etc.). No exceptions.
5. **Refresh agents-config before each new user task.** At the start of every non-trivial user request: (1) `git -C ~/agents-config pull` to fetch remote changes, (2) re-read `~/agents-config/INDEX_RULES.md` into your active context so the current session has the latest rules and doc references, (3) if the pull brought changes, also re-read any changed machine or workflow files relevant to your current environment. For long sessions (over 1 hour), also refresh mid-task — check with `date` and compare to your last pull. Push any uncommitted agents-config changes and run QA if changes were pulled from another agent.

---

## Trigger Rules (mandatory when triggered)

These rules fire in specific contexts. When the trigger condition is met, they are mandatory.

6. **Commit, push, and re-read agents-config after any edit.** _Trigger: you or the user modify any file under `~/agents-config/`._ (1) Re-read the changed file(s) so your context stays current for the rest of the conversation. (2) Commit and push to the remote before continuing with the next task — other agents on other machines pull from this repo, so stale config causes drift. Also ensure project-level config files that reference agents-config (e.g., a project's `CLAUDE.md`) stay consistent.
7. **Keep PRs short.** _Trigger: creating a pull request._ The PR description must start with a **Summary** section of 5–10 bullet points max (one line each). Follow with a short **Test plan** (2–3 bullets). Include links (W&B Report URLs, relevant docs). After these two sections, an optional **Appendix** may contain extended details, file lists, or context — but assume the reader stops after the summary. No walls of text.
8. **Commit and push after QA passes.** _Trigger: QA verdict is PASS or FIXED with 0 critical issues._ Immediately `git commit` and `git push` without asking the user. Only escalate to the human if the QA verdict includes critical issues (CRITICAL_ISSUES > 0) or is FAIL. Major-only issues in non-active files (archives, historical results) do not block the commit.
9. **GPU discipline: baseline → estimate → ask → verify → clean up.** _Trigger: about to launch a GPU job._ Before launching any experiment on a GPU, first run or reason from a 1-device baseline whenever practical. Report to the user: (a) estimated VRAM, (b) expected utilization pattern (compute-bound vs CPU/IO-bound), and (c) estimated duration, or explicitly state that the duration is unknown. If the workload appears mostly CPU or IO bound, or uses only brief compute bursts, say so clearly and suggest a smaller machine or a CPU-only node. Do not silently claim multiple devices. Present the per-device allocation plan and wait for user approval. Hardware allows sharing, but PyTorch's caching allocator means memory footprints can spike unpredictably, causing OOM crashes for others. Furthermore, spreading low-utilization work across multiple devices hogs the system's PCIe bandwidth. Therefore, the etiquette rule is: a small memory footprint on one shared device is fine; spreading low-utilization work across multiple devices, or holding idle devices for long durations, must be avoided. **Hard Rule:** The agent MUST explicitly set `export CUDA_VISIBLE_DEVICES=<chosen_ids>` in the bash environment before executing any python script. Verify with `nvidia-smi` within a few minutes of launch. If utilization stays persistently low, report it to the user and suggest consolidating, fixing the input pipeline, or moving off the device. After completion, clean up orphaned processes and report the final state. See [`workflows/expts-and-results.md`](workflows/expts-and-results.md) § Allocation Rules and § Post-Experiment Cleanup.
10. **Mega QA: sequential multi-model review chain.** _Trigger: user says "mega QA", "super QA", "extra careful QA", "deep QA", or similar._ Instead of the default single-reviewer QA, run all 3 models **sequentially** in 3 stages — each does full QA (correctness + structural, with authority to fix), then passes the improved code to the next. Default chain (3 stages, one per model): Codex → CC → Gemini (if CC built) or CC → Codex → Gemini (if Codex built). The builder reviews in the middle (it knows the intent best), Gemini always does the final clean-eyes pass. If the user asks for more rounds, cycle through the chain again (e.g., 6 rounds = chain × 2). Use case: end of work day, before major merges, before sleep — when you can afford the compute for a thorough review. See [`workflows/qa-correctness.md`](workflows/qa-correctness.md) § Mega QA.
11. **Load ML writing guide when editing LaTeX.** _Trigger: editing `.tex` files for an ML research paper._ Read [`writing/ml_research_writing.md`](writing/ml_research_writing.md) into your context before making any edits. Follow its persona, abstract structure, and writing rules throughout the editing session.

---

## Abbreviations

- **ac** = agents-config (this repo, `~/agents-config/`). When the user says "ac", they almost certainly mean agents-config.
- **CC** = Claude Code
- **QA** = quality assurance review (see Hard Rule 3)

---

## Guidelines (best practices)

Follow these as conventions. They improve quality but are lower priority than Hard Rules and Trigger Rules.

12. **Just do it.** Follow direct instructions immediately. Do not draft when told to send. Do not ask for confirmation unless the action is truly destructive (e.g., force-push to main, deleting production data).
13. **Prefer references over full context loading.** Cite file paths as text (e.g., `~/agents-config/machine/mac.md`); load the file only when the task needs it. A "reference" here is a written path to a doc — not a symlink or memory address.
14. **Keep `agents-config` self-consistent.** When modifying this repo, ensure INDEX_RULES.md, README.md, and listed doc paths remain accurate.
15. **Use explicit anchored paths in prose doc references and commands.** Write `~/agents-config/INDEX_RULES.md` or `~/veribench/docs/agent-docs/INDEX.md`, never bare relative references like `docs/agent-docs/`. The user works across many repos and machines, so unanchored paths are ambiguous without context.
16. **Always use `ls -la` (not `ls`) when listing directories for keys, tokens, configs, or credentials.** Hidden (dot-prefixed) files are common for sensitive data — plain `ls` omits them. This applies to any directory likely to hold secrets (e.g., `~/keys/`, `~/.ssh/`, `~/.config/`).
17. **Always use SOTA models for experiments.** When running experiments, use the best available model from any model provider (e.g., Opus 4.6 not Sonnet 4 for Anthropic). When reporting results, always state the exact model ID (e.g., `claude-sonnet-4-20250514`). Weaker models undermine the paper's conclusions.
18. **Use Brando's email signature.** When sending emails on Brando's behalf, CC brando9@stanford.edu and append the signature from [`email-signature.md`](email-signature.md).
19. **Check `~/keys/` for API keys and secrets.** Before asking the user for credentials, always check `~/keys/` first (`ls -la ~/keys/`). Common files: `anthropic_bm_key_koyejolab.txt` (Anthropic API), `openai_bm_key_koyejolab.txt` (OpenAI), `master_hf_token.txt` (HuggingFace), `brandos_wandb_key.txt` (W&B). Load them with `cat ~/keys/<file>.txt` and set as env vars.

---

## Machine Configs

Load the one matching your current environment. Machine docs contain only behavioral constraints and gotchas — not discoverable specs. Run bash commands (`uname -m`, `nvidia-smi`, etc.) to inspect hardware at runtime.

- [`machine/ampere1.md`](machine/ampere1.md) — SNAP ampere1 node (8x A100-80GB)
- [`machine/snap.md`](machine/snap.md) — Stanford SNAP cluster
- [`machine/snap-init.md`](machine/snap-init.md) — first-time setup & verification prompt for a new SNAP node
- [`machine/sherlock.md`](machine/sherlock.md) — Stanford Sherlock HPC
- [`machine/marlowe.md`](machine/marlowe.md) — Stanford Marlowe cluster
- [`machine/mac.md`](machine/mac.md) — local macOS dev machine

## Workflows

- [`workflows/qa-correctness.md`](workflows/qa-correctness.md) — cross-agent QA review: correctness + structural in one pass (default-on)
- [`workflows/qa-structural.md`](workflows/qa-structural.md) — structural QA reference: anti-degradation checks and metrics
- [`workflows/git-worktrees.md`](workflows/git-worktrees.md) — worktree isolation for parallel agents
- [`workflows/expts-and-results.md`](workflows/expts-and-results.md) — experiment structure and results reporting
- [`workflows/tweprints.md`](workflows/tweprints.md) — tweet thread format for research announcements
- [`workflows/blog-posts.md`](workflows/blog-posts.md) — SAIL-style blog post format for research projects
- [`workflows/repo-init.md`](workflows/repo-init.md) — migrating a project to the agents-config pattern

## Writing

- [`writing/ml_research_writing.md`](writing/ml_research_writing.md) — ML research paper writing guide (persona, abstract structure, LaTeX rules). **Loaded by Trigger Rule 11** when editing `.tex` files.
