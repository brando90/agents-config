# OpenClaw Setup Tutorial — Codex Pro / Claude Pro on Your Own Machines

**TLDR:** Reproducible recipe to stand up a self-hosted OpenClaw 2026.4.24 instance backed by your existing Codex Pro CLI auth (so model calls don't hit API billing), with Telegram as the chat channel. Verified end-to-end on macOS (MacBook Air, Apple Silicon, Node 25 via Homebrew) on 2026-04-26. Same recipe is meant to repeat on Mac Pro and SNAP `mercury2`. The full multi-instance plan is in [`cc_prompt.md`](./cc_prompt.md).

> **Prerequisite (one-time, per machine):** `codex login` against your ChatGPT/Codex Pro account. Verify with `cat ~/.codex/auth.json | grep chatgpt_plan_type` — should show `"chatgpt_plan_type": "pro"`. If it doesn't, the rest of this tutorial will silently fall back to API-key billing (or just fail).

---

## 1. Install (~30 s)

macOS (Homebrew Node) needs an `~/.npmrc` cafile entry first, otherwise OpenClaw's plugin loader can't `npm install` its bundled deps:

```bash
# macOS only — Linux's system npm usually doesn't need this
test -f ~/.npmrc || echo "cafile=/etc/ssl/cert.pem" > ~/.npmrc

# Install OpenClaw globally
npm install -g openclaw@latest
openclaw --version    # expect: OpenClaw 2026.4.24 (cbcfdf6) or newer
```

If you skipped the npmrc step and later see `UNABLE_TO_GET_ISSUER_CERT_LOCALLY` while OpenClaw stages plugins, add the cafile line, then `rm -rf ~/.openclaw/plugin-runtime-deps` and retry whatever you ran.

## 2. Onboarding — must be in a real Terminal (~1 min)

The next command is **interactive** and needs a TTY. Run it in Terminal.app (or iTerm), not piped from a script and not from inside a parent Claude Code / Codex agent session (subprocess deadlocks on `~/.claude/sessions` / `~/.codex/auth.json` locks):

```bash
openclaw onboard
```

Answer the prompts:

- **Where will the Gateway run?** → `Local (this machine)`
- **Auth choice** → `Codex (ChatGPT/OpenAI)` (it auto-detects your `~/.codex/auth.json` from `codex login`)
- **Default model** → accept `openai/gpt-5.5` (this routes through the codex harness, billed against your Pro plan)
- **Daemon install** → yes (installs `~/Library/LaunchAgents/ai.openclaw.gateway.plist` on macOS / a systemd-user unit on Linux; gateway starts on login)

After onboarding, `~/.openclaw/openclaw.json` should look like:

```json
{
  "agents": {
    "defaults": {
      "model": { "primary": "openai/gpt-5.5" },
      "embeddedHarness": { "runtime": "codex" }
    }
  },
  "plugins": { "entries": { "codex": { "enabled": true } } },
  "gateway": { "mode": "local", "bind": "loopback", "auth": { "mode": "token" } }
}
```

The two keys that matter for "use my Pro subscription, not API tokens" are `embeddedHarness.runtime: "codex"` + `model.primary: "openai/gpt-5.5"`. If onboarding picked a different model, fix it:

```bash
openclaw config set agents.defaults.model.primary openai/gpt-5.5
openclaw config set agents.defaults.embeddedHarness.runtime codex
openclaw gateway restart
```

## 3. Smoke test (~5 s)

```bash
openclaw infer model run --gateway --prompt "say only the word PONG"
```

Expected:

```
model.run via gateway
provider: openai
model: gpt-5.5
outputs: 1
PONG
```

If you see `Requested agent harness "codex" is not registered and PI fallback is disabled` → onboarding didn't take; re-run step 2 in a real Terminal. If you see `gateway closed (1006/1000)` → `openclaw gateway restart && sleep 5` and retry.

Sanity-check that you're actually on Codex Pro auth, not API key billing:

```bash
grep chatgpt_plan_type ~/.codex/auth.json   # → "chatgpt_plan_type": "pro"
openclaw config get agents.defaults.embeddedHarness.runtime   # → "codex"
```

## 4. Telegram channel (~5 min, requires phone)

Get a bot token:

1. Open Telegram → message [`@BotFather`](https://t.me/BotFather)
2. `/newbot` → name it (e.g. `your_handle_openclaw`) → copy the token it gives you (`123456:ABC-...`)
3. (Optional) `/newchannel` to create a private `openclaw-ops` channel for heartbeats; add the bot as admin

Wire it into OpenClaw:

```bash
mkdir -p ~/keys && chmod 700 ~/keys
echo 'PASTE_TOKEN_HERE' > ~/keys/openclaw_telegram_bot_token.txt
chmod 600 ~/keys/openclaw_telegram_bot_token.txt

openclaw channels add --channel telegram --token "$(cat ~/keys/openclaw_telegram_bot_token.txt)"
openclaw gateway restart
sleep 4
openclaw channels status   # → "Telegram default: enabled, configured, running"
```

First contact (the bot can't DM you until you DM it):

1. In Telegram, search for your bot's `@handle` and tap `/start`, send any message
2. The bot replies with a pairing code (`KBK4LMYU`-style) and the exact approval command
3. Run that approval command in your terminal:
   ```bash
   openclaw pairing approve telegram <CODE>
   ```
4. DM the bot again — this time it replies as the agent (Codex Pro / GPT-5.5)

## 5. Gmail channel (in progress)

```bash
openclaw channels add --channel google
```

This opens a browser → Google OAuth → consent screen (scopes: `gmail.readonly` + `gmail.send` + `gmail.modify` for labels). Token lands in `~/.openclaw/...` (per-host).

> **Multi-instance:** the Gmail token is per-Google-account, so generate it once on instance #1, then `scp` the token file to instance #2 and #3 to avoid re-OAuth'ing three times. Keep the audit trail clean.

(More wiring — admin-sender filter, triage system prompt, idempotency labels — comes after Gmail is connected. See [`cc_prompt.md`](./cc_prompt.md) §Phases 2–4.)

## 6. Multi-instance deployment

Brando runs OpenClaw on **three** boxes: this MacBook Air, a MacBook Pro, and SNAP `mercury2` (Linux GPU node). The shared design (forced by 3 readers on one inbox + the 4-device WhatsApp cap):

- **Channel:** Telegram (mandatory — WhatsApp's 4-device cap is exceeded)
- **Heartbeat:** posts to a private Telegram channel `openclaw-ops`, every 15 min
- **Idempotency:** Gmail labels `claw-claimed-by-<host>` → `triaged-by-claw`, with a 5-min stale-claim TTL (tightened from spec's 30 min because 3 readers race more)
- **Per-host secrets:** `~/keys/openclaw_telegram_bot_token.txt`, `~/keys/gmail_openclaw_token.json` — generate once, `scp` to the other hosts
- **Per-host auth:** run `codex login` separately on each (don't copy `~/.codex/auth.json` between hosts — refresh tokens rotate)
- **Daemon:** `openclaw onboard --install-daemon` does launchd on macOS; for `mercury2` use the SNAP tmux + watchdog + cron pattern from [`~/agents-config/machine/snap.md`](../../machine/snap.md) — no systemd-user there

## Gotchas (real ones, learned the hard way)

| Symptom | Cause | Fix |
|---|---|---|
| `npm` SSL: `UNABLE_TO_GET_ISSUER_CERT_LOCALLY` | Homebrew Node has no CA bundle | `echo cafile=/etc/ssl/cert.pem > ~/.npmrc` |
| `Error: No provider plugins found. Install one via 'openclaw plugins install'` | Stale plugin cache from a partial install | `rm -rf ~/.openclaw/plugin-runtime-deps` then re-run any openclaw command |
| `models auth login requires an interactive TTY` | Auth wizards need a real terminal | Stop driving them from a non-TTY shell; run in Terminal.app |
| `Requested agent harness "codex" is not registered and PI fallback is disabled` | `embeddedHarness.runtime` set but plugin didn't fully register (often: onboarding skipped) | Re-run `openclaw onboard` in a real Terminal |
| `claude -p` subprocess hangs forever (with claude-cli harness) | OpenClaw spawns `claude -p ...` which deadlocks on `~/.claude/sessions` lockfiles when called from inside another claude session | Don't drive OpenClaw from inside Claude Code; use Codex harness instead, or use a separate terminal |
| Telegram `Network request for 'sendMessage' failed!` despite working `curl` | Gateway lacks `NODE_EXTRA_CA_CERTS` in its launchd env | Edit `~/Library/LaunchAgents/ai.openclaw.gateway.plist` → add `NODE_EXTRA_CA_CERTS=/etc/ssl/cert.pem` to `EnvironmentVariables`, `openclaw gateway restart` |
| Bot won't DM you proactively | Telegram bots cannot initiate; user must `/start` first | Open chat, hit `/start`, then approve the pairing code OpenClaw prints |
| Spec says `https://github.com/steipete/claw-bot` | Wrong / outdated URL | Real repo is `https://github.com/openclaw/openclaw` (Steipete contributes, doesn't own) |

## What not to do

- **Don't** sign up at clawhub.ai for the smoke test or the basic triage feature — the 63 stock plugins (including `google`, `telegram`, `whatsapp`) are already bundled with the npm package. ClawHub is the optional marketplace for *third-party* skills.
- **Don't** put `gateway.auth.token`, `channels.telegram.botToken`, or any other secret in agents-config — they live in `~/keys/` (mode 600) per machine, scp'd between hosts.
- **Don't** copy `~/.codex/auth.json` between machines as a shortcut — the refresh token will rotate and break whichever host pulled it last.

## References

- Spec & plan: [`cc_prompt.md`](./cc_prompt.md) (the 6-phase deployment plan, dual-instance idempotency strategy, definition of done)
- OpenClaw repo: https://github.com/openclaw/openclaw
- OpenClaw docs: https://docs.openclaw.ai
- Helpful YouTube walkthrough (Brando found this useful): https://www.youtube.com/watch?v=st534T7-mdE
- @BotFather (Telegram bot creation): https://t.me/BotFather
- SNAP node setup playbook: [`~/agents-config/machine/snap.md`](../../machine/snap.md)
- macOS dev gotchas: [`~/agents-config/machine/mac.md`](../../machine/mac.md)
