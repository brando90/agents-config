# OpenClaw Chatops — Fleet Management via Telegram

**TLDR:** Extends OpenClaw from "personal assistant for one person" into "control plane for everything Brando runs" — heartbeats from every bot/worker/dispatcher land in `openclaw-ops`, DMs to the OpenClaw bot translate to shell actions (status, restart, logs) on the right host, and a `bots.yaml` registry tells the agent how to do that for each tracked process. Designed to absorb the conjecture-prover dispatcher reliability problem ([brando90.github.io/conjecture-prover/](https://brando90.github.io/conjecture-prover/)) plus future watchers / workers without growing a parallel ops system.

## The problem this solves

Brando runs many independent processes that need supervision:

- 3 OpenClaw instances (Air / Pro / mercury2) — covered by [`MASTER_PLAN.md`](./MASTER_PLAN.md) Phase 2 already
- Conjecture-prover dispatchers (current pain point — they die silently, no recovery story)
- Future: SuperCare browser-automation watchers, slurm job-queue watchers, W&B run watchers, SBSBZ event-time reminders

Without a unified plane, each one needs its own ops story (different launch mechanism, different alert channel, different restart command). With this design, **adding a new tracked process is a 5-line entry in `bots.yaml`**.

## Three concentric layers, all on Telegram

### Layer 1 — Passive: `openclaw-ops` channel as fleet status feed

Every process posts heartbeats to **one shared private Telegram channel** every 15 min:

```
[mac-air openclaw]            alive @ 19:00:00Z
[mac-pro openclaw]            alive @ 19:00:14Z
[mercury2 openclaw]           alive @ 19:00:31Z
[mercury2 conjecture-prover]  alive @ 19:00:45Z  queue=12 processed=178/hr
[mercury2 wandb-watcher]      alive @ 19:01:02Z
```

Channel scrollback = "what's alive right now?" at a glance. Silence watcher (already in [`MASTER_PLAN.md`](./MASTER_PLAN.md) Step 2.2) catches failures: `[mercury2 conjecture-prover] SILENT >30min — investigate`.

### Layer 2 — Active: command-and-control via DM to the OpenClaw bot

Brando DMs the agent in natural language; agent translates intent → executes via shell:

```
You: what's down right now?
Bot: [mercury2 conjecture-prover] last heartbeat 47 min ago. all others ✓.

You: restart the conjecture dispatcher
Bot: ssh mercury2 → tmux send-keys -t conjecture-dispatcher C-c, then ./run.sh
     ✓ restarted at 19:48:12Z. heartbeat resumed at 19:48:34Z.

You: tail logs of conjecture dispatcher
Bot: <last 30 lines>

You: /list bots
Bot: [registry: 3 OpenClaw instances + 2 conjecture dispatchers + 1 wandb-watcher]

You: kill the air openclaw and restart it
Bot: launchctl bootout gui/$(id -u)/ai.openclaw.gateway → bootstrap
     ✓ restarted at 19:51:02Z.
```

This is the existing OpenClaw agent + shell access (already on the exec-policy unlock plan, [`MASTER_PLAN.md`](./MASTER_PLAN.md) Step 1.3) + a small registry — no new substrate.

### Layer 3 — The registry: `bots.yaml`

Source of truth for everything OpenClaw knows how to supervise. Lives at `experiments/01_self_hosted_openclaw/bots.yaml` (in this repo) so changes are diffed and reviewed:

```yaml
- name: conjecture-prover-dispatcher
  host: mercury2
  type: tmux-watchdog        # or: launchd, systemd-user, cron, none
  start: cd ~/conjecture-prover && ./dispatcher.sh
  restart: |
    tmux send-keys -t conjecture-dispatcher C-c
    sleep 2
    tmux send-keys -t conjecture-dispatcher Enter "./dispatcher.sh" Enter
  health: curl -fsS http://localhost:7777/healthz
  heartbeat_id: mercury2-conjecture-prover
  heartbeat_cron: "*/15 * * * *"
  silence_alert_after: 30m
  owner: brando
  notes: |
    Polls GitHub issues / web form submissions for new conjectures, runs
    proof attempts, posts results back. Dies occasionally on OOM during
    large Lean compiles. Restart is idempotent — safe to fire even if
    it's already running.

- name: openclaw-air
  host: mac-air
  type: launchd
  restart: launchctl kickstart -k gui/$(id -u)/ai.openclaw.gateway
  heartbeat_id: mac-air-openclaw
  heartbeat_cron: "*/15 * * * *"
  silence_alert_after: 30m
  owner: brando

- name: openclaw-pro
  host: mac-pro
  # ... (same pattern, different host + heartbeat_id)

- name: openclaw-mercury2
  host: mercury2
  # ...
```

**Schema:**

| Field                  | Type     | Purpose                                                            |
| ---------------------- | -------- | ------------------------------------------------------------------ |
| `name`                 | string   | canonical ID; what Brando says in chat ("restart conjecture-prover-dispatcher") |
| `host`                 | string   | where it runs (matches an entry in `~/.ssh/config` for non-local hosts) |
| `type`                 | enum     | `launchd` / `systemd-user` / `tmux-watchdog` / `cron` / `none`     |
| `start` (optional)     | string   | command to start fresh (for type=`none` or first-launch scenarios) |
| `restart`              | string   | idempotent command to restart this process                         |
| `health` (optional)    | string   | command that returns 0 iff the process is healthy                  |
| `heartbeat_id`         | string   | the prefix this process posts to `openclaw-ops` ("[mercury2-conjecture-prover] alive @ ...") |
| `heartbeat_cron`       | string   | how often this process posts heartbeats (default `*/15 * * * *`)   |
| `silence_alert_after`  | duration | trigger SILENT alert after this gap (default `30m`)                |
| `owner`                | string   | who gets DMed for fatal alerts (default `brando`)                  |
| `notes`                | string   | freeform; failure modes, gotchas, context                          |

## Adding a new tracked process

Three steps:

1. **Add an entry to `bots.yaml`** with all fields above.
2. **Make the process post heartbeats** — the simplest pattern is a wrapper script that the process's main loop calls:
   ```bash
   # in the process's main loop:
   echo "[$HEARTBEAT_ID] alive @ $(date -u +%FT%TZ)" | telegram-post-to-ops-channel
   ```
   For OpenClaw-managed processes, register a `openclaw cron add --message "..." --cron "*/15 * * * *"` job. For non-OpenClaw processes (like the conjecture dispatcher), a small bash helper script + system cron entry is enough.
3. **Verify** — DM the bot `/list bots`, check that the new entry appears; wait 15 min, check `openclaw-ops` for the heartbeat.

## How this maps to MASTER_PLAN.md

This isn't a new phase — it's an **extension** of Phase 2 (idempotency + ops layer):

- Phase 2 builds heartbeats for OpenClaw instances themselves.
- Once that works for OpenClaw, **adding the conjecture-prover dispatcher to the same heartbeat infra is ~30 min of work** (write the wrapper script, add the bots.yaml entry, register the cron).
- Each subsequent tracked process is the same pattern: wrapper + entry + cron.

Phasing recommendation: don't build chatops layer 2 (DM-driven commands) until at least one non-OpenClaw process is tracked via heartbeats. That confirms the registry pattern works before layering interactive commands on top.

## Open questions for Brando (conjecture-prover side)

Same 4 questions noted in this conversation's queue:

1. **Where do the dispatchers run?** Mac mini at home? mercury2? Both?
2. **How are they launched today?** Manually `./run.sh` in tmux? launchd? systemd-user? cron `@reboot`?
3. **How do they fail?** Silent process exit? OOM kill? Network timeout? Stuck in a loop?
4. **One dispatcher or many?** If multiple workers reading the same queue, Gmail-label-style idempotency matters there too. If single dispatcher, simpler.

Once these land, fill in the `conjecture-prover-dispatcher` entry in `bots.yaml`.

## Status

| Date       | Status                                                                                                                                                |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-05-08 | Design drafted. `bots.yaml` not yet created (waiting on conjecture-prover infra answers from Brando). Registers as future work for Phase 6.x or later. |
