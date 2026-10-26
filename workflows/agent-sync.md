# Workflow: shared state and pings between Brando's agents

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/agent-sync.md>

**TLDR:** Codex, Claude Code and ultimate_brando9 agree on a project's state through one `SYNC.md` per project, checked
across every branch by `scripts/agent_sync.py check`; every push to `codex/*` or `claude/*` posts `[PUSH]` in the repo's
agent inbox issue, which wakes the assistant by GitHub's email. Brando never relays state or pushes. Rule:
[Trigger Rule 71](../rules/services.md#trigger-rule-71).

---

## SYNC.md

One file per project, next to its work: `experiments/vb-priv/SYNC.md`, or `SYNC.md` at the root of a one-project repo.
One `## <agent>` section per agent; each agent rewrites **only its own section**:

```markdown
# vb-priv: shared state

## codex
- updated: 2026-10-26T11:20-07:00
- commit: dd49f649
- branch: codex/vb-status
- accepted_tasks: 11/180 (new gate, 10-26-2026)
- gate: new
- doing: rerun batch 3

## claude-code
- updated: ...

## ultimate_brando9
- updated: ...
```

- `updated` is ISO 8601 with its offset (machine-read; human-facing dates stay `MM-DD-YYYY`). `commit` is the commit
  the beliefs rest on. `branch`, `doing`, `next`, `note`, `asks` are free text and never compared.
- Every other `- key: value` line is a fact others may rely on. Use the same key name for the same fact
  (`accepted_tasks`, not `accepted` in one section and `n_accepted` in another). A trailing `(comment)` is ignored
  when values are compared, so `11/180 (new gate)` agrees with `11/180`.
- Write your section after work that changes a fact, in the same push as the work. Delete a fact you no longer hold
  rather than leaving it stale.

## Read before working

```bash
python3 ~/agents-config/scripts/agent_sync.py check            # in the repo; fetches, reads SYNC.md on every branch
python3 ~/agents-config/scripts/agent_sync.py check --file experiments/vb-priv/SYNC.md --no-fetch
```

It keeps each agent's newest section across all branches (so a section on an unmerged `codex/*` branch counts) and
prints one `CONFLICT <key>:` line per disagreement, with each agent's value, date, commit and branch; exit 1. On a
conflict: say so to Brando with both values and their sources, post it in the inbox, and work out which is right from
the run records. Never pick one value silently. Report a number to Brando only after this check passes or the conflict
is named.

## Pings

- **Push → assistant:** `.github/workflows/agent-sync-ping.yml` (template [here](agent-sync-ping.yml)) comments `[PUSH] <repo> <branch> @ <sha>` in the repo's
  `Agent inbox` issue on each push to `codex/**` or `claude/**`: the commits, the SYNC.md diff and any conflicts. It
  @mentions `brando90`, so GitHub emails the comment and the assistant reads it. Coding agents skip `[PUSH]` comments
  unless they name a conflict.
- **Coding agent → assistant / assistant → coding agent:** `[TO-UB9]`, `[FROM-UB9]`, `[DONE]` as in Rule 71.
- **Assistant's session start (backstop, no timer):** before work on Brando's repos it runs
  `python3 ~/agents-config/scripts/agent_sync.py watch --repo-url https://github.com/brando90/vb-priv-bmg --repo-url https://github.com/brando90/agents-config`,
  which prints every `codex/*` or `claude/*` head that moved since its last run (including branches cut from an old
  base without the workflow), then remembers the heads in `~/.cache/agent-sync/seen.json`.

## Set up a repo (once per repo)

1. Copy [`agent-sync-ping.yml`](agent-sync-ping.yml) unchanged to `.github/workflows/agent-sync-ping.yml` on the
   default branch (agents-config too). Codex or Claude Code on Brando's Mac commits it with his account: the
   assistant's GitHub app may not write workflow files. Branches cut after that commit carry it; the assistant's
   `watch` covers older ones. In a private repo each run costs about one Actions minute.
2. The inbox: one open, pinned issue titled `Agent inbox: coding agents <-> ultimate_brando9`. agents-config uses
   [#68](https://github.com/brando90/agents-config/issues/68). A **private** repo gets its own (vb-priv-bmg: its own
   issue), so private work never lands in the public agents-config issue. Optional repo variable
   `AGENT_INBOX_ISSUE` pins the number.
3. `SYNC.md` for each project, with an empty section per agent.
4. Brando's GitHub notification email for mentions reaches an inbox the assistant reads (Settings → Notifications).

## Verify

- (a) Codex pushes a one-line SYNC.md change on a new `codex/*` branch: a `[PUSH]` comment quoting the diff appears in
  the inbox within a minute, and the assistant files a task quoting it, with no message from Brando.
- (b) The assistant writes a line in its section and posts `[FROM-UB9] <repo>: ...`: Codex's next session quotes it back.
- (c) Make two agents' counts differ: `agent_sync.py check` and the `[PUSH]` comment name the conflict, and the next
  agent says so instead of picking one. `scripts/test_agent_sync.py` runs (a) and (c) offline on throwaway repos.
