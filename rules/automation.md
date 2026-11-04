# Automatic Claude and Codex jobs

**Doc link:** <https://github.com/brando90/agents-config/blob/main/rules/automation.md>

**TLDR:** Every job that calls Claude or Codex without a person typing each turn keeps a full transcript log, has an end condition, is listed in the [manifest](../automation/manifest.md), stops at 80% of the weekly limit, emails Brando when it stops, and is never restarted without his yes.

Source: Brando, 11-03-2026, after a silent Mac job and a mercury2 queue drained his Claude plan overnight: "I always want things to be logged!", "I don't want zombie processes that eat up my credits like this again. Ever.", "I prefer 80% tbh.", and the stop-email rule below.

## What counts as an automatic job

Any Claude or Codex call that starts without a person at the keyboard for that call: cron, launchd, systemd, queue runners, supervisors, watchdogs, watchers, loops, tmux or screen sessions left running, headless and background agents, and anything that restarts one of these. It applies to Brando's jobs and to every agent's jobs (Claude Code, Codex, ub9sc, other assistants).

## The rules

1. **Transcript log.** Each job writes a full transcript to a log path chosen before it starts. No `--no-session-persistence`, `--ephemeral` or equivalent flag. Each call also saves its JSON result (model, effort, tokens, cost) to the job's log folder. A job with no log path does not start.
2. **End condition.** Each job has a time limit, an item count or a stop file. Nothing loops forever, and a loop that only waits ("provider hold", "sleep and retry") counts as a loop.
3. **Manifest.** Before its first start, the job is added to [automation/manifest.md](../automation/manifest.md): what it does, owner, account, host, schedule, end condition, log path, the exact stop command and the stop-email recipients. A job that is not in the manifest is stopped when found.
4. **Ceiling at 80%.** Queue gates stop launching new calls at 80% of the weekly limit, for the all-model meter and for the Fable meter, not at 100%. Read the meters before each launch, not once at start.
5. **Stop email.** When a job that was looping stops, for any reason (done, limit, error, killed), it emails brando.science@gmail.com and brandojazz@gmail.com: what it was doing, why it stopped, and suggested next steps, even if the next step is "done, ignore". The email names the log path.
6. **No restart without Brando's yes.** A stopped job is not restarted by hand, by a watchdog, by cron, by launchd keep-alive or from a tmux window without Brando's yes for that job. Stopping is a normal stop (SIGTERM); keep every file and log, and rename instead of deleting.
7. **Models.** Background and automatic jobs default to Sonnet 5.5 at medium effort. Opus or Fable at max effort (and Codex `ultra`) need Brando's yes for that job, written in the manifest row.

## How this fits the other rules

- For unattended jobs this rule wins over the master defaults in Hard Rule 8 and over the automatic continuation through other accounts in Rules 44, 48 and 58: a limit stops the job and sends the stop email; it does not hand work to another account on its own.
- Interactive sessions where Brando or an agent he is talking to types each turn are not automatic jobs; the transcript log rule still holds for them, since sessions are saved by default.
- Secrets never go into logs or the manifest (Hard Rule 1).

## Before starting a job

1. Pick the log path and the end condition.
2. Add the manifest row (stop command included) and commit it.
3. Start the job with the log on; confirm the first log line exists.
4. Put the stop-email step in the job's exit path (a trap or a final step), so a killed job still sends it where the host allows.

## Finding jobs nobody listed

On each host run: `ps -eo pid,etime,args | grep -E 'claude|codex'`, `crontab -l`, `launchctl list` (Mac), `systemctl --user list-timers` (Linux) and `tmux ls`. Compare with the manifest; every extra job is either added with its stop command or stopped.
