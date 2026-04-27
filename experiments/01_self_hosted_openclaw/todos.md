# OpenClaw 3-Instance Deployment — TODOs

**TLDR:** Living checklist of everything left to do across the 3-instance OpenClaw deployment (Air ✓ partial, MacBook Pro ◯, mercury2 ◯). Grouped by phase; check items as they land. Authoritative spec is [`cc_prompt.md`](./cc_prompt.md); reproducible install recipe is [`setup-tutorial.md`](./setup-tutorial.md).

Updated: 2026-04-26

## Pickup state (resume here next session)

Air instance is the active one; Pro and mercury2 untouched. Last working state on the Air:

| Channel / capability | State | Notes |
|---|---|---|
| Telegram (chat surface) | ✅ working | Bot `@ultimate_brando9_bot` paired with Brando, agent replies via Codex Pro / GPT-5.5. Token at `~/keys/openclaw_telegram_bot_token.txt` (mode 600), already rotated once. |
| Gmail (read + send) | ✅ working via `gog` skill | `gogcli` 0.13.0 installed, OAuth done, all 7 Workspace APIs enabled in GCP project 721441778080. `openclaw skills info gog` shows ✓ Ready. |
| Calendar / Drive / Docs / Sheets / Tasks / People | ✅ working via `gog` skill | All verified end-to-end (`gog -a brandojazz@gmail.com calendar list`, etc.) |
| Discord | 🟡 blocked on user actions | Bot created (ID `1498169663278813254`, token in `~/keys/openclaw_discord_bot_token.txt`), wired into OpenClaw config, but Discord refuses with **code 4014** because Message Content Intent is OFF on the dev portal AND bot is in 0 servers. **To resume:** flip the toggle in Bot tab → Save Changes; then run the OAuth2 URL Generator and invite the bot to a server Brando owns. |
| WhatsApp | 🟡 parked on upstream issue | Baileys 7.0.0-rc.9 returns `status=500` from web.whatsapp.com on every pair attempt. Not local. **To resume:** wait 24h+ then retry once; if still broken, defer until stable Baileys v7. Also revisit 4-device cap (current usage: phone + Mac WA = 2; +3 OpenClaws would be 5). |
| Gmail label idempotency / heartbeat / rate limit | ◯ not started | Blocked on "real Gmail flow alive on Air first" — i.e. one approval round-trip via Telegram before we add the multi-instance coordination layer. |
| Triage admin-email loop end-to-end | ◯ not started | Needs admin-filter list (Brando) + one real test email. Agent prompt is drafted in `config/agent-prompt.md`. |
| MacBook Pro install | ◯ not started | Needs SSH config OR Brando runs `scripts/install_openclaw_instance.sh` himself in Pro's terminal after `scp`'ing the per-host secrets. |
| mercury2 install | ◯ not started | Needs SSH access; Linux path (no launchd) — tmux + watchdog + cron + krenew. |

**Suggested resume sequence (smallest unblocked next step first):**
1. Brando enables Discord Message Content Intent + invites bot to a server (~90s of his time) → I restart gateway, confirm Discord ✓, push a test DM
2. Brando edits `config/admin-filter.txt` with his real admin-sender list (~1 min) and DMs the Telegram bot one real triage to validate the loop
3. Replicate to Pro via the install script
4. Replicate to mercury2 (Linux path — different recipe, see `cc_prompt.md` v2 section)
5. Wire idempotency labels + heartbeat + rate limit (autonomous)
6. 7-day soak

Last commit on this experiment as of pickup: see `git -C ~/agents-config log --oneline -10 -- experiments/01_self_hosted_openclaw/`.

## Air instance — finish the loop

- [x] OpenClaw 2026.4.24 installed via npm (with `~/.npmrc cafile` fix)
- [x] Codex Pro CLI auth verified (`~/.codex/auth.json`, plan=pro, valid 2026-12-11)
- [x] Smoke test: `openclaw infer model run --gateway --prompt PONG` returns PONG via `openai/gpt-5.5` on codex harness
- [x] Telegram bot created via @BotFather (`@ultimate_brando9_bot`), wired via `openclaw channels add --channel telegram`, paired with Brando's user id, two-way chat works
- [ ] **Fix gateway operator-CLI sendMessage HttpError** *(PARKED — agent runtime reply path works fine via gateway's grammy session; this only blocks `openclaw message send` from the CLI for operators; come back to it after the triage loop is otherwise complete)*. Diagnosis so far: cert chain to api.telegram.org is legit (GoDaddy → telegram.org), `node -e "fetch(...)"` with `NODE_EXTRA_CA_CERTS=/etc/ssl/cert.pem` returns OK, but the plist-set env doesn't reach the gateway's send subprocess despite bootout/bootstrap. Adding `NODE_OPTIONS=--dns-result-order=ipv4first --use-system-ca` and even `NODE_TLS_REJECT_UNAUTHORIZED=0` to the plist didn't help. Suggests OpenClaw's CLI `message send` spawns a fresh node subprocess outside the gateway session.
- [ ] **Wire Gmail** — `openclaw channels add --channel google` (browser OAuth, scopes: readonly + send + modify)
- [ ] **Enable agent shell/tool execution** — current agent reports "shell commands blocked by the local hook relay"; need to flip the right approval/exec-policy setting so the triage agent can read Gmail and apply labels
- [ ] **Decide admin-email filter** — 3–5 sender domains/keywords (`*.stanford.edu`, conference orgs, financial-aid, etc.); write to `config/admin-filter.txt`
- [ ] **Write triage agent system prompt** — read unread admin emails → classify → draft reply → DM Brando in Telegram with subject + 1-line summary + draft → wait for `approve` / `edit: <text>` / `skip` → on approve, send via Gmail and apply label
- [ ] **End-to-end real-email test** — pick one real unread admin email; let the agent draft; approve from Telegram; confirm Gmail send + label applied
- [ ] **Create private `openclaw-ops` Telegram channel**, add bot as admin (will be reused for heartbeats)

## Idempotency + ops (multi-instance)

- [ ] **Implement Gmail label idempotency** — atomic add of `claw-claimed-by-<host>` on pickup; final swap to `triaged-by-claw` on send; **5-min stale-claim TTL** (tightened from spec's 30 min for 3 readers)
- [ ] **Implement heartbeat** — each instance posts `[host] alive @ <ts>` to `openclaw-ops` Telegram channel every 15 min; `[host] STARTING` / `[host] RECOVERED` on lifecycle events. If silent >30 min, the others alert
- [ ] **Rate limit** — max 1 approval-DM per minute per instance, max 2 per minute total

## Multi-instance deployment

- [ ] **MacBook Pro install** — provide SSH config (or do install in Pro's own terminal); replicate Air recipe; scp Telegram + Gmail tokens; `codex login` separately
- [ ] **mercury2 install** — provide SSH access; Linux path (no launchd): tmux + watchdog while-loop + `@reboot` cron; clone OpenClaw to `/dfs/scratch0/<user>/openclaw` with `~/openclaw` symlink (DFS-backed, survives node reboots); coordinate with `~/agents-config/machine/snap.md` (krenew + keytab + slurm-migration warnings)
- [ ] **Setup scripts in agents-config** — `experiments/01_self_hosted_openclaw/{config/openclaw.json.template, scripts/install_openclaw_instance.sh, scripts/update_openclaw_instance.sh}` so re-installs are byte-identical
- [ ] **Per-machine secret bootstrap** — generate Telegram + Gmail tokens once on Air, scp to Pro and mercury2 into `~/keys/` (mode 600, never committed)

## Hardening + definition of done

- [ ] **Daemon survives reboot on each box** (Air launchd, Pro launchd, mercury2 cron + tmux + krenew)
- [ ] **Crash-recover proven** on each instance during a 7-day soak (kill-and-watch test in logs)
- [ ] **Log rotation** — Linux logrotate on mercury2; macOS `find ~/openclaw/*.log -mtime +14 -delete` cron on Air + Pro
- [ ] **Brando triages ≥10 real admin emails entirely from Telegram** — never opens Gmail web UI for them
- [ ] **Audit:** zero false-positive sends, zero double-processed emails (Gmail label trail shows each `triaged-by-claw` from exactly one host)

## Spec hygiene

- [ ] **Update `cc_prompt.md` 2-instance → 3-instance** — Telegram mandatory (WhatsApp 4-device cap), Telegram-as-heartbeat, 5-min TTL, per-machine `codex login`
- [ ] **Document upstream OpenClaw quirks** — file (or link to) issues for: `openclaw onboard --help` returns nothing; codex harness "not registered" without onboarding; gateway telegram sendMessage HttpError despite NODE_EXTRA_CA_CERTS being set; `paste-token` UI consumes piped stdin char-by-char without submitting

## Beyond admin-email triage (general personal-assistant)

- [ ] **SuperCare Health login + tasks** — agent should be able to log in to supercare.com (and similar personal portals) via OpenClaw's bundled `browser` plugin and complete tasks Brando assigns ("check my prescription status", "request a refill", "schedule X"). Requires: (a) browser plugin enabled (already loaded in stock 63); (b) credentials in `~/keys/supercare_credentials.json` (mode 600, not committed); (c) per-task prompt from Brando in Telegram; (d) 2FA strategy — for sites that require it, agent DMs Brando the code request, Brando pastes back. Start with non-2FA flows.
- [ ] **General "do X for me" capability** — extend the triage prompt to handle ad-hoc requests Brando DMs the bot (not just inbox triage): "book me a haircut", "summarize my W&B runs from this week", etc. Requires the same exec-policy / tool-execution unlock as task #3 plus per-capability prompts and credential storage.

## Hygiene & follow-ups

- [ ] **Rotate Telegram bot token** — current token was pasted in a Claude Code chat log + lives plaintext in `~/.openclaw/openclaw.json`; revoke via @BotFather `/revoke`, store rotated token only in `~/keys/openclaw_telegram_bot_token.txt`, then re-bind via `openclaw channels add`
- [ ] **Move secrets out of `~/.openclaw/openclaw.json`** — use SecretRef (`--ref-source file --ref-id ~/keys/...`) for the bot token + any other secret the channels write inline
