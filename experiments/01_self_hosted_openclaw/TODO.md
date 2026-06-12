# OpenClaw — Open TODOs

**TLDR:** Items still open after PR #46 (master plan consolidation) merged. Tracking here + as a GitHub issue assigned to Brando so nothing falls through the cracks. Canonical design lives in [`MASTER_PLAN.md`](./MASTER_PLAN.md); this file is just the "what's next" punch list.

## Phase 1 — finish Air email triage E2E (immediate critical path)

- [x] **1.1** Seed `config/admin-filter.txt` with Phase 1.6 SuperCare sender patterns (`*@supercare.com*`, `*@supercarehealth.com*`, `*amanadero@supercare.com*`, `*papresupply@supercare.com*`) plus a guarded `mailer-daemon@googlemail.com` bounce pattern — done 2026-06-12.
- [ ] **1.2** Verify `gog` skill exposed to agent: `openclaw skills info gog` → ✓ Ready; smoke test via DM
- [x] **1.3** **Unlock agent shell/tool execution** — *done 2026-05-09 on Pro via local node_modules patch.* Upstream codex extension registers a hook relay then loses lookup at PreToolUse time (gateway logs `native hook relay not found` on every `nativeHook.invoke`). 1-line patch to `dist/extensions/codex/harness.js` adds `{nativeHookRelay:{enabled:false}}` to the runAttempt options, which sends `features.codex_hooks: false` to codex. Codex falls back to its own sandbox/approval (already yolo+danger-full-access+never per `~/.codex/config.toml`). Patch + diff + how-to-undo + how-to-reapply-after-`npm install` documented in [`runbook.md` "Shell exec — local patch required"](./runbook.md). Install script now applies the patch automatically on every run. Verified with real `date +%s && uname -n && pwd` round-trip via Telegram. Apply on Air + mercury2 next time their gateways are touched.
- [x] **1.3.b** **Chat-reply silent failure (`tools.profile=coding` bug)** — *fixed 2026-05-09 on Pro.* Default `coding` profile bundles `image_gen`+`web_search` which require reasoning≥low; auto-reply path runs at `minimal` → every incoming msg dies with HTTP 400 and is not relayed. Fix: `openclaw config set tools.profile messaging`. Now baked into [`scripts/install_openclaw_instance.sh`](./scripts/install_openclaw_instance.sh). Decision tree for the 3 most common "bot doesn't reply" causes is in [`runbook.md`](./runbook.md). Apply on Air + mercury2 next time their gateways are touched.
- [ ] **1.4** Finalize `config/agent-prompt.md` — SuperCare/provider-admin handling was tightened 2026-06-12 (redact DOB/customer IDs in Telegram, do not reply to mailer-daemon, allow `done` for no-reply admin notices). Still open: answer the 3 placeholders: home address, payment posture, 2–3 sample-tone emails. ⏱ 10 min
- [ ] **1.5** Brando: create private Telegram channel `openclaw-ops`, add bot as admin, send channel ID to Claude. ⏱ 2 min
- [ ] **1.6** **THE PROOF POINT** — triage the current unread SuperCare thread from `amanadero@supercare.com` entirely from Telegram, no Gmail web UI. Exact steps: [`runbook.md` "Phase 1.6 SuperCare E2E proof point"](./runbook.md#phase-16-supercare-e2e-proof-point). ⏱ 10 min

## Phase 1 prereqs / quick TCC + watcher hygiene (do alongside)

- [ ] **TCC.1** Add Homebrew node binaries to **System Settings → Privacy & Security → Full Disk Access** (both `~/homebrew/bin/node` and `~/homebrew/Cellar/node/<ver>/bin/node`). See `MASTER_PLAN.md` §A.0.5.
- [ ] **TCC.2** Run `scripts/pre-grant-tcc-automation.sh` to batch-trigger Automation prompts (Mail, Outlook, Calendar, Reminders, Notes, Messages, Slack, Discord, etc.). Click Allow on each — they're then permanent.
- [ ] **WATCH.1** Install the self-healing watcher (`scripts/openclaw-health-watcher.sh`) via launchd on each host so bot liveness self-recovers from stuck-session / stale-plugin-cache failures. Install plist template inline at the bottom of the script.

## Phase 2 — idempotency + ops (Air, before replicating)

- [ ] **2.1** Implement Gmail label idempotency: `claw-claimed-by-${HOSTNAME}` → `triaged-by-claw`, 5-min stale-claim TTL. ⏱ 1 hr
- [ ] **2.2** Heartbeat via `openclaw cron add` — every 15 min `[host] alive @ <ts>` to `openclaw-ops`. Lifecycle hooks for STARTING / RECOVERED. SILENT >30 min watcher. ⏱ 20 min
- [x] **2.3** Rate limit — *skipped per Brando 2026-05-08* (prefers throughput). Circuit-breaker primitive preserved. ⏱ 0 min

## Phase 3 — replicate to MacBook Pro

- [x] **3.1** Brando: create second `@BotFather` bot for the Pro — done 2026-05-09: `@ultimate_brando9_pro_macbook_bot` (display name `ultimate_brando9_pro_mac_book_bot`; @handle has no underscore between mac/book). Token in `~/keys/openclaw_telegram_bot_token.txt` on Pro. Not yet added to `openclaw-ops` channel.
- [ ] **3.2** Decide access path: SSH config OR Brando runs install script in Pro's terminal himself. ⏱ 1 min
- [ ] **3.3** Per-host prereqs: `codex login`, `brew install node@24 gogcli`. ⏱ 10 min
- [ ] **3.4** scp gogcli auth from Air → Pro; verify with `gog gmail list`. ⏱ 2 min
- [~] **3.5** Run `scripts/install_openclaw_instance.sh` on Pro — partial: install ran 2026-04-26 with the Air token; on 2026-05-09 the Pro token replaced it via manual swap + `openclaw config set tools.profile messaging` + `openclaw gateway restart`. Re-running the (now updated) install script would normalize state.
- [x] **3.6** Pair Pro's bot via Telegram + `openclaw pairing approve` — done 2026-05-09: code `SVND4BDH` approved (channel-scoped pairing carried over after token swap). Bot now replies in `@ultimate_brando9_pro_macbook_bot` chat.
- [ ] **3.7** Verify Pro joins heartbeat + idempotency dance. ⏱ 10 min

## Phase 4 — replicate to mercury2 (Linux, different recipe)

- [x] **4.1** ssh mercury2 works (verified 2026-05-09; auto-resolved when run from on-mercury2 itself; from peer SNAP nodes it works via Kerberos keytab).
- [x] **4.2** Linux install path: `/dfs/scratch0/<user>/openclaw` + `~/openclaw` symlink + `~/.openclaw` (LFS, per-host) + tmux respawn wrapper + `@reboot` cron + 5-min health-watcher cron. Codified in `scripts/install_openclaw_instance_linux.sh` (2026-05-09). Verified end-to-end: hostname/pwd/whoami via agent, `clauded --version`, `codex --version`, and ssh-into-skampere1+nvidia-smi all return correctly through the local agent path.
- [x] **4.3 (partial)** mercury2 bot created (`@ubrando_mercury2_bot`); token at `~/keys/openclaw_telegram_bot_token.txt` (mode 600); `codex login` already done. **Still TODO:** Brando manually `/start`s the bot in Telegram + (optional) scp gogcli auth from instance #1.
- [x] **4.4** SNAP-specific hardening complete: `krenew` cron pre-existed, `@reboot` cron added (relaunches `openclaw-gateway` tmux after waiting for DFS + krenew), 5-min cron runs cross-platform `openclaw-health-watcher.sh`. Logrotate not yet wired (gateway.log will grow; revisit if it exceeds ~100MB).

### Phase 4 gotchas worth carrying forward

- **`--auth-choice openai-codex` is interactive-only.** `openclaw onboard --non-interactive --accept-risk --auth-choice openai-codex` errors with "requires interactive mode" because the OpenAI Codex provider plugin doesn't implement non-interactive setup. The `codex` choice does succeed but doesn't write the auth-profile that downstream `agents.defaults.model = openai/gpt-5.5` then needs (smoke test fails with "No API key found for provider openai" / "Failed to extract accountId from token" — the codex CLI auth file at `~/.codex/auth.json` has all four token fields populated under `auth_mode: chatgpt`, but the OpenClaw codex plugin can't bootstrap from it under the current code path on Linux).
- **Workaround used by `install_openclaw_instance_linux.sh`:** pin `agents.defaults.model.primary = anthropic/claude-haiku-4-5` and inject `ANTHROPIC_API_KEY` via `env.vars` from `~/keys/anthropic_api_key.txt`. Reliable, but uses paid Anthropic API rather than free Codex Pro inference.
- **Fix-forward:** when the codex plugin lands a non-interactive `auth login` (or once we figure out the right manual auth-profiles.json shape for `chatgptAuthTokens` profiles), flip the default model back to `codex/gpt-5.5` to use the subscription. Tracking: filed under "Hygiene / upstream issues" below.
- **`pkill -f openclaw` is dangerous in interactive sessions.** It matches any shell whose command line *contains* the string "openclaw" — including the bash that's currently running the install script if you're interactive. The Linux installer + watcher use `pkill -f 'openclaw gateway run'` (more specific) instead.
- **Don't share a Telegram token across hosts.** Long-polling collisions cause `HTTP 409` conflicts and drop messages — per `concepts.md` Q1. Each host needs its own `@BotFather` bot.

## Phase 5 — 7-day soak (Definition of Done)

- [ ] All 3 instances heartbeat every 15 min, auto-restart within 1 min after kill, zero double-processing, zero false-positive sends.
- [ ] Brando triages **≥10 real admin emails** entirely from Telegram (no Gmail web UI).
- [ ] Subjective end-of-week check-in: "did this actually reduce friction?"

## Phase 6 — standing-order rollout (post-soak, one at a time)

| Sub-phase | Standing order | Blocking on |
|---|---|---|
| 6.1 | WhatsApp voice-draft (`whatsapp_voice_draft.md`) | Baileys upstream stable |
| 6.2 | Stack Exchange `/ask` (`stackexchange_proofassistants_post.md`) | Playwright skill + persisted SE login |
| 6.3 | Grant applications (`grant_applications.md`) | Bio + project library bootstrap (see open setup questions) |
| 6.4 | SBSBZ (FB events + IG + mailing list + Drive→social) | FB Page admin token + IG account linkage |
| 6.5 | Stanford AI for Lean announcements (`lean_ai_club.md`) | aiforlean.org list + Discord/Slack ID + Fred/Henry/Eric emails |
| 6.6 | Experiment dispatch (`experiment_dispatch.md`) | mercury2 install (Phase 4) complete |
| 6.7 | Paper announcements (`paper_announcements.md`) | LinkedIn API access OR Playwright; X paid tier OR Playwright |
| 6.8 | Travel search (`travel_search.md`) | Brando home-airport prefs + price ceilings; first test case = McAllen Jun 13–21 2026 |

## Open setup questions Brando needs to answer (load-bearing for Phase 6)

- [ ] **Q5** SBSBZ acronym — what do the 5 letters stand for? (Confirmed: bachata + zouk, no salsa.)
- [ ] **Q6** SBSBZ posting permissions — does Brando have admin access to FB Page / IG / mailing list?
- [ ] **Q7** Stanford AI for Lean — official mailing-list address? Discord/Slack? Where do meeting announcements go today?
- [ ] **Q8** Grant-detection seed list — 5–10 grant programs Brando is currently watching.
- [ ] **Q9** Bio + project library bootstrap — Brando provides 1 successful past application (e.g. GRFP) so OpenClaw extracts bio paragraphs at 4 lengths + project summaries. *(Note: 2026-05-08 design pivoted to website + GitHub as truth, not flat config files; see `MASTER_PLAN.md` §4.3 + `grant_applications.md`.)*
- [ ] **Q10** LinkedIn / X credentials posture — Playwright-with-persisted-login OK, or pursue API access?
- [ ] **Q11** Drive → social folder convention — confirmed `Drive/OpenClaw/social-queue/<event-name>/`?
- [ ] **Q12** iMessage / SMS scope — needed at all? (Default: defer indefinitely.)
- [ ] **lean_ai_club Monthly workhackathon nudge** — Fred / Henry B / Eric Pineda emails; Lean AI Discord server name + leadership channel.
- [ ] **bots.yaml registry** (chatops.md) — when does this materialize? Currently waiting on conjecture-prover infra answers.

## Big follow-ups proposed but not yet built

- [ ] **Connection Instructions Appendix G** — web-researched 2026-current OAuth flows / API tiers / fallbacks for X / IG / FB / LinkedIn / Outlook (Stanford email / Microsoft Graph) / SuperCare. ~400 new lines. *Q2 from Brando 2026-05-08 — biggest gap.*
- [ ] **`coding_dispatch.md` standing order** — extend `experiment_dispatch.md` for general "update agents-config repo / brandomiranda blog" coding tasks via `claude --headless` or `codex --full-auto`. ~80 lines.
- [ ] **CI workflow** — `.github/workflows/openclaw-lint.yml` for markdown/YAML lint. *(Optional; "CI checks unavailable" message Brando saw is just because no workflow exists yet — not a gh-auth issue.)*
- [ ] **Outlook notification silence** — Brando does the 30-second System Settings fix when convenient. (See `MASTER_PLAN.md` Appendix F.2.)

## Hygiene (do alongside, not blocking)

- [ ] **H.1** Rotate Telegram bot token (current Air token was pasted in a Claude Code chat log).
- [ ] **H.2** Move secrets out of `~/.openclaw/openclaw.json` to SecretRef form (env-var indirection via plist wrapper).
- [ ] **H.3** File upstream OpenClaw issues for the bugs we hit (onboard --help empty, codex harness "not registered", sendMessage HttpError, paste-token UI consumes piped stdin).

## Quick personal TODOs (not OpenClaw-blocking)

- [ ] **Outlook notification silence** — System Settings → Notifications → Outlook → uncheck Allow notifications (or just sounds). 30-second fix.
