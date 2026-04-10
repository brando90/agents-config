# INDEX_RULES.md — Global Rules & Doc Routing

Load only the docs relevant to your current task.

**Remote fallback:** If `~/agents-config/` is not available locally (e.g., running in a cloud sandbox or on the phone), fetch any needed files from `https://raw.githubusercontent.com/brando90/agents-config/main/`. This applies to this file, all machine docs, all workflow docs, and anything else referenced below.

---

## Hard Rules (every response, never skip)

These rules apply to EVERY agent response and EVERY session. Violating any of these is a failure.

1. **Never commit secrets.** Use environment variables or reference existing config files (`~/keys/`, `~/.ssh/config`).
2. **Verify before pushing.** Review diffs for secrets, unintended changes, broken imports.
3. **Run the two-step QA chain before reporting any non-trivial task as done.** One QA chain per user-assigned task, not per commit. Step 1: correctness ([`workflows/qa-correctness.md`](workflows/qa-correctness.md)) — must pass before step 2. Step 2: structural ([`workflows/qa-structural.md`](workflows/qa-structural.md)) — skipped for markdown-only repos. **Always dispatch QA to the opposite agent** (Claude Code → Codex, Codex → Claude Code). If unavailable, use the smartest available model of your own agent type. When unsure whether to run QA, run it. **Quick dispatch:** If you are Claude Code, run `codex exec --full-auto "<review prompt>"`. If you are Codex, run `clauded -p "<review prompt>"`. See [`workflows/qa-correctness.md`](workflows/qa-correctness.md) for the full review prompt template.
4. **End every response with a TLDR.** Every response — not just task completion — must end with a `**TLDR:**` line: 1–2 sentences summarizing what was done or decided. This applies to all agents (Claude Code, Codex, etc.). No exceptions.
5. **Refresh agents-config before each new user task.** At the start of every non-trivial user request: (1) `git -C ~/agents-config pull` to fetch remote changes, (2) re-read `~/agents-config/INDEX_RULES.md` into your active context so the current session has the latest rules and doc references, (3) if the pull brought changes, also re-read any changed machine or workflow files relevant to your current environment. For long sessions (over 1 hour), also refresh mid-task — check with `date` and compare to your last pull. Push any uncommitted agents-config changes and run QA if changes were pulled from another agent.

---

## Trigger Rules (mandatory when triggered)

These rules fire in specific contexts. When the trigger condition is met, they are mandatory.

6. **Commit, push, and re-read agents-config after any edit.** _Trigger: you or the user modify any file under `~/agents-config/`._ (1) Re-read the changed file(s) so your context stays current for the rest of the conversation. (2) Commit and push to the remote before continuing with the next task — other agents on other machines pull from this repo, so stale config causes drift. Also ensure project-level config files that reference agents-config (e.g., a project's `CLAUDE.md`) stay consistent.
7. **Keep PRs short.** _Trigger: creating a pull request._ The PR description must start with a **Summary** section of 5–10 bullet points max (one line each). Follow with a short **Test plan** (2–3 bullets). Include links (W&B Report URLs, relevant docs). After these two sections, an optional **Appendix** may contain extended details, file lists, or context — but assume the reader stops after the summary. No walls of text.
8. **Commit and push after QA passes.** _Trigger: QA verdict is PASS or FIXED with 0 critical issues._ Immediately `git commit` and `git push` without asking the user. Only escalate to the human if the QA verdict includes critical issues (CRITICAL_ISSUES > 0) or is FAIL. Major-only issues in non-active files (archives, historical results) do not block the commit.
9. **GPU discipline: estimate → suggest → ask → verify → clean up.** _Trigger: about to launch a GPU job._ Before launching GPU experiments, estimate VRAM and utilization. If the job is small (<20 GB), suggest a smaller-GPU machine. If using multiple GPUs, present the plan and ask for approval. Check utilization within 2 min of launch. After experiments, kill zombies and free GPUs. See [`workflows/expts-and-results.md`](workflows/expts-and-results.md) § GPU Allocation Rules and § Post-Experiment Cleanup.
10. **Load ML writing guide when editing LaTeX.** _Trigger: editing `.tex` files for an ML research paper._ Read [`writing/ml_research_writing.md`](writing/ml_research_writing.md) into your context before making any edits. Follow its persona, abstract structure, and writing rules throughout the editing session.

---

## Guidelines (best practices)

Follow these as conventions. They improve quality but are lower priority than Hard Rules and Trigger Rules.

11. **Prefer references over full context loading.** Cite file paths as text (e.g., `~/agents-config/machine/mac.md`); load the file only when the task needs it. A "reference" here is a written path to a doc — not a symlink or memory address.
12. **Keep `agents-config` self-consistent.** When modifying this repo, ensure INDEX_RULES.md, README.md, and listed doc paths remain accurate.
13. **Use explicit anchored paths in prose doc references and commands.** Write `~/agents-config/INDEX_RULES.md` or `~/veribench/docs/agent-docs/INDEX.md`, never bare relative references like `docs/agent-docs/`. The user works across many repos and machines, so unanchored paths are ambiguous without context.
14. **Always use `ls -la` (not `ls`) when listing directories for keys, tokens, configs, or credentials.** Hidden (dot-prefixed) files are common for sensitive data — plain `ls` omits them. This applies to any directory likely to hold secrets (e.g., `~/keys/`, `~/.ssh/`, `~/.config/`).

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

- [`workflows/qa-correctness.md`](workflows/qa-correctness.md) — cross-agent correctness review (step 1, default-on)
- [`workflows/qa-structural.md`](workflows/qa-structural.md) — anti-degradation refactoring gate (step 2, skipped for markdown-only repos)
- [`workflows/git-worktrees.md`](workflows/git-worktrees.md) — worktree isolation for parallel agents
- [`workflows/expts-and-results.md`](workflows/expts-and-results.md) — experiment structure and results reporting
- [`workflows/tweprints.md`](workflows/tweprints.md) — tweet thread format for research announcements
- [`workflows/blog-posts.md`](workflows/blog-posts.md) — SAIL-style blog post format for research projects
- [`workflows/repo-init.md`](workflows/repo-init.md) — migrating a project to the agents-config pattern

## Writing

- [`writing/ml_research_writing.md`](writing/ml_research_writing.md) — ML research paper writing guide (persona, abstract structure, LaTeX rules). **Loaded by Trigger Rule 10** when editing `.tex` files.
