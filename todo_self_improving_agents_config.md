# TODO: Self-Improving agents-config

**GitHub Issue:** [brando90/agents-config#28](https://github.com/brando90/agents-config/issues/28)

Goal: make agents-config a **self-improving system** — agents learn from their own outcomes and
write improvements back into the config, so the system gets better without manual intervention.

Inspired by [Garry Tan's "Thin Harness, Fat Skills"](https://x.com/garrytan/status/2042925773300908103)
— specifically the learning loop pattern where an `/improve` skill reads post-task signals (QA
verdicts, failures, user corrections), extracts patterns, and rewrites rules/workflows back into
the skill files. The skill rewrites itself.

---

## Core Idea

```
Agent completes task
        |
        v
QA runs (Hard Rule 3) --> verdict + issues found
        |
        v
/improve skill reads:
  - QA verdicts (PASS/FAIL/FIXED, what was caught)
  - Agent errors (sandbox failures, auth issues, wrong file paths)
  - User corrections ("no, do it this way")
  - Repeated manual patterns ("I keep asking for X")
        |
        v
Extracts patterns, proposes rule/workflow changes
        |
        v
Writes changes back into ~/agents-config/ files
        |
        v
Commits + pushes (Trigger Rule 6) --> all agents on all machines get the update
        |
        v
Next task uses the improved config automatically
```

---

## TODO

### Phase 1: Instrumentation — capture learning signals

```
[ ] Create ~/agents-config/logs/ directory convention for structured outcome logs
[ ] Define a lightweight log schema: {timestamp, task_type, agent, QA_verdict,
    issues_found[], user_corrections[], time_spent, files_touched[]}
[ ] Add a post-QA hook/step that appends a structured log entry after every QA pass
[ ] Track "lessons learned" — when an agent hits an issue and solves it, log the
    problem/solution pair (e.g., bwrap sandbox failure → landlock fix)
[ ] Decide: logs in-repo (versioned, visible) vs. external (~/agents-config-logs/)
    to avoid bloating the repo
```

### Phase 2: /improve skill — the learning loop

```
[ ] Write an /improve skill file (~/agents-config/workflows/improve.md) that:
    - Reads recent outcome logs (last N tasks or last 7 days)
    - Identifies recurring patterns (same QA issue found 3+ times = candidate rule)
    - Identifies one-off fixes that should be permanent (e.g., a sandbox workaround
      that was manually applied → should be in machine docs)
    - Proposes concrete changes: new rules, updated workflows, new machine doc entries
    - Presents proposed changes to the user for approval before writing
[ ] Define trigger: when should /improve run?
    Options: (a) manually via /improve, (b) after every N tasks, (c) weekly cron,
    (d) after any QA FAIL/FIXED verdict, (e) end-of-day review
[ ] Implement the "one-off to permanent" detector: if the same workaround appears
    in 2+ todo files or QA fixes, promote it to a rule or machine doc entry
```

### Phase 3: Automated rule proposals

```
[ ] /improve generates a diff (proposed changes to INDEX_RULES.md, workflows/, etc.)
[ ] Human-in-the-loop: agent shows the diff, user approves/rejects/edits
[ ] On approval: agent commits + pushes (Trigger Rule 6), all agents get the update
[ ] Track rule provenance: each auto-generated rule gets a comment like
    "# Added by /improve on 2026-04-13, based on 3 QA findings re: sandbox failures"
[ ] Safeguard: /improve can only ADD rules or MODIFY existing ones — never DELETE
    Hard Rules (only human can do that)
```

### Phase 4: Cross-session learning

```
[ ] Summarize patterns across sessions: "In the last 20 tasks, QA caught import
    errors 8 times → propose a pre-commit import check rule"
[ ] Detect skill gaps: "Agent was asked to do X 5 times but no workflow exists for X
    → propose creating workflows/X.md"
[ ] Detect stale docs: "machine/ampere1.md hasn't been read in 30 tasks and references
    outdated kernel version → flag for review"
[ ] Build a "config health" dashboard: which rules fire most, which never fire,
    which workflows are most/least used
```

### Phase 5: The Garry Tan loop — skills that rewrite themselves

```
[ ] Allow workflows to have a "## Learning" section that accumulates edge cases
    and refinements over time (like the seating example: "when attendee says X
    but startup is Y, classify as Z")
[ ] Implement version tracking: each workflow edit by /improve increments a version
    counter and logs the change reason
[ ] Test the full loop end-to-end: agent does task → QA finds issue → /improve
    detects pattern → proposes rule → user approves → rule written → next task
    avoids the issue automatically
[ ] Measure improvement: track QA FAIL rate over time, ideally decreasing as
    /improve accumulates rules
```

---

## Design Principles

1. **Human-in-the-loop for rule changes.** The agent proposes, the human approves.
   No autonomous rewrites of Hard Rules.
2. **Thin diffs, fat context.** /improve shows exactly what it wants to change and
   why, with links to the evidence (log entries, QA verdicts).
3. **Commit everything.** All improvements go through git — full version history,
   all agents sync via pull. This is why we use agents-config as a repo, not a
   database.
4. **Don't over-automate initially.** Start with manual /improve invocations, then
   graduate to triggered runs once the signal quality is proven.
5. **The test: if you have to fix the same thing twice, the system failed.** (Garry
   Tan's rule.) Every manual fix should become a permanent improvement.

---

## Related existing work in this repo

- **QA gating (Hard Rule 3)** already captures pass/fail signals — /improve builds on this
- **Trigger Rule 6** (commit + push after agents-config edits) ensures improvements propagate
- **Todo files** (`cursor_ssh_kerberos_todo.md`, `todo_codex_qa_on_snap.md`, etc.) are
  manual versions of what /improve would automate — they capture lessons learned but require
  a human to read them and update rules
- **Mega QA (Trigger Rule 10)** is a deeper review pass — /improve could use mega QA
  findings as richer learning signals

---

## References

- [Garry Tan: Thin Harness, Fat Skills](https://x.com/garrytan/status/2042925773300908103)
  Key quote: "If I have to ask you for something twice, you failed." The /improve skill
  is the mechanism that ensures the system learns from every interaction.
- Existing todo files in this repo:
  - [`cursor_ssh_kerberos_todo.md`](cursor_ssh_kerberos_todo.md)
  - [`codex_remote_control_todo.md`](codex_remote_control_todo.md)
  - [`todo_codex_qa_on_snap.md`](todo_codex_qa_on_snap.md)
  - [`todo_infinite_reauth_kinit_server_side.md`](todo_infinite_reauth_kinit_server_side.md)
