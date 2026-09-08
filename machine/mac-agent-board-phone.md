# Private phone access to the agent board

**TLDR:** Use Tailscale Serve to reach the live Mac board from a phone, then save its private link to the phone's Home Screen. The Mac must be awake, connected, and logged in; the board displays a warning when its snapshot is over 90 seconds old.

## Setup

The regular board installer must already be running. Install the open source
Tailscale variant and run the phone helper:

```bash
brew install tailscale
python3 ~/agents-config/scripts/agent_board_phone.py
```

If prompted, open the printed sign-in link, use your personal Tailscale account,
and authorize the `agent-board` device. Run the helper again after signing in.
If Tailscale asks you to enable encrypted web serving for the account, follow
its printed setup link, then rerun the helper. The helper prints the private
`https://…ts.net/` address only after serving has been configured.

Install Tailscale on the phone and connect using the same account. Open the
printed address in Safari (iPhone) or Chrome (Android), and choose **Add to Home
Screen** from the browser's Share/menu options. For a focus interval, use that
icon for a quick status check and close it when finished.

## Access and behavior

- Tailscale's network access rules determine who can open the board. Use a
  personal network containing only your devices; a shared workplace network
  needs an administrator to restrict access before serving private task data.
- A small server binds only to `127.0.0.1:8766` and serves exactly
  `~/.agent-board/board.html` at `/` or `/board.html`. Every other path is rejected,
  and responses disable caching. Tailscale forwards encrypted private requests
  to it. The helper never enables Tailscale Funnel (public internet exposure).
- A dedicated user-level background service, `com.brando.agentboard.tailscale`,
  starts at Mac login and restarts if it exits. Tailscale runs in userspace
  networking mode: this service does not replace the Mac's network routes or
  name resolution, so existing Stanford connectivity remains under its own
  configuration.
- A second service, `com.brando.agentboard.web`, runs the local board server.
  Direct Tailscale file serving requires elevated privileges even with a
  user-owned daemon; the local server avoids that requirement.
- Private connection state and certificates stay under
  `~/.agent-board/tailscale/` with owner-only directory permissions. Do not
  commit that directory or share sign-in links.
- The existing renderer continues generating the board every 20 seconds.
  Phones display stacked task rows; desktops keep all eight table columns.
  An old snapshot gets an **Updates paused** warning. Individual remote rows
  can be older than the page; their existing stale-poll notes still apply.
- A sleeping, powered-off, disconnected, or logged-out Mac cannot serve the
  board. This setup does not create an online copy or change sleep settings.

## Check or stop

```bash
python3 ~/agents-config/scripts/agent_board_phone.py --status
tailscale --socket="$HOME/.agent-board/tailscale/tailscaled.sock" serve status
```

After updating `~/agents-config/scripts/agent_board_serve.py`, restart its
already-running process to load the new code:

```bash
launchctl kickstart -k "gui/$(id -u)/com.brando.agentboard.web"
```

To stop sharing and unload only the dedicated board connection:

```bash
tailscale --socket="$HOME/.agent-board/tailscale/tailscaled.sock" serve --https=443 off
launchctl bootout "gui/$(id -u)/com.brando.agentboard.tailscale"
launchctl bootout "gui/$(id -u)/com.brando.agentboard.web"
```

The helper restarts the service when run again. To prevent automatic startup
on future logins as well, move
both `com.brando.agentboard.tailscale.plist` and `com.brando.agentboard.web.plist` out of
`~/Library/LaunchAgents/` after unloading it.

Reference: [Tailscale Serve documentation](https://tailscale.com/docs/reference/tailscale-cli/serve).
