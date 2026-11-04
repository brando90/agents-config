# Automatic job manifest

**Doc link:** <https://github.com/brando90/agents-config/blob/main/automation/manifest.md>

**TLDR:** One row per automatic Claude or Codex job (rules in [automation rules](../rules/automation.md)). A job with no row does not run. Stop-email recipients for every job: brando.science@gmail.com and brandojazz@gmail.com.

## Columns

Job, what it does, owner and account, host, schedule, end condition, log path, stop command, status and date. Add Brando's yes (date) when a job uses Opus, Fable or Codex `ultra` at max effort.

## Active jobs

| Job | What it does | Owner / account | Host | Schedule | End condition | Log path | Stop command | Status |
|---|---|---|---|---|---|---|---|---|
| (none listed) | | | | | | | | 11-03-2026: no active automatic job is known |

## Stopped on 11-03-2026 (kept for the trace; no restart without Brando's yes)

Reported by Brando's desktop agent and by ub9sc; each line says what was verified.

| Job | What it did | Host | How it was stopped | Status |
|---|---|---|---|---|
| `e37-public-fable-recovery` | launchd job that ran Fable max-effort attempts on experiment 37 tasks pulled from the mercury2 queue (28 attempts, 11:12pm to 6:14am) | Mac | unloaded and disabled; plist kept | unloaded 18:43 (Brando's desktop) |
| Opus 5.5 max-effort coordinator worker (pids 86966, 86967) | background coordinator | Mac | killed | stopped 19:03 (desktop report) |
| `accept_queue_recovery.py` | queue runner for experiment 37; one gated top-tier review per packet; checked provider capacity every 5 minutes; stopped only at a window limit or 90% on the public Codex profile | mercury2 | file renamed `accept_queue_recovery.py.REMOVED-20261103`; pinned copy and older `accept_queue*.py` kept, not running | stopped (desktop report) |
| Experiment 37 Codex supervisors and live `codex exec` runs | wrapper loop under `.codex-vb37-public`, seven supervisor wrappers, adjudication loop, two live runs | mercury2 | SIGTERM (pids 3335072, 48854, 48906, 48915, 598754, 3803874, 3803878, 4047715, 3347341, 3348663) | stopped (desktop report; recheck found none alive) |
| Codex daemon cron relauncher | restarted the Codex daemon | mercury2 | cron line commented out | disabled (desktop report) |
| Experiment 37 search supervisors, attempt runs, watchers | search and attempt loops | skampere1, skampere2 | SIGTERM, 19:08 | stopped; ub9sc listing at 19:21-19:25 showed nothing restarted |
| Health watcher loop, reading-copy export loop and its progress script, `run-premises.sh`, `review_closure.py`, `extra_lanes.py` | experiment 37 support loops | mercury2 | stop ordered 19:01 (Brando's desktop) | confirmation pending |
| `codex-remote-control`, `paper-watch` | Mac launchd agents | Mac | unload and disable ordered 19:01, plists kept | confirmation pending |

## How to add a row

Copy a row into Active jobs before the job's first start, fill every column (write `none` where a column does not apply, never leave it empty), and commit the manifest with the job's code.
