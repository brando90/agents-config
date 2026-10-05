# Documentation catalog

**Doc link:** <https://github.com/brando90/agents-config/blob/main/CATALOG.md>

**TLDR:** Optional machine, workflow and writing references. Read only the documents needed for the task; mandatory trigger routing is in `~/agents-config/INDEX_RULES.md`.

## Machine Configs

Load the one matching your current environment. Machine docs contain only behavioral constraints and gotchas — not discoverable specs. Run bash commands (`uname -m`, `nvidia-smi`, etc.) to inspect hardware at runtime.

- [`machine/ampere1.md`](machine/ampere1.md) — SNAP ampere1 node (8x A100-80GB)
- [`machine/mercury1.md`](machine/mercury1.md) — SNAP mercury1 node (10x A4000-16GB)
- [`machine/mercury2.md`](machine/mercury2.md) — SNAP mercury2 node (10x RTX A4000-16GB)
- [`machine/skampere1.md`](machine/skampere1.md) — SNAP skampere1 node
- [`machine/skampere2.md`](machine/skampere2.md) — SNAP skampere2 node
- [`machine/snap.md`](machine/snap.md) — Stanford SNAP cluster
- [`machine/snap-init.md`](machine/snap-init.md) — first-time setup & verification prompt for a new SNAP node
- [`machine/sherlock.md`](machine/sherlock.md) — Stanford Sherlock HPC
- [`machine/marlowe.md`](machine/marlowe.md) — Stanford Marlowe cluster
- [`machine/agent-clis.md`](machine/agent-clis.md) — shared Cursor Agent / Grok Build / Antigravity CLI install, PATH, and login playbook for both Macs and SNAP (`scripts/install_agent_clis.sh`)
- [`machine/mac.md`](machine/mac.md) — local macOS dev machine (incl. Vibe/Leanstral install; § Agent board — the per-machine dashboard of every Claude/Codex/SNAP agent session and its tmux window, installed via `scripts/agent_board_install.sh`)
- [`machine/mac-never-sleep-lid.md`](machine/mac-never-sleep-lid.md) — reusable prompt/workflow for configuring a Mac to stay awake when the lid closes; load via `machine/mac.md` when Brando asks for never-sleep lid behavior.
- [`machine/macos-chrome-zombie-leak.md`](machine/macos-chrome-zombie-leak.md) — Cursor-terminal stall / hot Mac from a wedged Google Chrome zombie leak; diagnose + SIGKILL parent + tripwire. **Loaded by Trigger Rule 59.**
- [`machine/macos-ai-apps/ai_agent_automatable_setup_codex_clauded.md`](machine/macos-ai-apps/ai_agent_automatable_setup_codex_clauded.md) — reusable shell-automatable trusted-agent setup for Codex, Claude Code, Cursor, ChatGPT, and Manus on macOS
- [`machine/macos-ai-apps/manual_macos_permissions_checklist_ai_apps.md`](machine/macos-ai-apps/manual_macos_permissions_checklist_ai_apps.md) — reusable manual macOS Privacy & Security checklist for local AI apps

## Workflows

- [`workflows/cross-machine-projects.md`](workflows/cross-machine-projects.md) — proposed shared project identity and task catalog across agent tools, accounts, and computers; extends the private agent board with separate coordination controls. Design only, not a new execution policy.
- [`workflows/broad-investigation.md`](workflows/broad-investigation.md) — cross-agent investigation, official-source research, recovery and evidence before declaring blockers (Trigger Rule 62).
- [`workflows/codex-connector-tandem.md`](workflows/codex-connector-tandem.md) — verify connectors in the actual desktop, ChatGPT Work or cloud coding runtime; use authorized private data bridges when native tools are absent.
- [`workflows/verified-host-bootstrap.md`](workflows/verified-host-bootstrap.md) — reuse a verified host, maintain private configuration provenance and replicas, and verify native destination setup (Trigger Rule 62).
- [`workflows/valkyrie.md`](workflows/valkyrie.md) — public Vals documentation, command/model-routing diagnosis and the boundary between public procedures and private host configuration.
- [`workflows/jazz-playalongs/README.md`](workflows/jazz-playalongs/README.md) — Brando's jazz play-along audio (Aebersold, Hal Leonard, Snidero): Google Drive is the source of truth; checklist to sync new songs to both Macs, the Pixel and Spotify local files, plus verification scripts. Mirrored to a Google Doc (see its SYNC NOTE).
- [`workflows/qa-correctness.md`](workflows/qa-correctness.md) — QA tiers: deterministic checks (always), reviewer QA and Mega QA (only on request)
- [`workflows/qa-structural.md`](workflows/qa-structural.md) — structural QA reference: anti-degradation checks and metrics
- [`workflows/git-worktrees.md`](workflows/git-worktrees.md) — worktree isolation for parallel agents
- [`workflows/expts-and-results.md`](workflows/expts-and-results.md) — experiment structure and Markdown-first results reporting; external dashboards only on explicit request
- [`workflows/statistics-reporting.md`](workflows/statistics-reporting.md) — what statistics to report and why: Hard Rule 11's cheap minimum for every project, the judge-human agreement checklist (free vs costly rows, ICC notation, honest data reuse), paper/experiment consistency, a worked VeriBench example
- [`workflows/question-screenshot-ingest.md`](workflows/question-screenshot-ingest.md) — `Q go` screenshot-to-question workflow: save images, transcribe, create `questions/<NN>_<slug>/`, open issue, Mega QA, push `main`
- [`workflows/tweprints.md`](workflows/tweprints.md) — tweet thread format for research announcements
- [`workflows/blog-posts.md`](workflows/blog-posts.md) — SAIL-style research lab blog post format; use `writing/blog/` instead for Brando's personal site
- [`workflows/repo-init.md`](workflows/repo-init.md) — migrating a project to the agents-config pattern
- [`workflows/research-repo-layout.md`](workflows/research-repo-layout.md) — four-bucket research repo root (`experiments/`, `paper_latex_and_notes/`, `src/`, optional data bucket), the "where does X go?" decision procedure, and the staged migration procedure for reorganizing a repo with live branches (Trigger Rule 49).
- [`workflows/multi-account-agent-clis.md`](workflows/multi-account-agent-clis.md) — running one CLI under several accounts: `CLAUDE_CONFIG_DIR` / `CODEX_HOME` profile dirs, the `clauded-vals` / `clauded-su` / `codexd-vals` / `codexd-su` wrapper pattern, per-account model entitlements, and the mac→SNAP push scripts (`push_claude_su_snap.sh`, `push_codex_su_snap.sh`, `push_codex_vals_snap.sh`) with their credential guardrails
- [`workflows/reliable-agent-dispatch.md`](workflows/reliable-agent-dispatch.md) — master/worker selection, shared usage budgets, verified handoff, remote watchdog, bounded provider recovery and notifications (Trigger Rule 48).
- [`workflows/remote-job-dispatch.md`](workflows/remote-job-dispatch.md) — three ways to run a job on another SNAP node, plus the local path `scripts/deploy_cc.sh` (a Claude Code worker in its own byobu/tmux session on this machine, Remote Control on, so you can attach or phone-drive it): (1) **SSH fire-and-forget** (`scripts/ssh-submit.sh`) for live sessions, (2) **DFS watcher daemon** for headless/batch (code: `~/ultimate-utils/py_src/uutils/job_scheduler_uu/`), (3) **phone dispatch** via git-inbox poller (`scripts/git-inbox-poller.sh`) for claude.ai web/mobile and cloud sandboxes. The legacy smart-mode wrapper ([`workflows/smart-job-agent-prompt.md`](workflows/smart-job-agent-prompt.md)) is not a reliable agent recovery controller; use direct jobs with Rule 48's verified execution/recovery contract. **Prerequisite:** `~/dfs` → `/dfs/scratch0/<user>` symlink on every node (see [SNAP Required Symlinks](rules/hosts.md#snap-required-symlinks-every-node)). **Checking jobs:** when asked "is my job running" / "check jobs," always inspect BOTH the watcher queue AND detached tmux/nohup/GPU processes on source node and peers — see `workflows/remote-job-dispatch.md`.
- [`workflows/smart-job-agent-prompt.md`](workflows/smart-job-agent-prompt.md) — single source of truth for the smart-mode agent-wrapper prompt used by all three remote-dispatch paths. Edit here first, then propagate.

## Writing

- [`writing/ml_research/ml_research_writing.md`](writing/ml_research/ml_research_writing.md) — ML research paper writing guide (persona, abstract structure, LaTeX rules). **Loaded by Trigger Rule 13** when editing `.tex` files.
- [`writing/ml_research/write-intro.md`](writing/ml_research/write-intro.md) — CS197 six-move introduction skill: paper-agnostic, takes an abstract path and draft path, auto-detects edit-in-place vs context-only mode. **Loaded by Trigger Rule 21** when drafting / revising a paper's Introduction section.
- [`writing/ml_research/write-abstract.md`](writing/ml_research/write-abstract.md) — CS197 six-move abstract skill: paper-agnostic, takes a title and free-form rough ideas, optionally a draft path for context. Produces a ~150-word first draft plus 2–3 alternate openings. **Loaded by Trigger Rule 22** when drafting / revising a paper abstract.
- [`writing/ml_research/write-poster.md`](writing/ml_research/write-poster.md) — conference-poster skill: paper-agnostic, takes a paper (arXiv/OpenReview link, repo path, or PDF) plus a venue, and produces a compiled Stanford beamerposter PDF (RylanSchaeffer/Stanford-LaTeX-Poster-Template, XeLaTeX) with a render-and-look visual QA pass. **Loaded by Trigger Rule 30** when making a conference poster.
- [`writing/ml_research/write-sail-blog-post.md`](writing/ml_research/write-sail-blog-post.md) — SAIL blog skill: paper (link/path/PDF) → SAIL-format explainer draft + conference-roundup blurb, delivered as a PR in the paper's repo for co-author sign-off. **Loaded by Trigger Rule 31** for SAIL / lab blog posts; format spec in [`workflows/blog-posts.md`](workflows/blog-posts.md).
- [`writing/ml_research/write-tweet-thread.md`](writing/ml_research/write-tweet-thread.md) — X/Twitter tweprint skill: paper → 6–9-tweet CoDaPO-style thread draft, ≤280 chars/tweet programmatically checked, PR + per-paper review email. **Loaded by Trigger Rule 32**; voice reference [`workflows/tweprints.md`](workflows/tweprints.md).
- [`writing/ml_research/write-linkedin-post.md`](writing/ml_research/write-linkedin-post.md) — LinkedIn announcement skill: paper → CoDaPO-style post draft (~350–500 words, institutional credit, exact-number results), PR + per-paper review email. **Loaded by Trigger Rule 33**.
- [`writing/blog/rules.md`](writing/blog/rules.md) — compact non-negotiable checklist for Brando-style personal blog posts. **Loaded by Trigger Rule 25** when drafting / revising personal blog posts.
- [`writing/blog/blog_writing.md`](writing/blog/blog_writing.md) — full Brando personal blog voice and structure guide based on recent posts in `~/brandomiranda/`. **Loaded by Trigger Rule 25**.
- [`writing/blog/write-blog-post.md`](writing/blog/write-blog-post.md) — reusable skill for converting rough idea dumps into polished personal blog drafts or edit-in-place revisions. **Loaded by Trigger Rule 25**.

**Event and Project File Organization (Brando, 10-01-2026).** Keep all artifacts (scripts, images, generated PDFs, READMEs, promo material) for a given event or project together in a single canonical folder (e.g., `events/<event-name>/`). Do not split outputs by file type into separate `output/pdf/` or `output/images/` directories. Colocation reduces confusion.
