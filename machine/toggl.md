# Toggl Track for Brando's agents

**Doc link:** <https://github.com/brando90/agents-config/blob/main/machine/toggl.md>

**TLDR:** Toggl is connected to Pipedream's hosted development service. Mac Codex and Claude Code are configured; workspace and current-day reads passed. Other agents, including UB9sc, must verify their own private authentication. Entry creation uses Pipedream's hosted application programming interface (API) proxy because its Toggl MCP catalog currently lacks a create-entry action.

## Verified status (10-28-2026)

- GitHub sign-in reached the existing Pipedream account. Brando approved Pipedream's terms; the existing Toggl credential was transferred privately from his signed-in profile to the hosted connection.
- The requested existing Connect project uses **development**, as Brando selected for the Free plan. No demo, local server, self-hosted deployment, or paid upgrade was created.
- Hosted Model Context Protocol (MCP) checks returned one workspace and zero entries for 10-28-2026 in `America/Los_Angeles` (midnight through the following midnight). No entry was created, edited, or deleted.
- A fresh Codex command-line interface (CLI) session successfully called both native MCP tools (`toggl-list-workspace-id-options` and `toggl-get-time-entries`) using the installed dynamic headers. It returned the same one workspace and zero entries. Existing sessions may need to reconnect or restart to load the server.
- Claude Code reports `Connected` in user scope, including in a fresh runtime startup. Its independent tool check stopped at the account’s weekly model limit before any tool call; do not describe that as a successful Claude read test.
- Pipedream reports the connected Toggl account healthy. Its hosted API proxy passed a workspace read. The application registry confirms proxy support for `api.track.toggl.com`.
- The live MCP catalog has 13 Toggl actions plus `retrieve_options`; none creates, edits, or deletes time entries. Write requests were intentionally not tested because setup verification is read-only.
- UB9sc's independent connection remains unverified. Its original Scalable connection link reaches Pipedream consumer OAuth but stalls at “Redirecting to sign in”; the consumer Sign in controls also failed in Chrome and the in-app browser. UB9sc acknowledged the direct Slack request and is checking its runtime’s support for the project-based route. It confirmed setup tests remain read-only. A shared URL, acknowledgement, or successful Mac test does not authenticate another host.

## Current Mac setup

The private file `~/.config/pipedream/toggl-agents-oauth.json` has mode `0600` and contains a Pipedream client ID/secret plus `project_id`, `environment`, `external_user_id`, `app_slug`, and `account_id`. The Toggl token stays in Pipedream. Never print or commit the private file, bearer headers, or account-connection links.

The exact `~/.codex/config.toml` server section is:

```toml
[mcp_servers.pipedream]
url = "https://remote.mcp.pipedream.net/v3"
http_headers_helper = "python3 -c 'import json,pathlib,urllib.request; c=json.loads((pathlib.Path.home()/\".config/pipedream/toggl-agents-oauth.json\").read_text()); p={k:c[k] for k in (\"client_id\",\"client_secret\")}; p[\"grant_type\"]=\"client_credentials\"; t=json.load(urllib.request.urlopen(urllib.request.Request(\"https://api.pipedream.com/v1/oauth/token\",data=json.dumps(p).encode(),headers={\"Content-Type\":\"application/json\"}),timeout=8)); print(json.dumps({\"Authorization\":\"Bearer \"+t[\"access_token\"],\"x-pd-project-id\":c[\"project_id\"],\"x-pd-external-user-id\":c[\"external_user_id\"],\"x-pd-environment\":c[\"environment\"],\"x-pd-app-slug\":c[\"app_slug\"],\"x-pd-account-id\":c[\"account_id\"]}))'"
```

This inline configuration command obtains a short-lived Pipedream access token when the client connects; it runs no server. Claude Code uses the same hosted endpoint and command under `headersHelper` in a user-scoped HTTP server. To reuse the installed Codex settings on this Mac:

```bash
python3 - <<'PYSETUP'
import json, pathlib, subprocess, tomllib
server = tomllib.loads((pathlib.Path.home()/'.codex/config.toml').read_text())['mcp_servers']['pipedream']
config = {'type': 'http', 'url': server['url'], 'headersHelper': server['http_headers_helper']}
subprocess.run(['claude', 'mcp', 'add-json', '--scope', 'user', 'pipedream', json.dumps(config)], check=True)
PYSETUP
```

Reconnect by starting a fresh Codex session or reconnecting `pipedream` through Claude's `/mcp`. The helper obtains fresh credentials. If the Pipedream OAuth client was revoked, replace that client's private credentials through Pipedream's supported flow; do not rotate another application's client. If the Toggl connection expires, a read call returns a hosted account-connection link: complete it using the same project, environment, and external user, then repeat the read-only test.

## Another host or agent

Use the same project/environment/external-user/account mapping from the authorized private configuration and an authorized Pipedream OAuth client, provisioned through a private credential channel. Do not put these credentials in issue #68, email, prompts, or this repository. A remote agent needs its own runtime access to that private configuration and token refresh; copying only the endpoint is insufficient. UB9sc must report which authentication mechanism its runtime supports and prove its own read access before filling an entry batch.

The separate [consumer server](https://pipedream.com/docs/connect/mcp/users) is `https://mcp.pipedream.net/v2`. Its browser sign-in stalled during this setup; this Mac uses the project-based route above. The original consumer setup is:

```bash
codex mcp add pipedream --url https://mcp.pipedream.net/v2
codex mcp login pipedream
```

For that consumer route only, reconnect with `codex mcp login pipedream`; Claude Code can use the same server with `claude mcp add --transport http --scope user pipedream https://mcp.pipedream.net/v2`, then `/mcp`. Do not overwrite the working project-based configuration merely to retry the consumer route.

## Creating authorized entries through the hosted proxy

[Pipedream's Connect API proxy](https://pipedream.com/docs/connect/api-proxy) supplies the stored Toggl authentication. Use the Pipedream bearer token, `x-pd-environment`, the matching external user/account, and a URL-safe Base64 encoded Toggl endpoint:

```text
POST https://api.pipedream.com/v1/connect/{project_id}/proxy/{encoded_toggl_url}?external_user_id={external_user_id}&account_id={account_id}
Toggl target: https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/time_entries
```

The [Toggl create-entry documentation](https://engineering.toggl.com/docs/track/api/time_entries/) defines `created_with`, `start`, `duration`, `workspace_id`, and optional description/project fields. Read today's entries first, use Brando's supplied times or explicitly labeled estimates where he authorized them, and coordinate one writer per batch. Any verified agent may fill an authorized batch; UB9sc is not the exclusive writer. Existing-entry edits/deletions are outside the current fill instruction. Creating projects or clients is not an entry-creation test.

Sources: [Pipedream developer server](https://pipedream.com/docs/connect/mcp/developers), [authentication](https://pipedream.com/docs/connect/api-reference/authentication), [development environments](https://pipedream.com/docs/connect/managed-auth/environments), [Claude dynamic headers](https://code.claude.com/docs/en/mcp#use-dynamic-headers-for-custom-authentication), and [Codex MCP](https://developers.openai.com/codex/mcp).
