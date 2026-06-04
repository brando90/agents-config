# OpenClaw Runbook — Per-Machine Bot Lifecycle

**TLDR:** Grep-friendly playbook for recurring per-machine bot ops: setting up a new bot, restarting a stuck one, swapping tokens, and triaging "bot won't reply." Distilled from the 2026-05-09 MacBook Pro setup session. The full design is in [`MASTER_PLAN.md`](./MASTER_PLAN.md); the per-machine bot rationale is in [`concepts.md` Q1](./concepts.md); fleet-level ops are in [`chatops.md`](./chatops.md). Current open items live in [`TODO.md`](./TODO.md).

---

## When the bot doesn't reply (90-second decision tree)

Three causes in order of frequency observed on Pro 2026-05-09:

### 1. Gateway is polling the wrong bot

The token in `~/keys/openclaw_telegram_bot_token.txt` resolves to a different bot than the one you're DMing. Common after `scp`'ing keys between hosts and forgetting to swap.

```bash
TOKEN=$(cat ~/keys/openclaw_telegram_bot_token.txt)
curl -s "https://api.telegram.org/bot${TOKEN}/getMe" \
  | python3 -c "import json,sys; print('polling:', json.load(sys.stdin)['result']['username'])"
```

Compare against the bot's `@handle` in your Telegram chat header. If they differ → use **Swap bot token** below.

> Note: BotFather lets the display name (e.g. `ultimate_brando9_pro_mac_book_bot`) and the `@handle` (e.g. `@ultimate_brando9_pro_macbook_bot`) differ. The chat header shows the display name; only `getMe.username` is canonical.

### 2. User is unpaired (first contact)

OpenClaw's `telegram-auto-reply` module creates a pending pairing on first DM. The agent won't reply until you approve.

```bash
openclaw pairing list --channel telegram          # see pending requests
openclaw pairing approve --channel telegram <CODE>
```

(Pairings are channel-scoped, not bot-scoped — so a pairing approved against the Air bot also applies after a token swap to the Pro bot for the same Telegram user.)

### 3. `tools.profile` is set to `coding` (silent failure)

If `tools.profile = "coding"`, **every** incoming message hits an OpenAI API HTTP 400 and fails silently:

```
The following tools cannot be used with reasoning.effort 'minimal': image_gen, web_search.
```

Cause: the `coding` profile bundles `image_gen` + `web_search` tools that require reasoning ≥ `low`, but the Telegram auto-reply path invokes the agent at `minimal`. Result: `surface_error` in logs, nothing relayed back to the user.

```bash
openclaw config get tools                        # expect: {"profile":"messaging"}
# if it's "coding":
openclaw config set tools.profile messaging && openclaw gateway restart
sleep 20 && openclaw channels status | grep -i telegram   # wait for connected
```

Verify the fix in logs (should be empty):

```bash
openclaw logs | grep -E "image_gen.*web_search|reasoning.effort 'minimal'" | tail -5
```

The install script (`scripts/install_openclaw_instance.sh`) now applies this automatically; this section exists to recognize the failure mode on machines installed before that change landed.

### Still nothing?

Tail the live log while pinging the bot from your phone:

```bash
openclaw logs | tail -F \
  | grep -E --line-buffered "telegram-auto-reply|chatId|surface_error|embedded_run_failover"
```

Or push a test reply yourself (no human required):

```bash
openclaw agent --channel telegram --deliver \
  -m "say only: agent is alive" -t <YOUR_TELEGRAM_USER_ID> --timeout 90
```

(Find your Telegram user ID with `openclaw logs | grep -oE 'chatId.{0,20}' | head -1` after sending one DM.)

---

## Restart the gateway

```bash
openclaw gateway restart
# Telegram channel takes ~12-20s to reconnect after launchd bootstrap.
sleep 20 && openclaw channels status | grep -i telegram
```

Expected end state: `enabled, configured, running, connected, mode:polling`.

If it stays `disconnected` past 60s, check `openclaw logs | tail -30` for `gateway/channels/telegram` warnings.

---

## Discord setup and testing

Use this when the Discord bot token has already been copied to `~/keys/` on the target machine. Never paste the token into chat, shell history, or git.

```bash
# 1. Normalize the expected filenames and permissions.
chmod 600 ~/keys/openclaw_discord_bot_token.txt
if [ ! -e ~/keys/discord_bot_token.txt ]; then
  ln ~/keys/openclaw_discord_bot_token.txt ~/keys/discord_bot_token.txt
fi
chmod 600 ~/keys/discord_bot_token.txt ~/keys/openclaw_discord_bot_token.txt

# 2. Point OpenClaw at the token file via SecretRef, not plaintext config.
openclaw config set secrets.providers.discord_bot \
  --provider-source file \
  --provider-path "$HOME/keys/openclaw_discord_bot_token.txt" \
  --provider-mode singleValue
openclaw config set channels.discord.token \
  --ref-provider discord_bot --ref-source file --ref-id value
openclaw config set channels.discord.enabled true --strict-json
openclaw config set plugins.entries.discord.enabled true --strict-json
openclaw config validate
```

If `openclaw config validate` warns `plugin not installed: discord`, install the Discord plugin. Match the plugin to the local OpenClaw version unless you are intentionally upgrading OpenClaw:

```bash
# mercury2 was verified on OpenClaw 2026.5.7 with this exact plugin version.
openclaw plugins install @openclaw/discord@2026.5.7

# On newer hosts, this is usually fine:
openclaw plugins install @openclaw/discord
```

Restart or signal the gateway:

```bash
# Service-managed hosts:
openclaw gateway restart

# mercury2 custom respawn-wrapper host if the service reports disabled:
# Kill the inner gateway; the respawn wrapper relaunches it within a few seconds.
pkill -f 'openclaw gateway run'
sleep 20
```

Expected smoke status:

```bash
openclaw channels status --deep | grep -E 'Discord|Telegram'
# - Discord default: enabled, configured, running, connected, bot:@ultimate_brando9_bot, token:config
```

Functional send test requires a Discord target. Prefer a private test channel first.

```bash
# Find candidate channel IDs and user IDs.
openclaw directory groups list --channel discord
openclaw directory peers list --channel discord --query "<name>"
openclaw channels resolve --channel discord --kind group "<server-or-channel-name>"

# Dry-run, then send a visible test message to a channel.
openclaw message send --channel discord --dry-run \
  -t channel:<CHANNEL_ID> \
  -m "OpenClaw Discord smoke test from $(hostname) at $(date +%Y-%m-%dT%H:%M:%S%z)."

openclaw message send --channel discord \
  -t channel:<CHANNEL_ID> \
  -m "OpenClaw Discord smoke test from $(hostname) at $(date +%Y-%m-%dT%H:%M:%S%z)."

# DM form, if the bot shares a server with the user and DMs are allowed.
openclaw message send --channel discord \
  -t user:<USER_ID> \
  -m "OpenClaw Discord DM smoke test from $(hostname) at $(date +%Y-%m-%dT%H:%M:%S%z)."
```

Full human-in-the-loop test: DM the OpenClaw Telegram bot with a request like `send "OpenClaw smoke test" to Discord channel <channel name>`, confirm the preview with `post`, and verify the message appears in Discord. This exercises Telegram approval plus Discord execution instead of only the raw Discord send path.

Current verified state, 2026-06-04:

- Mac local OpenClaw: Discord connected as `@ultimate_brando9_bot`; token file is `~/keys/openclaw_discord_bot_token.txt` mode `600`; config uses `channels.discord.token` SecretRef.
- `mercury2.stanford.edu`: `~/keys` is `/dfs/scratch0/brando9/keys`; `@openclaw/discord@2026.5.7` is installed; Discord and Telegram both report `running, connected`.
- Status may show `intents:content=limited`. If inbound ordinary message content does not work, enable **Message Content Intent** in the Discord Developer Portal for bot ID `1498169663278813254` and ensure the bot is invited to the target server/channel.

---

## Swap bot token (repoint gateway to a different bot, or rotate)

```bash
# 1. Verify the new token resolves to the expected bot BEFORE overwriting
NEW_TOKEN='TOKEN_HERE'
curl -s "https://api.telegram.org/bot${NEW_TOKEN}/getMe" \
  | python3 -c "import json,sys; print('username:', json.load(sys.stdin)['result']['username'])"

# 2. Overwrite the token file
printf '%s\n' "${NEW_TOKEN}" > ~/keys/openclaw_telegram_bot_token.txt
chmod 600 ~/keys/openclaw_telegram_bot_token.txt

# 3. Restart so the channel re-binds
openclaw gateway restart && sleep 20
openclaw channels status | grep -i telegram

# 4. The new bot won't reply until you /start it (Telegram bots can't initiate)
#    AND approve the pairing it generates. In Telegram: search the new bot's
#    @handle, send /start, then:
openclaw pairing list --channel telegram
openclaw pairing approve --channel telegram <CODE>
```

---

## Add a new per-machine bot from scratch

Per-machine bot is the canonical pattern (see [`concepts.md` Q1](./concepts.md): one shared bot across N hosts causes constant `getUpdates` 409 conflicts).

```bash
# 1. In Telegram, DM @BotFather:
#      /newbot
#      <Display Name>            (e.g. ultimate_brando9_pro_mac_book_bot)
#      <handle>_bot              (e.g. ultimate_brando9_pro_macbook_bot)
#    Copy the token BotFather sends.

# 2. On the target machine, drop the token in:
printf '%s\n' 'TOKEN_FROM_BOTFATHER' > ~/keys/openclaw_telegram_bot_token.txt
chmod 600 ~/keys/openclaw_telegram_bot_token.txt

# 3. Install (idempotent — safe to re-run on a host that already has openclaw).
#    The script bakes in the messaging-profile fix and the pairing-CLI flag fix.
bash ~/agents-config/experiments/01_self_hosted_openclaw/scripts/install_openclaw_instance.sh

# 4. In Telegram, /start the new bot, then approve its pairing:
openclaw pairing list --channel telegram
openclaw pairing approve --channel telegram <CODE>

# 5. DM the bot — it should reply via the agent (Codex Pro / GPT-5.5).
```

---

## Diagnostic commands cheat sheet

Telegram-side (uses the on-disk token):

```bash
TOKEN=$(cat ~/keys/openclaw_telegram_bot_token.txt)

# which bot does this token belong to?
curl -s "https://api.telegram.org/bot${TOKEN}/getMe"

# is there a stale webhook intercepting updates? (must be empty for polling)
curl -s "https://api.telegram.org/bot${TOKEN}/getWebhookInfo"

# 409 Conflict here = GOOD: OpenClaw is the polling client, no second poller.
# pending_update_count > 0 = OpenClaw isn't consuming for some reason.
curl -s "https://api.telegram.org/bot${TOKEN}/getUpdates"

# push a message FROM the bot to a known user (proves bot identity / reachability)
curl -s "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  --data-urlencode "chat_id=<USER_ID>" \
  --data-urlencode "text=ping"
```

OpenClaw-side:

```bash
openclaw channels status                            # connected/disconnected
openclaw logs | tail -50                            # recent gateway activity
openclaw pairing list --channel telegram            # pending pairings
openclaw doctor                                     # general health
openclaw agents list                                # agent registry + routing
openclaw config get tools                           # MUST be {"profile":"messaging"}
openclaw infer model run --gateway --prompt PONG    # end-to-end model smoke test
openclaw exec-policy show                           # shell exec policy (effective)
```

---

## Shell exec — local patch required (broken upstream)

**Status:** Working as of 2026-05-09 with a 1-line patch to `node_modules/openclaw`. Verified end-to-end by running `date +%s && uname -n && pwd` via the agent and getting real exec output back through Telegram. Upstream is broken (see "How it was broken" below).

**The patch (`/usr/local/lib/node_modules/openclaw/dist/extensions/codex/harness.js`, ~line 21):**

```diff
       runAttempt: async (params) => {
           const { runCodexAppServerAttempt } = await import("./run-attempt-DHkL03VS.js");
-          return runCodexAppServerAttempt(params, { pluginConfig: options?.pluginConfig });
+          return runCodexAppServerAttempt(params, { pluginConfig: options?.pluginConfig, nativeHookRelay: { enabled: false } });
       },
```

This makes `options.nativeHookRelay.enabled === false`, which causes:

1. `createCodexNativeHookRelay` to early-return (no relay registration in the gateway's in-memory map)
2. `nativeHookRelayConfig = buildCodexNativeHookRelayDisabledConfig()` to be sent to codex (`features.codex_hooks: false` + cleared PreToolUse/PostToolUse/PermissionRequest arrays)

Codex then falls back to its own sandbox/approval flow, which is already `yolo` + `danger-full-access` + `approvalPolicy: never` (default for `policyMode === "yolo"`, plus your `~/.codex/config.toml` explicitly sets `approval_policy = "never"` and `sandbox_mode = "danger-full-access"`). Tool calls execute directly.

**Apply automatically:** [`scripts/install_openclaw_instance.sh`](./scripts/install_openclaw_instance.sh) detects the unpatched state and applies the patch (with backup at `harness.js.bak.preopenclawpatch`).

**Restore upstream behavior** (re-block shell exec):

```bash
cp /usr/local/lib/node_modules/openclaw/dist/extensions/codex/harness.js.bak.preopenclawpatch \
   /usr/local/lib/node_modules/openclaw/dist/extensions/codex/harness.js
openclaw gateway restart
```

**Re-apply after upgrade:** Any `npm install -g openclaw@latest` overwrites the patch. Re-run the install script, which is idempotent and re-applies the patch.

**How it was broken.** Codex's `PreToolUse` hook is implemented via a relay subprocess (`openclaw hooks relay --provider codex --relay-id <UUID> --event pre_tool_use`) that calls back to the gateway over WebSocket. The gateway's `invokeNativeHookRelay` looks up `<UUID>` in an in-memory `relays` Map and throws `native hook relay not found` if missing. The relay IS registered at run start by `createCodexNativeHookRelay` → `registerNativeHookRelay`, but is unregistered in a `finally` block of `runCodexAppServerAttempt`. By the time codex's tool-call subprocess actually fires the relay command, the registration is gone.

Smoking gun in gateway logs:

```
gateway/ws  ⇄ res ✗ nativeHook.invoke 1ms errorCode=INVALID_REQUEST errorMessage=native hook relay not found
```

The same `errorMessage=native hook relay not found` repeats on every shell tool call until the patch lands. Reachability isn't the problem — the gateway sees the request fine.

Same finding will apply to Air + mercury2 once they enable shell exec; install script applies the patch on every host.
