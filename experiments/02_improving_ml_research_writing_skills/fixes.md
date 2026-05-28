# Improving ML Research Writing Skills — Fix Log

**TLDR:** Iterative log of veribench-paper writing fixes promoted to general agents-config rules under `writing/ml_research/` and `INDEX_RULES.md`. Each round records: the original critique surfaced from a writing model's feedback → the general principle extracted → where the codified rule now lives. Companion to `agents.md` (raw user prompts).

**Status (2026-05-28):** Rounds 1–2 in scope. Round 2 adds antipatterns #11–14 (deepity, rhetorical register, em-dash/colon mechanics, micro-brevity) from abstract-polishing feedback. Adjacent ac work (out-of-scope for this experiment) is summarized in `## Adjacent ac changes` at the bottom.

---

## Round 1 — 2026-05-06 (commit `fc5f13b`)

### Source

Two prompts in `agents.md`:

1. **Initial:** quoted writing-model output critiquing the use of "artificial" to describe scaffolded-prompting benchmarks (\textsc{VERINA}, \textsc{CLEVER}). The point: scaffolded chatbot-style prompting is a *real* older paradigm, not a flawed one — the right critique is that it lacks **agentic autonomy** (the new paradigm we're benchmarking).

2. **Expanded** (Brando's synthesis from the broader veribench session): five takeaways covering sentence pacing, audience-calibrated terminology, logical bridging, integrated literature critique, and precise agentic framing.

### Takeaway → codified rule mapping

#### Takeaway 1 — Sentence Structure & Pacing

Avoid run-on sentences chained by weak coordinators (`and`, `while`); break multi-claim sentences; prefer active voice.

**Status:** already covered by existing antipatterns in `ml_research_writing.md` § Sentence-Level Prose Discipline #1–6 (colon overload, sentence budget ≤25 words / ≤1 claim, active voice with concrete antipatterns, garden-path / read-aloud check, connective discipline, de-nominalize). No new rule added — existing coverage was sufficient.

#### Takeaway 2 — Audience-Calibrated Terminology (ML vs FM)

Translate niche subfield jargon to terminology the target audience already owns. Formal-methods *specification* reads to ML reviewers as *prompt spec* / *API spec*; *soundness* / *completeness* are alien to most ML readers.

**Codified at:**
- `writing/ml_research/ml_research_writing.md` § Sentence-Level Prose Discipline **#7** (full antipattern with examples)
- `INDEX_RULES.md` **Trigger Rule 24** (cross-cutting principle, fires for any reader-facing text crossing subfields)

**Examples:**
- ✗ "We benchmark agents on specification generation." (ML reader: prompt spec? API spec?)
- ✓ "We benchmark agents on theorem formulation: extracting a provable mathematical property from raw source."
- ✗ "sound and complete" → ✓ "every accepted proof is correct; every correct proof is accepted."

#### Takeaway 3 — Logical Bridging & Escalation

Don't pivot abruptly from a general problem to a high-stakes domain (security, kernels, finance). Add a bridging sentence naming the *mechanism* that ties the two.

**Codified at:**
- `writing/ml_research/ml_research_writing.md` § Sentence-Level Prose Discipline **#8**
- Linked from `writing/ml_research/write-intro.md` paragraph 1 (motivation move)

**Examples:**
- ✗ "Tests miss bugs. In safety-critical kernels, this is unacceptable." (escalation without mechanism)
- ✓ "Tests certify behavior only on the inputs they run; every other input is a black box. For code whose correctness must hold on all inputs — kernels, cryptographic protocols, financial settlement — finite testing is structurally insufficient."

#### Takeaway 4 — Integrated Related-Work Critique

In a setup / related-work paragraph, attach the specific limitation to the description of prior work in the *same sentence* — not at the end of the paragraph as an after-the-fact verdict. Reader can't tell which paper a late-paragraph critique applies to.

**Codified at:**
- `writing/ml_research/ml_research_writing.md` § Sentence-Level Prose Discipline **#9**
- Linked from `writing/ml_research/write-intro.md` paragraph 2 (set-up-the-bit move)

**Examples:**
- ✗ "VERINA evaluates spec generation. CLEVER scores proof completion. DafnyBench scores Dafny proofs. **However, all these benchmarks evaluate isolated subtasks.**" (late critique; reader can't tell which paper has which gap)
- ✓ "\textsc{VERINA} evaluates spec generation in isolation by feeding models natural-language descriptions, abstracting away the agentic core: extracting properties from raw code. \textsc{CLEVER} scores proof completion against pre-written specifications, removing the burden of formulating the right theorem."

#### Takeaway 5 — Precise Agentic Framing (the original "artificial" issue)

When critiquing older LLM methodologies (chatbot-style scaffolding, prompt filling), don't dismiss them as "artificial" / "naive" / "unrealistic." Name the *specific* missing capability — typically the new paradigm requires something the old paradigm didn't measure (e.g., *agentic autonomy*, *end-to-end inference*).

**Codified at:**
- `writing/ml_research/ml_research_writing.md` § Sentence-Level Prose Discipline **#10**
- Linked from `writing/ml_research/write-intro.md` paragraph 2

**Examples:**
- ✗ "Existing benchmarks are artificial: they feed models partial scaffolds." — "artificial" is wrong since chatbot-style prompting is a real paradigm.
- ✓ "Existing benchmarks score isolated subtasks under chatbot-style scaffolding, abstracting away the autonomy required by modern agentic coding: extracting and formalizing properties directly from raw source."
- **Test:** can you finish "the gap is ___"? If not, the critique is too vague.

### Meta — subdirectory restructure (finalized this round)

The writing skills had been moved on disk into `writing/ml_research/` but were uncommitted, leaving stale path references across the repo. Finalized in this commit:

- `writing/ml_research_writing.md` → `writing/ml_research/ml_research_writing.md`
- `writing/write-intro.md` → `writing/ml_research/write-intro.md`
- `writing/write-abstract.md` → `writing/ml_research/write-abstract.md`
- Path references updated in: `INDEX_RULES.md` (8 refs), `CLAUDE.md` (1), `workflows/expts-and-results.md` (1), `writing/ml_research/write-intro.md` (cross-ref + GitHub URL), `writing/ml_research/write-abstract.md` (cross-refs).

### Commit

```
fc5f13b ML writing: add 4 prose-discipline antipatterns + Trigger Rule 24
        6 files changed, 32 insertions(+), 13 deletions(-)
```

Pushed to `brando90/agents-config@main`.

### QA

Self-review only (markdown-only, additive doc edits, single-reviewer dispatch skipped per Hard Rule 3: "structural checks are skipped for markdown-only repos"). Verified: all path references migrated (grep clean), Trigger Rule numbering correct (24 follows 23), antipattern numbering correct (7–10 follow 6), cross-references resolve.

---

## Round 2 — 2026-05-28 (claude.ai abstract-polishing session)

### Source

A claude.ai chat session polishing the VeriBench NeurIPS-2026 abstract (`paper_latex/NeurIPS_2026_VeriBench/00_abstract.tex`) for arXiv, plus a follow-up Brando note before committing the rule update. Four issues surfaced, none caught by Round 1's antipatterns (#1–10):

1. **Empty-but-fancy phrasing** — "preserving partial-credit signal among sub-frontier systems." Brando flagged "sub-frontier systems" as a *deepity* (Dennett): sounds deep, says little.

2. **Register** — "We argue that ... benchmarks must be X ... and must aggregate ... conjunctively" reads like a position paper; is that appropriate for a datasets/benchmarks or main-track submission?

3. **Mechanics** — the opening sentence had a dangling em-dash, a colon whose unpacking attached to the wrong noun, and a "finite testing / finite test suites" repetition.

4. **Micro-brevity** — "\textsc{VeriBench} instantiates this setting as ..." was active but still wordier than needed; "instantiates this via ..." carries the same relation with fewer frame words.

### Takeaway → codified rule mapping

#### Takeaway 1 — Deepity / empty evocative jargon

Cut evocative phrases that don't survive a plain paraphrase; ban capability-ranking marketing shorthand ("frontier" / "sub-frontier").

**Codified at:**

- `writing/ml_research/ml_research_writing.md` § Sentence-Level Prose Discipline **#11**
- "Plain-paraphrase" row added to the self-edit checklist
- "frontier" / "sub-frontier" added to § Scientific Rigor **#7** no-hype list

**Example:** ✗ "preserving partial-credit signal among sub-frontier systems" → ✓ "while partial progress still earns partial credit."

#### Takeaway 2 — Rhetorical register: prescription vs. contribution

Normative "the field must X" framing is position-paper register; in a benchmarks / main-track paper, carry it as design rationale or as a descriptive fact about the domain. A universal "must" from one artifact is over-extrapolation (Scientific Rigor #4).

**Codified at:** `writing/ml_research/ml_research_writing.md` § Sentence-Level Prose Discipline **#12**.

**Example:** ✗ "We argue that ... benchmarks must be ... agentic ... and must aggregate ... conjunctively" → ✓ "Verification is conjunctive by nature ... \textsc{VeriBench} therefore scores the full pipeline with a geometric mean ..."

#### Takeaway 3 — Em-dash and colon mechanics

Close em-dash pairs; a colon binds its unpacking to the nearest preceding noun phrase — restructure if the intended referent is the whole clause.

**Codified at:** `writing/ml_research/ml_research_writing.md` § Sentence-Level Prose Discipline **#13**. The "name-then-restate" sub-point ("finite testing / finite test suites") is already covered by #6 (de-nominalize) + #11; no separate rule added.

#### Takeaway 4 — Micro-brevity after active voice

Active voice is necessary but not sufficient; after pinning the agent, cut low-content frame nouns and preposition chains.

**Codified at:**

- `writing/ml_research/ml_research_writing.md` § Sentence-Level Prose Discipline **#14**
- "Frame words" row added to the self-edit checklist

**Example:** ✗ "\textsc{VeriBench} instantiates this setting as \emph{agentic} Python-to-Lean~4 autoformalization under verifier feedback." → ✓ "\textsc{VeriBench} instantiates this via \emph{agentic} Python-to-Lean~4 autoformalization under verifier feedback."

### Meta

Additive only; no restructure. Antipatterns #11–14 follow #10, the self-edit checklist gains two rows, and § Scientific Rigor #7's no-hype list is extended. Existing Trigger Rule 13 already routes "apply § Sentence-Level Prose Discipline," so no new `INDEX_RULES.md` trigger was needed. Not codified as rules: a paper-specific TODO to cite `sosso2026agenticprovingprogramverification` in the VeriBench intro, and that "active voice" alone doesn't decide between a colon sentence and a sentence split — the deciding lever there is the #2 sentence budget.

### Commit

```
c41e7df ML writing: add Round 2 ML prose antipatterns (#11-14)

  writing/ml_research/ml_research_writing.md
  experiments/02_improving_ml_research_writing_skills/fixes.md
```

### QA

Self-review only (markdown-only, additive doc edits; single-reviewer dispatch skipped per Hard Rule 3). Verified: antipattern numbering (#11–14 follow #10), checklist rows added, Rigor #7 list extended, cross-refs (#3, #4, #6, #7, #11, #14) resolve.

---

## Round template (for future fixes)

For each new round, append a section like Round 1 above with these subsections:

1. **Source** — link the prompts in `agents.md` (or paste excerpts).
2. **Takeaway → codified rule mapping** — for each takeaway:
   - one-paragraph principle
   - codified at: file + section + #number
   - ✗ / ✓ examples (terse — defer detail to the rule itself)
3. **Meta** — restructure / cleanup work that landed alongside the rules.
4. **Commit** — hash + one-line summary + diff stats.
5. **QA** — what was reviewed, by whom (cross-agent or self-review), and outcome.

---

## Adjacent ac changes (out-of-scope for this experiment)

For situational awareness only — these landed on `main` after Round 1 but did *not* touch `writing/ml_research/` and are tracked elsewhere.

| Commit | Date | Author | Summary | Files |
|---|---|---|---|---|
| `742b7fe` | 2026-05-06 | Claude (Round 1 cont.) | This `fixes.md` + `agents.md` archive | `experiments/02_improving_ml_research_writing_skills/` |
| `603e459` | 2026-05-07 | Brando (solo) | Personal blog writing guides + Trigger Rule 25 | `writing/blog/{rules,blog_writing,write-blog-post}.md`, `INDEX_RULES.md`, `README.md`, `workflows/blog-posts.md` |

The blog-writing additions (`603e459`) live under `writing/blog/` and are loaded via Trigger Rule 25 — separate from the ML-research-writing pipeline this experiment improves. If a future blog/ML overlap surfaces a generalizable writing principle, codify it once and link both trigger rules.
