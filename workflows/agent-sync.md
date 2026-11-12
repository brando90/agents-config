# Workflow: shared state and pings between Brando's agents

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/agent-sync.md>

**TLDR:** Shared state across all of Brando's agents and assistants lives in the private repository `brando90/agent-sync` (`PRIORITIES.md`, `assistants/`, `coding/`, `archive/`). Per-project `SYNC.md` files and `[PUSH]` inbox pings remain as documented below. Rule:
[Trigger Rule 71](../rules/services.md#trigger-rule-71).

---

## `brando90/agent-sync` (shared state across all agents and assistants)

Two sides in one private repository (`brando90/agent-sync`, local clone `~/agent-sync`):
- **`assistants/`**: `ub9sc` (Brando's assistant `ultimate_brando9`), Dot, Grokbot, chat apps
- **`coding/`**: Claude Code, Codex, Pi, Antigravity, and any other CLI or desktop agent

Layout:
- `README.md`: what the repo is and the rules below
- `PRIORITIES.md`: under 15 lines, true for both sides
- `assistants/STATE.md` and `coding/STATE.md`: each under one page, one short block per project (what is in flight, owner, next step, blockers; mark unknowns `unknown`, never invent)
- `assistants/log.md` and `coding/log.md`: append-only, one line per finished task: `date | agent | what | link`
- `assistants/requests/` and `coding/requests/`: one small file per ask, named `<to-agent>-<date>-<slug>.md`, plus `.gitkeep`. A request from one side to the other goes in the other side's `requests/`.
- `chats/BRIEF.md`: one-page read-only brief for web/mobile chat apps (ChatGPT, Claude.ai Projects, Gemini Import code) that can read `brando90/agent-sync` but cannot push commits; kept up to date by coding agents whenever `PRIORITIES.md` or `STATE.md` changes.
- `archive/`: old state and finished requests, agents never open it, plus `.gitkeep`

Rules for every agent:
- At task start: read `PRIORITIES.md`, your side's `STATE.md` and the last 20 lines of your side's `log.md`; open a request file only if it is addressed to you.
- At task end: add one line to your side's `log.md`, and update your side's `STATE.md` only if the state changed (coding agents also update `chats/BRIEF.md` when `PRIORITIES.md` or `STATE.md` changes).
- Push straight to `main`, no branches. Pull before writing. Never poll the repo on a schedule. Never write keys, passwords or private notes anywhere. Keep each `STATE.md` and `chats/BRIEF.md` under one page; move old things to `archive/`.

Paste-in for assistants outside git (Dot, Grokbot, chat apps):

```text
Shared state for all my agents lives in the private GitHub repo brando90/agent-sync. At the start of a task, read PRIORITIES.md and assistants/STATE.md and the last 20 lines of assistants/log.md. At the end, add one line to assistants/log.md: date | agent | what | link. Open a file in assistants/requests/ only if its name starts with your name. Never poll it, and never put keys or private notes in it.
```

Paste-in for read-only web/mobile chat apps (ChatGPT GitHub connector, Claude.ai Project GitHub integration, Gemini Import code):

```text
Shared state for all my agents lives in the private GitHub repo brando90/agent-sync. Read chats/BRIEF.md (and PRIORITIES.md) at the start of a task. Since chat apps are read-only for GitHub, never claim you pushed to the repo; when something should be written back or dispatched, give me a short copy-paste block for my coding agent or assistant (with suggested model + effort + harness).
```

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
  agent says so instead of picking one. `scripts/tests/test_agent_sync.py` runs (a) and (c) offline on throwaway repos.
