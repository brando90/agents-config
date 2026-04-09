# Codex Remote Control — Status & Setup

Codex CLI has **no native `remote-control` command** like Claude Code. There is no phone handoff flow.
Active feature requests: [QR pairing (#13543)](https://github.com/openai/codex/issues/13543), [RC from ChatGPT app (#9224)](https://github.com/openai/codex/issues/9224), [app-server network exposure (#11166)](https://github.com/openai/codex/issues/11166).

---

## Option A: SSH + tmux (most reliable, works today)

No extra tools needed. Use a mobile SSH client (Blink on iOS, Terminus on Android).

```bash
# On the server — start a persistent session
tmux new -As codex
codex  # authenticate with ChatGPT login or OPENAI_API_KEY

# From phone/laptop — reconnect later
ssh <server> -t 'tmux attach -t codex'
```

Codex CLI is conversation-based, so it works well on small screens.

---

## Option B: App-server WebSocket (experimental)

The Codex app-server exposes a bidirectional JSON-RPC 2.0 API over WebSocket.
This is designed for programmatic/IDE clients (VS Code extension), not phone handoff — but it can be used for remote access.

```bash
# Start app-server with WebSocket on a port
codex app-server --listen ws://0.0.0.0:4500

# With auth (required for non-loopback — don't expose unauthenticated)
codex app-server --listen ws://0.0.0.0:4500 \
  --ws-auth capability-token \
  --ws-token-file /absolute/path/to/token

# Or signed bearer tokens (HMAC-signed JWT/JWS)
codex app-server --listen ws://0.0.0.0:4500 \
  --ws-auth signed-bearer-token \
  --ws-shared-secret-file /absolute/path/to/secret \
  --ws-issuer optional-issuer \
  --ws-audience optional-audience

# Health check
curl http://localhost:4500/readyz  # 200 OK when ready
```

**Security warning:** Non-loopback WebSocket listeners allow unauthenticated connections by default. Always configure `--ws-auth` when exposing remotely.

**Limitation:** You need a JSON-RPC client to talk to this — there's no built-in TUI that connects to a remote app-server yet. The TUI refactor to support this is in progress ([#11166](https://github.com/openai/codex/issues/11166)).

**SSH port-forward workaround** (avoids exposing the port publicly):

```bash
# On the server — start app-server on loopback only
codex app-server --listen ws://127.0.0.1:4500

# From laptop — tunnel the port
ssh -L 4500:127.0.0.1:4500 <server>
# Then connect your local client to ws://127.0.0.1:4500
```

---

## Option C: Third-party tools

- **[Remodex](https://github.com/Emanuele-web04/remodex)** — local-first bridge + iOS app. Keeps Codex runtime on your Mac, phone connects via paired secure session.
- **[HQSSH](https://hqssh.com/)** — iOS/Android app purpose-built for managing Claude Code, Codex, and Opencode on remote systems. Launch Codex in the right directory with one tap.
- **code-server** — run VS Code in a browser on the server, access from phone. Pair with Codex VS Code extension.
- **Tailscale + ttyd** — expose a terminal over HTTPS on a private Tailscale network.

---

## TODO

```
[ ] Monitor openai/codex#13543 (QR pairing) and #9224 (RC from ChatGPT) for native RC support
[ ] Monitor openai/codex#11166 (TUI connecting to remote app-server) for first-party remote TUI
[ ] Test app-server WebSocket + SSH port-forward on a SNAP node
[ ] Evaluate Remodex or HQSSH for phone access if tmux is too clunky
[ ] Once native RC ships, document it here and add to README.md Remote Access section
```

---

Sources:
- [Codex App-Server docs](https://developers.openai.com/codex/app-server)
- [App-Server README (GitHub)](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md)
- [Community: Using Codex CLI remotely from mobile](https://community.openai.com/t/using-codex-cli-remotely-using-your-mobile-device/1375896)
- [Feature request: QR pairing (#13543)](https://github.com/openai/codex/issues/13543)
- [Feature request: RC from ChatGPT (#9224)](https://github.com/openai/codex/issues/9224)
- [Feature request: Network app-server (#11166)](https://github.com/openai/codex/issues/11166)
- [Discussion: RC from ChatGPT app (#9200)](https://github.com/openai/codex/discussions/9200)
