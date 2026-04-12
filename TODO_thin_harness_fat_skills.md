# TODO: Thin Harness, Fat Skills — Improvement Plan for agents-config

Inspired by [Garry Tan's "Thin Harness, Fat Skills" post](https://x.com/garrytan/status/2042925773300908103) (Apr 11, 2026). Each item maps a gap between the current repo and the framework's principles.

---

## Already strong (no action needed)

- [x] Thin harness — `CLAUDE.md` is 13 lines, bootstraps and delegates
- [x] Resolvers — `INDEX_RULES.md` trigger rules + doc routing = Garry's resolver pattern
- [x] Context efficiency — three-layer architecture, on-demand loading, "prefer references over full context"
- [x] No fat-harness anti-pattern — no bloated tool definitions or god-tools

---

## TODO

### 1. Add vocabulary mapping to README.md
**Why:** People arriving from Garry's post (or the broader discourse) search for "thin harness," "fat skills," "resolvers." The README uses its own terms. A small mapping table makes the repo instantly recognizable to that audience.

**Action:** Add a "Concept Mapping" subsection to the README under "The Three-Layer Architecture" — a 5-row table: Garry's term | agents-config equivalent | notes. See [Appendix A](#appendix-a-vocabulary-mapping-draft).

---

### 2. Introduce parameterized skill files alongside workflows
**Why:** Current `workflows/` are reference docs (protocols the agent reads). Garry's skill files are *invokable procedures with explicit parameters* — like method calls. `/investigate TARGET QUESTION DATASET` produces different output depending on arguments. The repo has no equivalent.

**Action:**
- Create a `skills/` directory for parameterized, invokable markdown procedures
- Each skill file should have: **Name**, **Parameters** (with types/examples), **Steps** (numbered), **Output format**
- Migrate `qa-correctness.md` as the first candidate — it already has a semi-procedural structure. Parameterize it: `REPO_PATH`, `BRANCH`, `BUILDER_AGENT`
- Add a routing entry in `INDEX_RULES.md` under a new "Skills" section
- Keep `workflows/` for non-parameterized reference docs (git-worktrees, blog-posts, etc.)

See [Appendix B](#appendix-b-skill-file-template) for a template.

---

### 3. Add "codify repeated work" guideline to INDEX_RULES.md
**Why:** Garry's rule: "If I have to ask you for something twice, you failed." First time, do it manually. If it recurs, extract it into a skill. The repo has no guideline encouraging agents to self-codify.

**Action:** Add as Guideline 15 in INDEX_RULES.md:

> **Codify repeated work.** If a task pattern recurs, extract it into a skill file (`skills/`) or workflow (`workflows/`). First occurrence: do it manually. Second occurrence: propose a skill file to the user. Never let the same multi-step process stay ad-hoc.

---

### 4. Add latent vs. deterministic guidance
**Why:** Garry calls confusing these "the most common mistake in agent design." The repo has no guidance telling agents when to use LLM judgment vs. deterministic tooling. This matters for research workflows — e.g., use the LLM to design experiments but deterministic scripts to parse W&B results.

**Action:** Add as Guideline 16 in INDEX_RULES.md:

> **Separate latent from deterministic work.** Use LLM judgment (latent) for synthesis, interpretation, experimental design, and code review. Use deterministic tooling (scripts, SQL, compiled code) for parsing, computation, data aggregation, and anything where correctness requires exact reproducibility. When a task involves both, split it: deterministic steps produce structured data, latent steps interpret it.

---

### 5. Add a post-task learning loop workflow
**Why:** Garry's strongest claim: skills should improve themselves. His `/improve` skill reads feedback, extracts patterns, and writes new rules back into skill files. The repo currently has no self-improvement mechanism — all updates are human-initiated.

**Action:**
- Create `workflows/learning-loop.md` (or `skills/improve.md` if adopting the skills pattern)
- Structure: after a task completes, the agent reviews what went wrong or was suboptimal, proposes a concrete rule or parameter change to the relevant skill/workflow file, and presents it to the user for approval
- Start conservative: agent *proposes* changes, human approves. Don't auto-rewrite skill files yet
- Add a Trigger Rule: "After QA reveals a recurring issue pattern, propose an update to the relevant workflow or skill file"

See [Appendix C](#appendix-c-learning-loop-sketch).

---

### 6. Add a diarization workflow for research contexts
**Why:** Diarization = the model reads everything about a subject and writes a structured one-page profile. This is directly useful for literature reviews, codebase onboarding, and experiment post-mortems — all common in the research workflows this repo supports.

**Action:**
- Create `skills/diarize.md` — parameters: `SUBJECT`, `SOURCES` (list of paths/URLs), `FOCUS_QUESTION`
- Output: a structured markdown profile with sections like SUMMARY, KEY FINDINGS, CONTRADICTIONS, TIMELINE, GAPS
- Use case: onboarding to a new codebase, synthesizing a paper cluster, profiling a dataset

---

## Priority order

| Priority | Item | Effort | Impact |
|:---------|:-----|:-------|:-------|
| 1 | Vocabulary mapping in README | 15 min | High (discoverability) |
| 2 | Codify-repeated-work guideline | 5 min | High (behavioral shift) |
| 3 | Latent vs. deterministic guideline | 5 min | Medium (quality improvement) |
| 4 | Parameterized skill files | 1-2 hrs | High (structural upgrade) |
| 5 | Learning loop workflow | 1 hr | Medium (compounding returns) |
| 6 | Diarization skill | 30 min | Medium (research-specific) |

---

## Appendix

### Appendix A: Vocabulary mapping draft

| Garry Tan's term | agents-config equivalent | Notes |
|:---|:---|:---|
| Thin harness | `CLAUDE.md` + `agents.md` (Layer 1) | 13-line entry points that bootstrap and delegate |
| Fat skills | `workflows/` (Layer 3) | Currently reference docs; see TODO #2 for upgrade to parameterized skills |
| Resolvers | `INDEX_RULES.md` Trigger Rules + doc routing (Layer 2) | Trigger Rule 10 is a textbook resolver: "editing .tex → load ml_research_writing.md" |
| Latent vs. deterministic | Not yet explicit | See TODO #4 |
| Diarization | Not yet present | See TODO #6 |

### Appendix B: Skill file template

```markdown
# Skill: /skill-name

> One-line description of what this skill does.

## Parameters

| Parameter | Required | Description | Example |
|:----------|:---------|:------------|:--------|
| `TARGET` | Yes | What to operate on | `~/veribench/src/` |
| `QUESTION` | No | Focus question | "Why are eval scores dropping?" |

## Steps

1. **Scope.** [What the agent does first]
2. **Gather.** [What data to collect, from where]
3. **Analyze.** [Latent — judgment and synthesis]
4. **Verify.** [Deterministic — run tests/checks]
5. **Output.** [Structured result format]

## Output format

[Describe the expected output structure — markdown sections, table, etc.]
```

### Appendix C: Learning loop sketch

```
Trigger: QA reveals a pattern that has occurred 2+ times
         OR user flags a recurring friction point

Steps:
1. Identify the recurring issue (what went wrong, which files, which workflow)
2. Find the relevant skill or workflow file
3. Draft a concrete rule addition or parameter change (1-3 lines)
4. Present the proposed change to the user with:
   - What happened (the pattern)
   - What would change (the new rule)
   - What it prevents (future impact)
5. If approved, apply the edit and commit under Trigger Rule 6

Example:
  Pattern: "Agent keeps running full test suite when only one module changed"
  Proposed rule in qa-correctness.md:
    "When changes are scoped to a single module, run only that module's tests first.
     Run the full suite only if scoped tests pass."
```
