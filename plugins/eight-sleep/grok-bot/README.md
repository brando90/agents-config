# Eight Sleep in Grok Bot

Date: 11-22-2026

Steps (from xAI's "Connect an app" page, https://docs.x.ai/grok-bot/computer-and-apps, read 11-22-2026):

1. Desktop app: open **Connect apps** in the sidebar, scroll to the bottom, pick **Add a custom connector**.
2. Name: `Eight Sleep`. Type: **Remote HTTPS**. Server URL: `https://public-api.8slp.net/mcp`. Leave HTTP headers, Client ID and Client Secret empty (Eight Sleep registers the client itself).
3. Choose **Add plugin**, then **Authenticate**, and finish the Eight Sleep login in the browser (about 10 minutes before the card expires; **Reconnect**/**Reopen** restarts it). On the consent screen allow read access only (sleep, device); do not allow "control your device".
4. "Added" only means installed. The row must say signed in, not "Needs auth".

Alternative from the Cursor README (not confirmed on xAI's page): **Settings -> Plugins**, install **Eight Sleep**, same sign-in. Cursor's README also sets `"placement": "server"` for Grok Bot's hosted path:

```json
{ "mcpServers": { "eight-sleep": { "type": "http", "url": "https://public-api.8slp.net/mcp", "placement": "server" } } }
```

You can also tell the Bot: "Add the MCP server at https://public-api.8slp.net/mcp" (xAI's page says this works).
