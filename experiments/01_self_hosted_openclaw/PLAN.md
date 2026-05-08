# OpenClaw 3-Instance Deployment — Action Plan (Brando + Claude split)

**TLDR:** Step-by-step action plan to get OpenClaw fully live across MacBook Air (already partial), MacBook Pro, and mercury2. Each step is tagged 👤 (Brando) or 🤖 (Claude) so it's clear who does what. Authoritative spec is [`cc_prompt.md`](./cc_prompt.md); reproducible install recipe is [`setup-tutorial.md`](./setup-tutorial.md); live deployment checklist is [`todos.md`](./todos.md). This file is the **role-split execution plan**, derived from those, **cross-checked against official OpenClaw docs** (`docs.openclaw.ai`) on 2026-05-08.

Last updated: 2026-05-08
Branch: `claude/review-clock-setup-Lj7CR`

## Doc-verified corrections vs. earlier repo notes

Cross-checking `cc_prompt.md` / `setup-tutorial.md` / `todos.md` against [docs.openclaw.ai](https://docs.openclaw.ai/llms.txt) surfaced four things this plan corrects:

1. **One Telegram bot per instance — not one shared bot.** Per [Telegram channel docs](https://docs.openclaw.ai/channels/telegram.md): *"If you still see `getUpdates` 409 conflicts, another OpenClaw gateway, script, or external poller is likely using the same token."* Three instances polling the same bot will collide. Each host needs its own `@BotFather` bot; Brando ends up DMing 3 bots (or picks one primary + 2 silent failover via `--profile rescue`). The existing scripts assume one shared token — that needs to change before Phase 3.
2. **Gmail is already wired via the `gog` skill — there is no `openclaw channels add --channel google`.** Per [docs index](https://docs.openclaw.ai/llms.txt), the only Google channel documented is **Google Chat** (not Gmail). `setup-tutorial.md:118-198` already documents the correct path (gogcli + bundled `gog` skill auto-flips to Ready), and `todos.md:14` confirms it's working on the Air. The "Wire Gmail" line in `todos.md:40` and the install-script tail message are outdated — what's actually needed is *verifying the agent can invoke `gog` as a tool*, not running a non-existent OAuth command.
3. **Use the built-in `openclaw cron add`, not a custom cron.** Per [cron-jobs docs](https://docs.openclaw.ai/automation/cron-jobs.md), OpenClaw ships with `openclaw cron add --cron "*/15 * * * *" --message ...`, persisted at `~/.openclaw/cron/jobs.json`, surviving restarts. The earlier plan / `agent-prompt.md:111-127` shows raw `*/15 * * * *` cron syntax — keep the schedule but register via OpenClaw's CLI so it's gateway-managed.
4. **SecretRef schema.** Per [secrets docs](https://docs.openclaw.ai/gateway/secrets.md), the schema is `{source, provider, id}`, with `source ∈ {env, file, exec}`. Cleanest path for a raw-text token in `~/keys/`: load it into `TELEGRAM_BOT_TOKEN` env var via the launchd plist, then config holds `{source: "env", provider: "default", id: "TELEGRAM_BOT_TOKEN"}`. Avoids needing to restructure `~/keys/` into a JSON file.

There's also one **production gotcha** worth surfacing: the existing IPv6/DNS workaround we already added to the plist (`NODE_OPTIONS=--dns-result-order=ipv4first`) is documented upstream as `network.autoSelectFamily: false` in OpenClaw config — equivalent fix, but the config-level setting is more durable than env-var patching.

---

## Legend

- 👤 **Brando** — manual, requires you (browser OAuth, phone, physical access, decisions)
- 🤖 **Claude** — automatable from a session (script, edit, verify, commit)
- 🟡 **Parked** — known blocker, deferred (don't waste cycles)
- ⏱ time estimate is for that step only

The plan is sequenced **smallest-unblocked-next-step first**. Don't skip ahead — Phase 2 idempotency assumes Phase 1 works on the Air; Phase 3/4 replication assumes Phase 1 + 2 are stable.

---

## Phase 0 — Where we are now (Air partial, Pro/mercury2 untouched)

From `todos.md:13-21` (verified 2026-04-26):

| Capability                                  | Air | Pro | mercury2 |
| ------------------------------------------- | --- | --- | -------- |
| OpenClaw 2026.4.24 installed                | ✅  | ◯   | ◯        |
| Codex Pro CLI auth (`~/.codex/auth.json`)   | ✅  | ◯   | ◯        |
| Gateway smoke test (`PONG`)                 | ✅  | ◯   | ◯        |
| Telegram bot wired + paired                 | ✅  | ◯   | ◯        |
| Gmail / Calendar / Drive via `gog` skill    | ✅  | ◯   | ◯        |
| Discord                                     | 🟡  | ◯   | ◯        |
| WhatsApp                                    | 🟡  | —   | —        |
| Triage agent loop end-to-end                | ◯   | ◯   | ◯        |
| Idempotency labels + heartbeat + rate limit | ◯   | ◯   | ◯        |
| Daemon survives reboot                      | ✅  | ◯   | ◯        |

**Out of scope for this plan:** WhatsApp (Baileys upstream `status=500` — `todos.md:17`), Discord (parked behind a 90s manual toggle — `todos.md:16`; can be picked up anytime but not on the critical path). Telegram is the mandatory channel.

---

## Phase 1 — Finish the Air triage loop (smallest-unblocked first)

Goal: one real admin email triaged end-to-end (read → classify → DM Brando → approve → send → label) on the Air alone, before replicating.

### Step 1.1 — 👤 Brando: write `config/admin-filter.txt` ⏱ 2 min

You list the senders/domains that count as "admin" so the agent only DMs you about those.

- 👤 Open `experiments/01_self_hosted_openclaw/config/admin-filter.txt` (Claude will create a starter file with placeholders if it doesn't exist — see Step 1.1b).
- 👤 Add 3–8 lines, one per sender pattern. Examples:
  ```
  *@stanford.edu
  *@cs.stanford.edu
  *financialaid*@*
  *@neurips.cc
  noreply@*conference*
  *@registrar.*
  ```
- 👤 Commit: `git -C ~/agents-config add experiments/01_self_hosted_openclaw/config/admin-filter.txt && git commit -m "OpenClaw: seed admin-email filter" && git push`

### Step 1.1b — 🤖 Claude: create the empty `admin-filter.txt` skeleton ⏱ 1 min

If the file doesn't exist yet, write a placeholder with comments explaining the syntax so Brando isn't editing a blank file.

```text
# admin-filter.txt — sender patterns the triage agent treats as "admin"
# One pattern per line. Glob-style. Lines starting with # are comments.
# Match against From: header; case-insensitive.
#
# Example:
# *@stanford.edu
# *financialaid*@*
```

### Step 1.2 — 🤖 Claude: verify the `gog` skill is exposed to the agent ⏱ 5 min

**Correction from earlier notes:** Gmail is already wired via the `gog` skill (gogcli) per `todos.md:14` and `setup-tutorial.md:118-198`. There is no `openclaw channels add --channel google` for Gmail in the [official channel list](https://docs.openclaw.ai/llms.txt) — only Google **Chat**. So this step isn't OAuth, it's verification that the agent can actually call `gog` as a tool.

- 🤖 On the Air, confirm skill state:
  ```bash
  openclaw skills info gog       # expect: "✓ Ready"
  gog -a brandojazz@gmail.com gmail list "is:unread" --max 1 -p   # expect: real data
  ```
- 🤖 DM the bot in Telegram: *"send me an email saying hi from the openclaw test"*. Watch `openclaw logs --follow` to confirm the agent picks `gog gmail send` as the tool.
- 👤 Brando confirms the email lands in his inbox.
- ❌ If skill reports not-Ready, re-run `gog auth add` per `setup-tutorial.md:136-140`.

### Step 1.3 — 🤖 Claude: unlock agent shell/tool execution ⏱ 15 min

The agent currently reports "shell commands blocked by the local hook relay" (`todos.md:41`). Need to identify and flip the right exec-policy / approval setting.

- 🤖 Read OpenClaw's exec-policy docs: `openclaw config get agents.defaults.execPolicy` and `openclaw doctor`.
- 🤖 Identify the gating setting (likely `agents.defaults.execPolicy.shell` or a per-tool allowlist).
- 🤖 Propose the diff to Brando before applying — exec unlock has security implications (the agent is reading arbitrary email + has shell). Ask before flipping.
- 👤 Brando: approve or push back on the proposed setting.
- 🤖 Apply, restart gateway, verify with a smoke prompt that asks the agent to run `whoami`.

### Step 1.4 — 🤖 Claude + 👤 Brando: finalize triage agent prompt ⏱ 10 min

Skeleton already exists at `config/agent-prompt.md`. Three placeholders need Brando's input (see `config/agent-prompt.md:129-141`).

- 👤 Brando answers in chat or by editing the file:
  1. Home shipping address (or "store in `~/keys/brando_personal_facts.json` and let agent read it").
  2. Default payment posture: agent drafts "I'll update by EOD" vs. pauses + asks?
  3. 2–3 sample emails Brando has actually sent, showing tone (so the agent can pattern-match).
- 🤖 Substitute the `<peer-host-1>` / `<peer-host-2>` placeholders with the real hostnames once Pro and mercury2 are known. (For Air-only Phase 1, just use `OPENCLAW_HOST=mac-air` and leave peer hostnames as `pending`.)
- 🤖 Load the prompt into OpenClaw's agent config and restart gateway.

### Step 1.5 — 👤 Brando: create private Telegram channel `openclaw-ops` ⏱ 2 min

This is where heartbeats land. Phase 2 needs it; create it now so Phase 1 testing can also exercise the channel.

- 👤 In Telegram: tap pencil (new message) → New Channel → name `openclaw-ops` → Private.
- 👤 Add `@ultimate_brando9_bot` as **admin** (Channel info → Administrators → Add Admin).
- 👤 Send the channel ID to Claude. Easiest way:
  ```bash
  # On the Air, after the bot is in the channel and you've sent any message:
  curl -s "https://api.telegram.org/bot$(cat ~/keys/openclaw_telegram_bot_token.txt)/getUpdates" \
    | python3 -c 'import json,sys; [print(u["channel_post"]["chat"]["id"]) for u in json.load(sys.stdin)["result"] if "channel_post" in u]'
  ```
- 🤖 Store the channel ID in `~/.openclaw/openclaw.json` under `channels.telegram.opsChannelId` (or whatever OpenClaw's config schema names it — verify via `openclaw config schema`).

### Step 1.6 — 🤖 Claude + 👤 Brando: end-to-end real-email test ⏱ 10 min

The proof point. One real unread admin email goes through the full loop.

- 👤 Brando: identify one unread email from a sender already in `admin-filter.txt`. Don't open it (so it stays unread and the agent picks it up).
- 🤖 Claude: poke the agent (`openclaw agent poke main` or DM the bot "check my email") and watch logs (`openclaw logs --follow`).
- Expected: bot DMs Brando with the `📬 [sender] subject / summary / Draft / approve / edit / skip` format.
- 👤 Brando: reply `approve` (or `edit: <text>`) in Telegram.
- 🤖 Claude: verify Gmail Sent folder has the message and the email got the `triaged-by-claw` label.
- 🤖 Claude: log result in `todos.md` Status & Log.

**If anything fails at this step, STOP. Do not move to Phase 2 until E2E works on Air.** Capture the error in `todos.md` and debug.

---

## Phase 2 — Idempotency + ops layer (Air only, before replicating)

These are the multi-instance prerequisites. Build them on the Air first; the labels and heartbeats are no-ops with one instance, but that's fine — verify the mechanism works before adding readers that race on it.

### Step 2.1 — 🤖 Claude: implement Gmail label idempotency ⏱ 1 hr

Per `cc_prompt.md:64-71` + the `agent-prompt.md` "Loop" section:
- 🤖 Patch the agent prompt / agent runtime to apply `claw-claimed-by-${OPENCLAW_HOST}` atomically on pickup.
- 🤖 Final swap to `triaged-by-claw` only after `gmail.send` returns success.
- 🤖 5-min stale-claim TTL (tightened from spec's 30 min — `cc_prompt.md:160`).
- 🤖 Test: simulate a crash mid-draft (kill gateway after claim label applied, no triaged label). On restart, verify the next loop steals the claim after 5 min.
- 👤 Brando: spot-check Gmail labels in the web UI once to confirm the labels are appearing as expected.

### Step 2.2 — 🤖 Claude: implement heartbeat via built-in `openclaw cron` ⏱ 20 min

Per [cron-jobs docs](https://docs.openclaw.ai/automation/cron-jobs.md), OpenClaw ships a built-in scheduler that persists across restarts (`~/.openclaw/cron/jobs.json`).

- 🤖 Register the heartbeat:
  ```bash
  openclaw cron add --name "heartbeat-${HOSTNAME}" --cron "*/15 * * * *" \
    --tz "America/Los_Angeles" --session isolated \
    --message "post '[${HOSTNAME}] alive @ '$(date -u +%FT%TZ)' to telegram channel openclaw-ops"
  ```
- 🤖 Verify: `openclaw cron list` shows the job; `openclaw cron run <jobId>` triggers an immediate post; check `openclaw-ops` channel.
- 🤖 Hook gateway lifecycle events: `STARTING` on start, `RECOVERED` after a restart-from-crash. (Verify whether OpenClaw exposes lifecycle hooks via plugin API; if not, fall back to a launchd `LaunchEvents` trigger that posts via `openclaw message send --channel telegram --target <ops-chat-id> --message "..."`.)
- 🤖 Add the SILENT watcher: a separate `openclaw cron add` job that fetches recent `openclaw-ops` posts via `gog`-style Telegram lookup (or just maintains its own state file of last-seen-ts per peer), and posts `[<peer>] SILENT >30min — investigate` if threshold breached. No-op until Pro/mercury2 are up; verify the cron itself fires.

### Step 2.3 — 🤖 Claude: implement rate limit ⏱ 15 min

- 🤖 Per-instance: max 1 approval-DM / 60s.
- 🤖 Global ceiling: 2 / 60s across instances. Per `agent-prompt.md:72-77`, this is enforced via per-instance limit + the Gmail label lock; verify both layers are in place.

---

## Phase 3 — Replicate to MacBook Pro

Goal: byte-identical OpenClaw on the Pro using the install script.

### Step 3.1 — 👤 Brando: create a SECOND Telegram bot for the Pro ⏱ 3 min

**Critical: do not reuse the Air's bot token.** Per [Telegram channel docs](https://docs.openclaw.ai/channels/telegram.md), two gateways polling `getUpdates` on the same token cause 409 conflicts. Each instance needs its own bot.

- 👤 Telegram → `@BotFather` → `/newbot` → name e.g. `ultimate_brando9_pro_bot` → copy token.
- 👤 Add the new bot as admin to the `openclaw-ops` channel (so this instance can also post heartbeats).
- 👤 Decide: do you want to DM 3 different bots (one per host) or use the [`--profile rescue` failover pattern](https://docs.openclaw.ai/gateway/multiple-gateways.md) where only the primary bot DMs you and the others stay silent until the primary is silent? Default recommendation: **3 separate bots, all DM-capable**, since the triage loop already rate-limits to 2 DMs/min total — redundancy > tidiness here.

### Step 3.2 — 👤 Brando: choose access path ⏱ 1 min decision

- **Option A (faster, recommended):** Brando provides SSH access from the Air (or wherever Claude runs) to the Pro. Add to `~/.ssh/config`:
  ```
  Host mac-pro
    HostName <pro's local IP or .local>
    User <brando's username on pro>
    IdentityFile ~/.ssh/id_ed25519
  ```
- **Option B (more friction, no SSH config needed):** Brando opens a Terminal on the Pro himself and pastes commands Claude prepares.

### Step 3.3 — 👤 Brando: per-host prereqs on the Pro ⏱ 10 min

- 👤 `codex login` on the Pro (don't copy `auth.json` — refresh tokens rotate; per `cc_prompt.md:161` and `setup-tutorial.md:208`).
- 👤 Install Node 24 if not already (`brew install node@24`).
- 👤 Install `gogcli` (`brew install gogcli`).

### Step 3.4 — 🤖 Claude: scp per-host secrets from Air → Pro ⏱ 2 min

- 👤 Brando: write the **Pro's new bot token** (from Step 3.1) to `~/keys/openclaw_telegram_bot_token.txt` on the Pro (mode 600). NOT the Air's token.
- 🤖 From the Air, copy gogcli auth (this is shared — same Google account, tokens auto-refresh):
  ```bash
  scp -r "$HOME/Library/Application Support/gogcli" mac-pro:'~/Library/Application Support/gogcli'
  ```
- 🤖 Verify the scp'd `gogcli` directory works on the Pro (`ssh mac-pro 'gog -a brandojazz@gmail.com gmail list "is:unread" --max 1 -p'`). Tokens auto-refresh; no re-OAuth needed (per `setup-tutorial.md:198`).

### Step 3.5 — 🤖 Claude: run the install script on the Pro ⏱ 5 min

```bash
ssh mac-pro 'git -C ~/agents-config pull && bash ~/agents-config/experiments/01_self_hosted_openclaw/scripts/install_openclaw_instance.sh'
```

Per `scripts/install_openclaw_instance.sh:6-23`, the script handles npm install, plist patching, daemon install, Telegram wiring, and smoke test. **Note:** the script's tail message references `openclaw channels add --channel google` for Gmail OAuth — that's the outdated path; on the Pro, just rely on the scp'd gogcli tokens (Step 3.4) plus a `gog` skill verification (same as Step 1.2 but on the Pro).

### Step 3.6 — 👤 Brando: post-install manual steps on Pro ⏱ 3 min

- 👤 Open Telegram, `/start` the **Pro's** bot (not the Air's), then run the pairing-approve command on the Pro:
  ```bash
  openclaw pairing list telegram                    # shows the pending code
  openclaw pairing approve telegram <CODE>
  ```
  (Per [docs](https://docs.openclaw.ai/channels/telegram.md): pairing codes expire after 1 hour.)
- 👤 DM the Pro's bot once to confirm it replies as the agent.

### Step 3.7 — 🤖 Claude: verify Pro joins the heartbeat + idempotency dance ⏱ 10 min

- 🤖 Watch `openclaw-ops` channel — Pro should start posting `[mac-pro] alive @ <ts>` within 15 min.
- 🤖 Force a label race: send Brando a test email, watch logs on both Air and Pro. Confirm only one instance applies `triaged-by-claw`. The race is real because OpenClaw [explicitly does not coordinate gateways on the same inbox](https://docs.openclaw.ai/gateway/multiple-gateways.md) — the Gmail-label lock from Step 2.1 is what prevents double-processing.

---

## Phase 4 — Replicate to mercury2 (Linux, different recipe)

mercury2 is a SNAP node — different daemon mechanism, different filesystem. Per `cc_prompt.md:154-165` and `machine/snap.md`.

### Step 4.1 — 👤 Brando: SSH access to mercury2 ⏱ 5 min

- 👤 Confirm `ssh mercury2` works from the launching machine. If not, add SSH config entry + accept host key once. (Per `cc_prompt.md:175`, last attempt failed with "Host key verification failed".)
- 👤 Confirm Kerberos keytab is set up per `~/agents-config/machine/init_no_passwords_snap_kinit.md` (so `krenew` cron can refresh tokens unattended).

### Step 4.2 — 🤖 Claude: install on mercury2 ⏱ 30 min

mercury2 install is **not** identical to macOS — needs the Linux path:
- 🤖 Clone OpenClaw to `/dfs/scratch0/<user>/openclaw` with symlink `~/openclaw → /dfs/scratch0/<user>/openclaw` (DFS-backed, survives node reboots — per `cc_prompt.md:46`).
- 🤖 No `launchd`. Use the SNAP pattern from `machine/snap.md`: tmux session `openclaw` running watchdog while-loop + `@reboot` cron + `krenew` cron.
- 🤖 The existing `install_openclaw_instance.sh` is macOS-flavored — needs a Linux branch added, OR write a sibling `install_openclaw_instance_linux.sh`. **Decision point:** propose the cleaner path to Brando before implementing.

### Step 4.3 — 👤 Brando + 🤖 Claude: secrets + smoke ⏱ 15 min

- 👤 Brando: create a **third** bot via `@BotFather` (e.g. `ultimate_brando9_mercury2_bot`), add to `openclaw-ops` channel as admin, write token to `~/keys/openclaw_telegram_bot_token.txt` on mercury2 (mode 600). Same reason as Step 3.1 — no shared bot.
- 🤖 scp gogcli tokens from Air → mercury2 — but note path differs by OS: `~/.config/gogcli/` on Linux vs. `~/Library/Application Support/gogcli/` on macOS (per `setup-tutorial.md:198`).
- 👤 Brando: `codex login` once on mercury2.
- 🤖 Smoke test: `PONG` via gateway; agent reads one Gmail; posts heartbeat to `openclaw-ops`.

### Step 4.4 — 🤖 Claude: SNAP-specific hardening ⏱ 30 min

Per `machine/snap.md`:
- 🤖 `krenew` cron for Kerberos refresh.
- 🤖 `@reboot` cron to re-launch tmux watchdog after node reboots.
- 🤖 logrotate for `~/openclaw/*.log`.
- 🤖 Document slurm-migration warnings in the experiment's status log (mercury2 may go down for maintenance; the other two instances cover the gap).

---

## Phase 5 — 7-day soak (Definition of Done)

Per `cc_prompt.md:102-114`. Mostly autonomous; Brando provides the "did this actually reduce friction?" signal.

### What runs autonomously (🤖)

- All 3 instances post heartbeats every 15 min.
- Each instance is killed at least once during the window (Claude or Brando triggers); auto-restart within 1 min, verified in logs.
- Gmail label audit: every `triaged-by-claw` came from exactly one host (zero double-processing).
- Zero replies sent without explicit `approve` (verified by inspecting `gmail.send` logs vs. Telegram approval log).

### What Brando does (👤)

- 👤 Triage **≥10 real admin emails** entirely from Telegram. Don't open Gmail web UI for them.
- 👤 Subjective check-in at end of week: did this actually reduce friction? (Per `cc_prompt.md:112` — this is the real ROI test.)

### Bail-out criteria

If any of the 6 measurable DoD items (`cc_prompt.md:106-111`) fail and aren't fixable in a day, document in `todos.md` Status & Log and recommend either:
- (a) consolidate to one instance,
- (b) switch channel (already on Telegram — n/a),
- (c) park experiment.

---

## Hygiene (do alongside, not blocking)

These are not on the critical path but should not be forgotten.

### H.1 — 👤 Brando + 🤖 Claude: rotate Telegram bot token ⏱ 5 min

Current Air token was pasted in a Claude Code chat log (per `todos.md:80`). Risk: anyone with that log can hijack the bot. (Pro and mercury2 bots from Phase 3/4 will have fresh, never-leaked tokens — no rotation needed there at first.)

- 👤 Open Telegram → `@BotFather` → `/revoke` → select `@ultimate_brando9_bot` → confirm. Copy new token.
- 👤 Paste new token into `~/keys/openclaw_telegram_bot_token.txt` on **the Air only** (mode 600). The other instances have their own bots.
- 🤖 Re-load on Air via env var (see H.2) or in-place config edit; restart gateway.
- 🤖 Verify pairing still works post-rotation (`openclaw pairing list telegram`).

### H.2 — 🤖 Claude: move secrets to SecretRef ⏱ 30 min

Per `todos.md:81` and [secrets docs](https://docs.openclaw.ai/gateway/secrets.md). Currently the bot token sits plaintext inside `~/.openclaw/openclaw.json`. Verified SecretRef schema: `{source, provider, id}`.

**Cleanest path for raw-text token files in `~/keys/` — env-var indirection:**

- 🤖 Patch the launchd plist (macOS) / systemd-user unit (Linux) to load the file into an env var:
  ```xml
  <key>EnvironmentVariables</key>
  <dict>
    <key>TELEGRAM_BOT_TOKEN</key>
    <string><!-- read from ~/keys/openclaw_telegram_bot_token.txt at daemon start --></string>
  </dict>
  ```
  (launchd doesn't support file-substitution in plist directly — use a small wrapper script in `ProgramArguments` that exports the env then execs `openclaw gateway`.)
- 🤖 Patch `~/.openclaw/openclaw.json` to use the SecretRef form:
  ```json
  "channels": {
    "telegram": {
      "enabled": true,
      "token": { "source": "env", "provider": "default", "id": "TELEGRAM_BOT_TOKEN" }
    }
  }
  ```
- 🤖 Verify with `openclaw secrets audit --check` (per docs) — should report zero plaintext secrets after.
- 🤖 Update `install_openclaw_instance.sh` to write the SecretRef form, not the inline form. Add the wrapper-script generation for the plist's `ProgramArguments`.

### H.3 — 🤖 Claude: file upstream OpenClaw issues ⏱ 30 min

Per `todos.md:71`. Documenting the bugs we hit:
1. `openclaw onboard --help` returns nothing.
2. Codex harness "not registered" without onboarding.
3. Gateway Telegram `sendMessage` HttpError despite `NODE_EXTRA_CA_CERTS` being set.
4. `paste-token` UI consumes piped stdin char-by-char without submitting.

Filing these is good open-source citizenship and forces upstream to think about the fixes.

---

## Effort summary

| Role        | Total time | Spread                                                                |
| ----------- | ---------- | --------------------------------------------------------------------- |
| 👤 Brando   | ~45–60 min | 8–10 short async touchpoints (≤5 min each), spread over a week        |
| 🤖 Claude   | ~5–8 hr    | Continuous work in 4 sessions (one per phase)                         |
| ⏱ Wall time | ~2 weeks   | Dominated by the 7-day soak window; pre-soak work could finish in 3–4 days |

---

## Open decisions (Brando, please pick when convenient)

1. **Discord:** flip Message Content Intent toggle now (90s, parallelizable with everything else) or defer until Telegram triage is proven? Default: defer, since the critical path is email-triage and Telegram already works.
2. **mercury2 install script:** add Linux branch to existing `install_openclaw_instance.sh`, or sibling `_linux.sh`? Default: sibling file — keeps each script readable.
3. **Triage prompt placeholders:** answer the 3 questions in `config/agent-prompt.md:129-141` — home address, payment posture, tone calibration examples.
4. **SuperCare Health + general "do X" capability** (`todos.md:75-76`): in scope after triage works, or separate experiment? Default: separate experiment (keeps DoD scoped to admin-email triage).

---

## Cross-references

### Internal (this repo)

- Spec: [`cc_prompt.md`](./cc_prompt.md) (6-phase plan, idempotency strategy, DoD, hard rules)
- Recipe: [`setup-tutorial.md`](./setup-tutorial.md) (reproducible install, gotchas)
- Live checklist: [`todos.md`](./todos.md) (granular per-task TODOs, Status & Log)
- Wishlist (post-MVP): [`wishlist.md`](./wishlist.md)
- Standing orders (per-feature specs): [`standing_orders/`](./standing_orders/)
- SNAP playbook: [`~/agents-config/machine/snap.md`](../../machine/snap.md)
- Mac playbook: [`~/agents-config/machine/mac.md`](../../machine/mac.md)

### Upstream OpenClaw docs (verified 2026-05-08)

- Doc index: https://docs.openclaw.ai/llms.txt
- Install + onboard: https://docs.openclaw.ai/install
- Telegram channel (CLI, pairing, gotchas, 409 conflict warning): https://docs.openclaw.ai/channels/telegram.md
- Cron / scheduler (`openclaw cron add`, persistence): https://docs.openclaw.ai/automation/cron-jobs.md
- Multiple gateways (rescue-bot pattern, no shared-inbox coordination): https://docs.openclaw.ai/gateway/multiple-gateways.md
- Gateway lock (per-host, per-port, **not** cross-host): https://docs.openclaw.ai/gateway/gateway-lock.md
- Secrets / SecretRef schema (`{source, provider, id}`): https://docs.openclaw.ai/gateway/secrets.md
- SecretRef credential surface: https://docs.openclaw.ai/reference/secretref-credential-surface.md
- Repo: https://github.com/openclaw/openclaw
- npm package: https://www.npmjs.com/package/openclaw
