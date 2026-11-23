# Eight Sleep Antigravity plugin

**Doc link:** <https://github.com/brando90/agents-config/blob/main/plugins/eight-sleep/antigravity/README.md>

Date: 11-23-2026

**TLDR:** Antigravity plugin and direct Model Context Protocol (MCP) configuration for Eight Sleep's hosted Streamable HTTP server (`https://public-api.8slp.net/mcp`), defaulting to read-only usage rules (`read_sleep`, `read_device`).

## Install (choose one method, not both)

Antigravity namespaces plugin MCP servers as `<plugin-name>_<server-key>` (`eight-sleep_eight-sleep`), so installing both this plugin bundle and the standalone global `eight-sleep` entry registers duplicate Eight Sleep servers. Install **either** one method **or** the other, not both at the same time.

### Option A: Antigravity plugin bundle (recommended for sharing)

```bash
agy plugin validate --strict ~/agents-config/plugins/eight-sleep/antigravity
agy plugin install ~/agents-config/plugins/eight-sleep/antigravity
```

Or update a local checkout first if needed (`git -C ~/agents-config pull --ff-only`) and install from that local directory (`agy` 1.5.15 `plugin install` accepts a local directory or `<plugin>@<marketplace>`, not a GitHub subfolder URL).

### Option B: Direct global MCP entry (`~/.gemini/config/mcp_config.json`)

```bash
agy mcp add --type http eight-sleep https://public-api.8slp.net/mcp
```

This adds `"eight-sleep": {"serverUrl": "https://public-api.8slp.net/mcp"}` (exact match to Eight Sleep's Protected Resource Metadata `resource`, with no trailing slash).

## Sign-in and read-only scopes

Antigravity's `mcp_config.json` schema has no Open Authorization (OAuth) `scopes` field (`oauth` accepts only manual `clientId` and optional `clientSecret`). Enforce read-only access on Eight Sleep's consent screen and via the bundled `rules/AGENTS.md` rule:

1. In the Antigravity App, open **Customizations -> Installed -> MCP Servers -> `eight-sleep_eight-sleep` (Option A) or `eight-sleep` (Option B) -> Authenticate** (or `/mcp` in Antigravity CLI).
2. Sign in with your Eight Sleep account and grant **only** `read_sleep` and `read_device`. Leave **control your device** (`write_device`) unticked.
3. Do not install or use the deprecated Gemini CLI (`gemini`).

## Upstream OAuth allowlist status

As of 11-23-2026:

- `GET https://public-api.8slp.net/v1` and `GET https://public-api.8slp.net/.well-known/oauth-protected-resource/mcp` are healthy (`200`).
- Eight Sleep's authorization server (`https://auth-api.8slp.net`) currently rejects Antigravity's Client Identifier Metadata Document (`https://antigravity.google/oauth/client-metadata.json`) on `/v1/ui/authorize` with an `"Eight - Uh, oh"` error page, and Dynamic Client Registration (`POST https://auth-api.8slp.net/v1/oauth/register`) returns HTTP `400` `invalid_redirect_uri` (`"these redirect_uris are not open to registration"`) for `https://antigravity.google/oauth-callback` and standard Request for Comments (RFC) 8252 loopback URIs (`http://127.0.0.1:...`, `http://localhost:...`).
- If browser **Authenticate** hits that refusal, contact `support@eightsleep.com` to allowlist `https://antigravity.google/oauth/client-metadata.json` and `https://antigravity.google/oauth-callback`.

## Verification

```bash
agy plugin validate --strict ~/agents-config/plugins/eight-sleep/antigravity
python3 ~/agents-config/plugins/eight-sleep/scripts/test_eight_sleep_connector.py --live
```

Once pushed to `main`, `agy plugin validate --strict https://github.com/brando90/agents-config/tree/main/plugins/eight-sleep/antigravity` also validates directly from GitHub.
