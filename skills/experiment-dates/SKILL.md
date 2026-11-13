---
name: experiment-dates
description: Apply, advance, or backfill `_start_<DDMonYYYY>` and `_end_<DDMonYYYY>` lifecycle suffixes on experiment folders safely without breaking freeze hashes, active worktrees, or cross-repo links. Loaded by Trigger Rule 88.
---

# Experiment Folder Dates (`_start_<DDMonYYYY>` / `_end_<DDMonYYYY>`)

Use this skill whenever creating an experiment folder, closing/archiving a finished experiment, or backfilling `_start_<DDMonYYYY>` and `_end_<DDMonYYYY>` across `experiments/` and `experiments/archive/` ([Trigger Rule 88](../../rules/research.md#trigger-rule-88)).

## 1. Classify Each Folder and Verify Dates (Zero Guessing)

For every directory under `experiments/` and `experiments/archive/` (and `experiments/ideas/` if present):

| Lifecycle state | Folder pattern | Rule |
|---|---|---|
| **Proposed, not started** | `<descriptive_setup>` (no `_start_`, no `_end_`) | Unnumbered proposals and `DEFERRED — NOT RUN` ideas carry neither suffix until work actually starts. |
| **Active, paused, or pending gate** | `experiments/<NN>_<descriptive_setup>_start_<DDMonYYYY>` | Every folder directly under `experiments/`: in flight, paused with unstarted phases, a `Pending` phase/review row in `results.md`, or a finished run kept active by a live dependency (paper integration). Never add `_end_` outside the archive. |
| **Completed (archived)** | `experiments/archive/<NN>_<descriptive_setup>_start_<DDMonYYYY>_end_<DDMonYYYY>` | Only archived folders carry `_end_`. Append it in the same commit that moves the folder to `experiments/archive/`, once the experiment reaches `COMPLETE`, `DONE`, or `STOPPED` with no `PENDING` phase rows (same-day `_start_09Nov2026_end_09Nov2026` or multi-day `_start_10Nov2026_end_11Nov2026`). |

- **Date token (`<DDMonYYYY>`):** Two-digit day (`01`–`31`), TitleCase three-letter English month (`Jan`, `Feb`, `Mar`, `Apr`, `May`, `Jun`, `Jul`, `Aug`, `Sep`, `Oct`, `Nov`, `Dec`), four-digit year (`America/Los_Angeles` date unless pinned otherwise). Prose and files inside the folder still use `MM-DD-YYYY` (Trigger Rule 53).
- **Live creation/closure vs backfilling unlabeled "old" experiments:**
  - **First-time live creation or archiving:** Append today's local `<DDMonYYYY>` (`_start_<DDMonYYYY>` when creating a new folder; `_end_<DDMonYYYY>` when closing/archiving a completed folder) automatically by default.
  - **Backfilling unlabeled historical or migrated folders (trace original upstream source!):** Never mistake a downstream repository-split, folder-import, or consolidation commit date for `_start_` or `_end_` (e.g., `trustworthy-theorem-judges` was split from `veribench` in November 2026, while `01_` started `03May2026` and ended `29Sep2026` in `veribench`, `09_` started `28Sep2026` in `veribench` experiment 102 `human_round/`, and `15_` started `04Nov2026` in `veribench`). Always inspect `SOURCE_MANIFEST.json`, `MIGRATION.json`, `SOURCE_INDEX.md`, `provenance.json`, and `git log --follow` in **both** the current repository and any upstream source repository (`~/veribench`, `~/cert-judge`, `~/judges-dont-need-psychometrics-or-corr`, `~/vb-priv-bmg`).
  - **Imported experiment vs new analysis on old cached data:** Distinguish **(a) an imported or migrated upstream experiment/collection** (inherits the upstream study's genuine `_start_` and `_end_` dates) from **(b) a brand-new experiment conceived to test a new question on an older frozen dataset** (uses the new experiment's own `_start_` and `_end_` dates, e.g., a retrospective prover-outcome or rubric audit conceived, frozen, and run today on cached scores).
  - **End-date stability:** `_end_<DDMonYYYY>` records when the study's execution and final report completed. Later clerical moves, byte-copied archival memos, or zero-call post-hoc bootstrap supplements at import keep the original `_end_` date; only reopening a study for a new experimental phase removes `_end_` while active and sets a new `_end_` on completion.
  - If a date cannot be verified from Git history or upstream/local repo artifacts, report `unknown` rather than guessing.
  - **Git history is the authority.** Folder dates are day-level labels; for exact times or a doubtful label, `git log --follow -- <folder>` here and in the upstream repo settles it. In the repo's `experiments/README.md`, add a short **Folder dates** section that says this and lists, per folder, the start/end commits (hash and date) used as evidence.

## 2. Pre-Rename Safety Inventory

1. **In-flight worktrees and processes:** Run `git worktree list`, `git status -sb`, and check live processes (`ps aux` / `tmux ls`). Never edit another owner's dirty worktree. If the local main checkout holds unpushed private/sensitive commits, run and push the public rename from an isolated detached worktree at `origin/main`, remove that temporary worktree immediately after push (Trigger Rule 19), and reconcile the local checkout without pushing private commits. Record a one-line rebase note in `brando90/agent-sync` (`coding/STATE.md`) if any active worktree adds files under a renamed path.
2. **Freeze-bound files (never edit bytes):** Check every `FREEZE.json`, `SOURCE_MANIFEST.json`, `inference_freeze.json`, `construction_manifest.json`, `verification.json`, and `provenance.json`. Never edit any file whose SHA-256 is pinned by a freeze manifest; `git mv` only the enclosing folder so relative hashes remain 100% intact.
3. **Cross-repo consumer scan:** `git grep` across the repo and sister repos (`~/agent-sync`, `~/veribench`, `~/cert-judge`, `~/judges-dont-need-psychometrics-or-corr`, `~/vb-priv-bmg`) for every old folder basename before moving.

## 3. Execute Rename, Update Live Consumers, and Verify

1. Move directories with `git mv <old_dir> <new_dir>`.
2. Update **live consumers only** using negative lookahead `re.escape(old_basename) + r"(?!_start_)"` so replacements are idempotent:
   - Instructions, Git path globs, and indexes: `AGENTS.md` and `CLAUDE.md` (preserve identical shared content), `.cursor/rules/*.mdc`, `.gitattributes` / `.gitignore` / CI path globs (which silently disarm if left on old folder names), root `README.md`, `experiments/README.md`, and `experiments/archive/README.md` (update live links + add one dated `Previous path → Current path` provenance table while preserving backticked historical `Previous path` strings).
   - Runnable scripts and tests: project verifiers (`scripts/check_project.py`), cross-experiment `sys.path` / path resolvers (`phase0_transfer.py`, `run_exp17.py`, `run_exp18.py`, `costed_allocation.py`), regenerated non-frozen derived outputs (`costed_allocation.py --write`, `refresh_provenance_hashes.py --write`), and active-experiment live docs.
   - Paper provenance `%` comments and `paper_latex/.../README.md` (discard rebuild-only PDF metadata diffs when rendered LaTeX text is unchanged).
   - **Never rewrite:** archived experiment `README.md` / `results.md` bodies, frozen manifests, raw ratings, or source captures.
3. Run full deterministic checks before pushing straight to `main`:
   - Project test suite + paper build pass.
   - All freeze-manifest SHA-256 checks pass.
   - All local Markdown links in live `README.md` / `AGENTS.md` files resolve on disk.
   - `git diff --cached -M --name-status` confirms `R092`–`R100` rename detection (no accidental `D`/`A` pairs or secrets) and `git diff --cached --check` is empty.
4. Sync cross-repo live pointers on `main` (including `brando90/agent-sync` `STATE.md`, `chats/BRIEF.md`, and `log.md`).
