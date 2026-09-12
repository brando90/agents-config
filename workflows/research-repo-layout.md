# Workflow: Research Repo Layout — Four Buckets at the Root

**TLDR:** A research repo's root holds **four directories and a short list of files**:
`experiments/`, `paper_latex_and_notes/`, `src/`, and (only if the repo ships data) one
data bucket. Everything else is a stray: route it into a bucket, move it out of the
repo, or `.gitignore` it. This doc gives the canonical tree, the "where does X go?"
decision procedure, and the **staged migration procedure** that keeps a reorg from
silently resurrecting old paths when in-flight branches merge.

Governing rule: `~/agents-config/INDEX_RULES.md` **Trigger Rule 49**.
Naming and archiving *inside* `experiments/` is **Trigger Rule 39** — this doc does not
restate it.

---

## Why

Brando, 2026-09-12, on `~/veribench` (24 top-level entries):

> "I'm seeing so many folders and stuff in the root of my repo. I prefer to keep
> things simple. Usually I only really need 1. experiments folder with all my
> experiments, results etc 2. latex file for my papers/notes 3. src for the main code
> and prompts."

A research repo accretes root directories one plausible decision at a time — a
`results/` for one cache file, a `tmp/` for one PDF, a `tweets/`, a course folder from
an unrelated class, three near-synonymous code dirs. Each addition is locally
reasonable; the sum is a root nobody can scan. The fix is a **closed** list of
buckets, so "where does this go?" has an answer instead of a new directory.

---

## The canonical tree

```
<repo>/
├── experiments/              # 1. every experiment: scripts, results, checkpoints, ledgers
│   ├── NN_LABEL_setup/       #    named per Trigger Rule 39
│   ├── ideas/                #    optional/undecided research (Rule 39)
│   └── archive/              #    finished strands, one-line outcome in archive/README.md
├── paper_latex_and_notes/    # 2. anything a human READS: papers + notes
│   ├── <VENUE>_<Year>_<Proj>/#    one dir per venue, main file 00_main_*.tex
│   ├── notes/                #    research notes, standards docs, tweets, threads
│   ├── support/              #    figure/table generators, reference checkers for the paper
│   └── site/                 #    blog, talks, handoff docs, any static site
├── src/                      # 3. all importable code AND prompts
│   ├── py_src/               #    the installed package (or src/<pkg>/)
│   ├── prompts/              #    agent + judge prompt templates
│   └── scripts/              #    shared runnable tooling (not experiment-local scripts)
├── <name>_dataset/           # 4. ONLY if the repo ships a data artifact; else omit
└── README.md  CLAUDE.md  AGENTS.md  LICENSE  pyproject.toml  uv.lock  setup.sh
    tests/  .github/  .claude/  .gitignore  .gitattributes
```

**`paper_latex_and_notes/`, not `paper_latex/`.** Notes become papers. Keeping them in
one bucket means a note is never homeless and never spawns a `notes/` root dir.

**The fourth bucket is conditional.** A repo that *ships* a dataset or benchmark keeps
it at the root (`veribench_dataset/`, `data/`) because it is the **product**, not
source: it has its own toolchain (a Lean `lake` project, a HF dataset card), its own CI
job, and thousands of external references. A repo with no released data artifact has
three buckets, and incidental data lives inside the experiment that produced it.

**Root files are an allowlist, not a dumping ground:** `README.md`, `CLAUDE.md` /
`AGENTS.md`, `LICENSE`, the package config and lockfile, a setup script, and dotfiles.
Keep these few and boring — if you find yourself adding a *second* setup script or a
third loose `.md`, that is the signal a bucket should own them. `tests/` is a permitted
root directory: pytest, coverage and CI all expect it there, and fighting that
convention costs more than the one extra entry.

---

## Decision procedure — "where does X go?"

Ask in this order; stop at the first yes.

| Ask | Then |
|---|---|
| Is it unrelated to this repo's purpose? (coursework, another project, a one-off side repo) | **Out of the repo.** Copy it somewhere safe **first** (`cp -R`), *then* `git rm` — `git rm` preserves nothing but history, so it is not itself a backup. Zero inbound `git grep` references is supporting evidence, not proof: also confirm the purpose mismatch and look for consumers grep cannot see (CI, sibling repos, a person's habits). |
| Is it generated or ephemeral? (`tmp/`, `_build/`, `.venv/`, caches, a lone `*_cache.json`) | **`.gitignore` it.** Never commit a cache to buy a root directory. |
| Is it an experiment, a run, a result, a checkpoint, or a ledger? | `experiments/` (Rule 39 for the name) |
| Is it prose a human reads? (paper, note, blog, slide deck, talk, tweet thread, handoff doc, standards doc) | `paper_latex_and_notes/` |
| Is it code, a prompt template, or shared tooling that other things import or invoke? | `src/` |
| Is it the released data artifact itself? | the data bucket |
| Still unsure? | It is almost always an experiment. Put it in `experiments/`; promotion out is cheap, a new root dir is not. |

### Anti-patterns, named

- **A root directory for one file.** `results/judge_cache.json` is a gitignore entry, not a bucket.
- **A root directory that is empty.** That is a bug; delete it.
- **A root directory only an *archived* script imports.** That is a compatibility shim — archive it *with* the script it serves, not at the root.
- **Near-synonymous code dirs** (`utils/`, `<proj>_metric/`, `<proj>_prompts/`, `py_src/` all at the root). They are one bucket: `src/`.
- **A root scratchpad.** Use the session scratchpad or `experiments/<current>/`.
- **Promotion as an excuse.** Rule 39 promotes live infrastructure out of `experiments/` — promote it *into `src/`*, not onto the root.

---

## Migration procedure (the part that bites)

A layout reorg is a mass rename. In a repo with live agents it is **not** a safe
refactor, for a reason that is easy to miss:

> A branch cut **before** the rename still carries the old paths, and git handles the
> cases differently. An **edit** to a file you renamed follows the rename into its new
> home (rename detection). But a branch that **adds** a file under the old directory
> re-creates that directory on merge, and every stale path string in prose, config, CI
> and runbooks merges back verbatim. The reorg does not loudly conflict — the tidy root
> just grows back, one merge at a time.

Verify rather than assume: `git merge-tree` (or a throwaway merge) against each unmerged
branch tells you exactly which old paths reappear, for your git version and your branches.

So:

### 1. Inventory in-flight work first — always

```bash
git worktree list                       # local checkouts other agents may be mid-edit in

# open PRs AND the top-level dirs each one touches (--limit defaults to 30; raise it)
for n in $(gh pr list --state open --limit 100 --json number -q '.[].number'); do
  printf 'PR #%-5s %s\n' "$n" \
    "$(gh pr view "$n" --json files -q '.files[].path' | cut -d/ -f1 | sort -u | tr '\n' ' ')"
done

# every unmerged branch, same view (a branch need not have a PR yet)
for b in $(git branch -r --format='%(refname:short)' | grep -v HEAD); do
  printf '%-55s %s\n' "$b" \
    "$(git diff --name-only origin/main..."$b" | cut -d/ -f1 | sort -u | tr '\n' ' ')"
done
```

`gh pr list` alone only names PRs — it does not show their paths, and it caps at 30 by
default, so page it explicitly. Any bucket that appears in either listing is a bucket you
cannot rename today without follow-up.

### 2. Stage the reorg

- **Stage 1 — now:** move only what **no** open PR, branch or worktree touches, plus the renames the user explicitly asked for. Ship it as one PR.
- **Stage 2 — flag day:** the rest, once the open PRs land or are closed. Announce it, land it in one commit, and immediately rebase or re-cut any surviving branch.

State the split explicitly in the PR body and leave it in the repo (see step 6) so the
next agent does not have to re-derive it.

### 3. Move with `git mv`, never delete-and-recreate

`git mv` keeps rename detection, so `git log --follow` and `git blame` survive and the
diff stays reviewable. Verify with `git diff --cached -M --name-status`, which prints
`R100 <old> <new>` for a pure rename. (`git diff --stat` renders renames as
`{old => new}/file` and never prints the `R` status code — don't look for `R100` there.)

### 4. Update live references, never frozen ones

```bash
git grep -l -- 'old/path' -- ':!experiments/archive' ':!research_archive'
```

- **Update:** packaging (`pyproject.toml` `packages`/`pythonpath`), CI workflows, hooks, `CLAUDE.md` / `AGENTS.md` / `README.md`, imports, and any script still run.
- **Do not update:** frozen manifests, recorded results JSON/CSV, archived experiment READMEs, dataset version records. Those state what the path *was* when the run happened; rewriting them falsifies the record. Note the old→new mapping once instead.

### 5. Re-check the things a rename disarms **silently**

- **Hook and CI globs.** A hook that routes on the path — typically a `case "$fp" in */paper_latex/*/*.tex) ... ;; *) exit 0 ;; esac` — stops matching after a rename to `paper_latex_and_notes/` and takes its no-op branch instead, exiting 0. Nothing errors; the hook simply never runs again. (Other glob contexts are noisier: an unmatched glob in a shell command usually passes through literally and the command then fails, and `shopt -s failglob`/`nullglob` change that again — the silent case is the routing one, which is exactly what hooks use.) Grep every hook and workflow for the old directory name, then fire the hook once to prove it still runs.
- **Implicit `sys.path`.** A top-level package imported as `import <pkg>` because it sat at the repo root breaks the moment it moves under `src/`. Add `[tool.pytest.ini_options] pythonpath = [...]` (or the packaging equivalent) **in the same commit**, and run the test suite to prove it.
- **Relative paths inside moved files.** `.code-workspace` folder lists, `lakefile` paths, and `Path(__file__).parent / ".."` chains all shift by the depth you moved them.

### 6. Leave a map

Add `LAYOUT.md` (or a section in the repo's `CLAUDE.md`) with the four buckets, the
dated old→new table, and the remaining stage-2 moves. Per Rule 39, rename history lives
in that map — **not** in a rules file — so grepping live files for a stale directory
name stays a real check instead of hitting its own changelog.

---

## Quick audit

Run this on any research repo. There is no hard limit, but a root you cannot take in at
a glance — much past a dozen entries — is the symptom this rule exists to treat.

```bash
cd <repo>
echo "top-level entries: $(ls -A | wc -l)"
ls -A
# orphan check: a tracked root dir nothing else mentions is a candidate to evict
for d in */; do
  d=${d%/}
  n=$(git grep -lI -- "$d" -- ':!'"$d" 2>/dev/null | wc -l)
  printf '%-28s %s inbound refs\n' "$d" "$n"
done | sort -k2 -n
```

Zero inbound references plus "not one of the four buckets" ⇒ evict it.
