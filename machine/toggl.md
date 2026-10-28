# Toggl Track for Brando's agents

**Doc link:** <https://github.com/brando90/agents-config/blob/main/machine/toggl.md>

**TLDR:** Toggl Track has no official MCP server. Brando's agents use Pipedream's hosted MCP server (`https://mcp.pipedream.net/v2`, Toggl app page `https://mcp.pipedream.com/app/toggl`), which signs in with OAuth. Nothing is built or self-hosted, and no Toggl API token is stored anywhere. Do not duplicate this: if your agent already has Toggl working another way, add a line under "Other agents" below and say how.

## Status (2026-10-28)

- Ultimate Brando9 (the Linux assistant) added the Pipedream server as a connected app and sent Brando the OAuth link. Setup is waiting on Brando's sign-in to Pipedream with his own account, then connecting his Toggl there.
- Ultimate Brando9 does the daily fill: one Toggl entry per project line of Brando's entry in the weekly updates Doc, his own minutes where he gave them and estimates (marked est.) otherwise. It only creates entries, never edits or deletes existing ones.
- Codex and ub9sc: nothing is needed from you unless you must write entries yourself. Then follow the setup below, and add a line here when it works.

## Setup for another agent (not yet verified from Codex or Claude Code on the Mac)

- Claude Code: `claude mcp add --transport http pipedream https://mcp.pipedream.net/v2`, then `/mcp` to sign in.
- Codex: add the same URL as a streamable-HTTP MCP server in `~/.codex/config.toml` (see Pipedream's current docs), then run its MCP login.
- Pick Toggl in Pipedream and connect Brando's account. Test with a read-only call (workspaces, today's entries) before any write.
- Never put a token or key in this repo.

## Other agents

(add a line here: agent, date, what works)
