# Eight Sleep connector for all assistants

**Doc link:** <https://github.com/brando90/agents-config/blob/main/plugins/eight-sleep/README.md>

Date: 11-22-2026
As of 11-23-2026: added Antigravity (`agy`) plugin bundle (`antigravity/`), fixed the read/write tool counts (`6` read + `6` write), added deterministic/live verification (`scripts/test_eight_sleep_connector.py`), and recorded live Eight Sleep OAuth allowlist status.

**TLDR:** Eight Sleep runs a hosted MCP server at `https://public-api.8slp.net/mcp` (OAuth, no API key). Each assistant signs in once with Brando's Eight Sleep account. Request read scopes only (`read_sleep`, `read_device`). Nothing here is signed in yet, and no token or secret lives in this repo.

## Address and sign-in

- Server: `https://public-api.8slp.net/mcp` (streamable HTTP). Docs: https://public-api.8slp.net/connectors
- Auth: OAuth authorization code with PKCE (S256) and dynamic client registration against `https://auth-api.8slp.net`. No client ID or secret to configure.
- Metadata (checked 11-22-2026): `https://public-api.8slp.net/.well-known/oauth-protected-resource/mcp` lists scopes `read_sleep`, `read_device`, `write_device`.
- Needs an Eight Sleep account and a Pod; alarms and the temperature schedule also need an active membership.

## Scopes

| Scope | Grants | Default here |
| --- | --- | --- |
| `read_sleep` | sleep days and sessions | yes |
| `read_device` | Pod status, temperature settings, alarms | yes |
| `write_device` | change alarms, power, temperature, schedule | **no** (only if Brando says so) |

Where a client lets you set scopes (Codex), set the two read scopes. Elsewhere, untick "control your device" on the consent screen.

## The 12 tools (Cursor plugin README, read 11-22-2026)

- Sleep (3): `get_sleep_days`, `get_sleep_sessions`, `get_sleep_session`
- Pod (2): `get_device_status`, `get_temperature_settings`
- Alarms (4): `list_alarms`, `create_alarm`, `update_alarm`, `delete_alarm`
- Changes (3): `set_pod_power`, `set_temperature`, `update_temperature_schedule`

The `6` write tools (`create_alarm`, `update_alarm`, `delete_alarm`, `set_pod_power`, `set_temperature`, `update_temperature_schedule`) need `write_device`. The `6` read tools (`get_sleep_days`, `get_sleep_sessions`, `get_sleep_session`, `get_device_status`, `get_temperature_settings`, `list_alarms`) work with `read_sleep` and `read_device` only. Rate limit: 60 calls per minute per connection, plus 10 change requests per 5 minutes and 50 per day.

## Assistants and sign-in status (as of 11-23-2026)

| Assistant | How | Status |
| --- | --- | --- |
| Antigravity (`agy`) | plugin in [`antigravity/`](antigravity/README.md) or `agy mcp add --type http eight-sleep https://public-api.8slp.net/mcp` | configured locally (`mcp_config.json`, `agy mcp list` enabled); blocked upstream by Eight Sleep OAuth allowlist as of 11-23-2026 |
| Claude Code | plugin in `claude-code/` | not signed in yet |
| Codex | `codex/config.toml.snippet` | not signed in yet |
| Cursor | marketplace plugin or `cursor/mcp.json` | not signed in yet |
| Grok Bot | `grok-bot/README.md` | not signed in yet |
| ChatGPT (and Codex app) | private plugin "Eight Sleep" v0.1.0 already created in Brando's ChatGPT account (per Brando's 11-22-2026 paste from ChatGPT's Plugin Creator): Plugins -> Created by you -> Eight Sleep -> install, sign in. Public listing needs OpenAI's domain-verification token on public-api.8slp.net or 8slp.net, which only Eight Sleep can host | created, not signed in yet, live read unverified |
| Claude apps (claude.ai, desktop) | add the address as a custom connector (Eight Sleep's page names Claude as an example; client-specific steps not confirmed) | not signed in yet |

## Do assistants need this repo (or Brando's GitHub)?

No. The address and each assistant's own Eight Sleep sign-in are enough for any assistant that speaks remote MCP over HTTP with OAuth. This folder is only a shared copy of the steps and configs (11-22-2026).

## Antigravity (agy)

Docs checked 11-23-2026: https://antigravity.google/docs/mcp.md, https://antigravity.google/docs/build-plugins.md, and `agy plugin validate --strict`. Install **either** the plugin bundle **or** the standalone global MCP entry (not both, to avoid registering duplicate Eight Sleep MCP servers: the plugin namespaces its server as `eight-sleep_eight-sleep` alongside the global `eight-sleep` entry):

```bash
# Option A: install the Antigravity plugin bundle (includes read-only rules/AGENTS.md)
agy plugin validate --strict ~/agents-config/plugins/eight-sleep/antigravity
agy plugin install ~/agents-config/plugins/eight-sleep/antigravity

# Option B: add only the global MCP entry in ~/.gemini/config/mcp_config.json
agy mcp add --type http eight-sleep https://public-api.8slp.net/mcp
```

See [`antigravity/README.md`](antigravity/README.md) for UI sign-in steps (**Customizations -> Installed -> MCP Servers -> `eight-sleep_eight-sleep` (Option A) or `eight-sleep` (Option B) -> Authenticate**) and read-only scope selection (Antigravity's `mcp_config.json` has no OAuth `scopes` key, so untick "control your device" on Eight Sleep's consent screen). Live probes on 11-22-2026 and 11-23-2026 confirmed Eight Sleep's `https://auth-api.8slp.net` currently returns `"Eight - Uh, oh"` on `/v1/ui/authorize` for Antigravity's Client Identifier Metadata Document (`https://antigravity.google/oauth/client-metadata.json`) and HTTP `400 invalid_redirect_uri` on `/v1/oauth/register` for both `https://antigravity.google/oauth-callback` and RFC 8252 loopback URIs (`http://127.0.0.1:...`, `http://localhost:...`). Do not install or use the deprecated Gemini CLI (`gemini`) per Hard Rule 7.

## Claude Code

Docs checked 11-22-2026: https://code.claude.com/docs/en/plugins-reference (manifest at `.claude-plugin/plugin.json`, servers in `.mcp.json` at plugin root), https://code.claude.com/docs/en/mcp (add and login commands). `claude plugin validate` passes on both `claude-code/` and the marketplace (Claude Code 2.1.304).

```bash
git -C ~/agents-config pull --ff-only
claude plugin marketplace add ~/agents-config/plugins/eight-sleep
claude plugin install eight-sleep@brando-eight-sleep
```

Then in Claude Code run `/mcp`, pick `eight-sleep`, sign in, untick "control your device". From a shell: `claude mcp login eight-sleep` (add `--no-browser` over SSH). The server name inside a plugin may show with a plugin prefix in `/mcp`. Without the plugin: `claude mcp add --transport http --scope user eight-sleep https://public-api.8slp.net/mcp`.

## Codex

Docs checked 11-22-2026: https://learn.chatgpt.com/docs/extend/mcp?surface=cli (the old developers.openai.com/codex/mcp redirects there). Config parses in Codex CLI (`codex mcp list` shows it, "Not logged in").

```bash
cat ~/agents-config/plugins/eight-sleep/codex/config.toml.snippet >> ~/.codex/config.toml
codex mcp login eight-sleep --scopes read_sleep,read_device   # add --no-browser without a local browser
```

## Cursor

Docs checked 11-22-2026: https://cursor.com/docs/plugins and https://cursor.com/docs/context/mcp. The Cursor README says: **Cursor Settings -> Plugins**, search **Eight Sleep**, **Install**, complete sign-in; or `/add-plugin eight-sleep`. Cursor's own docs describe the **Customize** sidebar (Install, project or user scope) and say nothing about `/add-plugin` or a "Settings -> Plugins" page, so those two paths are from the README only. The plugin's page on cursor.com/marketplace could not be read (page text not returned).

Fallback that matches the docs: copy `cursor/mcp.json` into `~/.cursor/mcp.json` (all projects) or `.cursor/mcp.json`, then sign in when Cursor prompts. Cursor's `auth.scopes` setting needs a fixed client ID in its docs, so scopes are chosen on the consent screen.

## Grok Bot

See `grok-bot/README.md`. xAI's page (https://docs.x.ai/grok-bot/computer-and-apps) gives the custom connector steps (Connect apps -> Add a custom connector -> Remote HTTPS). It does not mention Settings -> Plugins or an Eight Sleep catalog entry; both come from the Cursor README only.

## Verification

```bash
agy plugin validate --strict ~/agents-config/plugins/eight-sleep/antigravity
python3 ~/agents-config/plugins/eight-sleep/scripts/test_eight_sleep_connector.py --live
```

## Safety

- Read scopes only; nothing here changes the Pod. Revoke from **Data Sharing** in the Eight Sleep app or disconnect in the assistant (effective within about 5 minutes, per the Cursor README).
- Never commit a token, code or callback URL. Tokens stay in each client's own store.
