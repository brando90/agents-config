# Toggl Track for Brando's agents

**Doc link:** <https://github.com/brando90/agents-config/blob/main/machine/toggl.md>

**TLDR:** Any agent with verified access may populate authorized Toggl entries; read existing entries and coordinate one writer per batch to avoid duplicates. Use Pipedream's hosted service, authenticate each client, and verify the required tools before claiming write access. Never put credentials in this repository.

## Status (10-28-2026)

- Ultimate Brando9 (the Linux assistant) added the Pipedream server as a connected app and sent Brando the OAuth link (11:24). Waiting on his tap and Toggl connect.
- Any of Brando's agents may fill Toggl (Brando, 2026-10-28 11:36): ub9sc is not the exclusive writer. Whichever agent has verified access fills the day's entries from his entry in the weekly updates Doc: one entry per project line, his own minutes where he gave them and estimates (marked est.) otherwise. Create only, never edit or delete existing entries. Read today's entries first so nothing is duplicated if another agent already filled them.
- Ultimate Brando9 (the Linux assistant) will fill once its Pipedream read-only test passes (workspaces, today's entries).
- Codex already wrote the Mac-side setup and reconnect steps in `machine/mac.md` (section "Toggl Track through Pipedream hosted MCP"); use that for Codex and Claude Code on the Mac.

## Setup for another agent (not yet verified from Codex or Claude Code on the Mac)

- Claude Code: `claude mcp add --transport http --scope user pipedream https://mcp.pipedream.net/v2`, then `/mcp` to sign in.
- Codex: `codex mcp add pipedream --url https://mcp.pipedream.net/v2`, then `codex mcp login pipedream`. Reconnect with the login command; see `machine/mac.md` for the equivalent configuration.
- Pick Toggl in Pipedream and connect Brando's account. Test with a read-only call (workspaces, today's entries) before any write.
- Never put a token or key in this repo.

## Hosted connection routes

The [end-user service](https://pipedream.com/docs/connect/mcp/users) at
`https://mcp.pipedream.net/v2` uses browser OAuth and does not configure an
existing Connect project's production environment.

To use a specified Connect project, follow the [developer remote-server guide](https://pipedream.com/docs/connect/mcp/developers):
`https://remote.mcp.pipedream.net/v3`, a short-lived OAuth bearer token, and
`x-pd-project-id`, `x-pd-environment`, `x-pd-external-user-id`, and
`x-pd-app-slug` headers (`toggl` for Toggl Track). The project and external user
must match the hosted account connection. Development and production accounts
are separate; do not silently switch environments. The Free plan supports
Connect in development only; production requires an eligible plan. See
[Pipedream environments](https://pipedream.com/docs/connect/managed-auth/environments).

OAuth authenticates the agent to Pipedream. The current
[Pipedream Toggl component](https://github.com/PipedreamHQ/pipedream/blob/master/components/toggl/toggl.app.mjs)
uses a Toggl API token behind the hosted connection. Do not ask Brando to paste
that token into chat or put it in the repository. Browser sign-in, a configured
server, and authenticated agent tool access are separate verification steps.

## Verified limits (10-28-2026)

- GitHub sign-in reached the existing Pipedream Connect workspace. The consumer hosted sign-in stalled at its redirect; it is not yet authenticated in Codex.
- The development project remote server initialized successfully and returned 14 tools: 13 Toggl actions plus `retrieve_options`. No create/update/delete time-entry action appeared. Creating projects or clients does not establish time-entry write capability.
- The read-only workspace call returned an account-connection link, not workspace data. Toggl connection and today's entry test remain pending. Do not report this as a passed test.
- The development connection reached Pipedream's terms acceptance screen. Browser confirmation is pending. No Toggl entries were created or changed.
- For entry creation, investigate Pipedream's documented [Connect API proxy](https://pipedream.com/docs/connect/api-proxy) or an available hosted action; do not build or self-host a server. Verify the exact supported route before assigning a fill batch.

## Other agents

- Codex, 10-28-2026: configured the consumer server and verified the separate development server/tool catalog; see the limits above. Setup is not yet verified end to end.
(add a line here: agent, date, what works)
