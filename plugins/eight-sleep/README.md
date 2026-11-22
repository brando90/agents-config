# Eight Sleep connector for all assistants

Date: 11-22-2026

**TLDR:** Eight Sleep runs a hosted MCP server at `https://public-api.8slp.net/mcp` (OAuth, no API key). Each assistant signs in once with Brando's Eight Sleep account. Request read scopes only (`read_sleep`, `read_device`). Nothing here is signed in yet, and no token or code lives in this repo.

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

The last 7 change things and need `write_device`. With read scopes only, use the first 5 plus `list_alarms`. Rate limit: 60 calls per minute per connection, plus 10 change requests per 5 minutes and 50 per day.

## Assistants and sign-in status (as of 11-22-2026)

| Assistant | How | Status |
| --- | --- | --- |
| Claude Code | plugin in `claude-code/` | not signed in yet |
| Codex | `codex/config.toml.snippet` | not signed in yet |
| Cursor | marketplace plugin or `cursor/mcp.json` | not signed in yet |
| Grok Bot | `grok-bot/README.md` | not signed in yet |
| ChatGPT (and Codex app) | private plugin "Eight Sleep" v0.1.0 already created in Brando's ChatGPT account (per Brando's 11-22-2026 paste from ChatGPT's Plugin Creator): Plugins -> Created by you -> Eight Sleep -> install, sign in. Public listing needs OpenAI's domain-verification token on public-api.8slp.net or 8slp.net, which only Eight Sleep can host | created, not signed in yet, live read unverified |
| Claude apps (claude.ai, desktop) | add the address as a custom connector (Eight Sleep's page names Claude as an example; client-specific steps not confirmed) | not signed in yet |

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

## Safety

- Read scopes only; nothing here changes the Pod. Revoke from **Data Sharing** in the Eight Sleep app or disconnect in the assistant (effective within about 5 minutes, per the Cursor README).
- Never commit a token, code or callback URL. Tokens stay in each client's own store.
