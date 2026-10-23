# Herdr mouse, clipboard and agent repairs — 10-22-2026

**Doc link:** <https://github.com/brando90/agents-config/blob/codex/mac-pi-herdr-10-22-2026/machine/herdr-mouse-agent-repairs-10-22-2026.md>

**Google Doc:** <https://docs.google.com/document/d/1VkkBXmcezvHvq_XRrV1gw4Q_yPZ6Ni73-efcMhkoCm4/edit>

**TLDR:** Keep mouse reporting enabled for Herdr navigation, enable drag-to-copy, and retain macOS Command-C/Command-V. Herdr configuration validates and was applied live; iTerm2 profile settings and the user's failing gesture remain unverified because computer control denied access to iTerm2. No claim of an “always works” guarantee.

## Persistent setup

The Mac's `~/.config/herdr/config.toml` now explicitly contains the following settings, confirmed supported by the installed Herdr 0.9.5 `--default-config`. Merge these sections into an existing file; do not replace unrelated configuration.

```toml
[ui]
mouse_capture = true
copy_on_select = true

[ui.toast.clipboard]
enabled = true

[keys]
remote_image_paste = "ctrl+v"
```

Run `herdr config check`, then `herdr server reload-config`. On this Mac, validation returned `config: ok`; live reload returned `status: applied` and no diagnostics. Original config is backed up under `~/.local/share/pi-local-setup/10-22-2026/herdr-config-before-mouse.toml`. These values were already the documented defaults; pinning them alone does not establish or resolve the reported cause.

In **iTerm2 Settings → Profiles → the active profile → Terminal**, keep **Enable mouse reporting**, **Report mouse wheel events**, and **Report mouse clicks & drags** enabled. Save the profile, rather than changing only a current session. Disabling clicks/drags lets iTerm2 select text but prevents Herdr receiving those gestures. This profile step is still pending on this Mac; tool access to iTerm2 was explicitly blocked and was not bypassed.

## Daily actions and recovery

| Action | Use |
|---|---|
| Herdr tabs, sidebar, pane selection and scrolling | Ordinary click/drag/wheel with mouse reporting enabled. |
| Copy pane text | Herdr drag selection copies automatically. |
| Force native terminal selection | Hold **Option** while dragging, then **Command-C**. This can include visible pane borders; it is a fallback. |
| Paste text | **Command-V**, iTerm2's normal Paste action. Keep it mapped to Paste; do not globally remap it to Control-V. |
| Local clipboard image | Choose **Save to Temp File and Paste Path**, optionally **Remember my choice**. The local agent must support reading images; a path is not image bytes. |
| Remote clipboard image | In a supported `herdr --remote` attachment, **Control-V** uses Herdr's remote image transfer. This setting is only active in that mode; verify the remote file is readable. A Mac `/var/folders/...` path alone does not work on SNAP. |
| Mouse stops after another terminal program | First distinguish Herdr navigation from text selection. Use Option-drag for immediate selection. Validate/reload Herdr configuration; then detach and reattach the Herdr client if needed, preserving running sessions. Do not terminate servers or jobs to reset mouse state. |

Keep normal Command-C/Command-V bindings. Control-C is an interrupt when no selection-copy handler consumes it; it is not a universal copy shortcut. The image paste dialog and mouse-reporting controls are separate settings; the reported timing does not prove the image choice caused mouse failure.

**Acceptance check still needed in iTerm2:** click two Herdr tabs; scroll a pane; drag-select a known line and paste it into an empty editor; repeat using Option-drag/Command-C; paste text with Command-V; paste one local image and verify the target reads it; repeat remote image transfer only in a supported remote attachment. Repeat after opening a fresh iTerm2 session to establish persistence. No live clipboard contents were inspected or overwritten by this repair.

Sources: [Herdr configuration](https://herdr.dev/docs/config-reference/), [Herdr keyboard/mouse behavior](https://herdr.dev/docs/keyboard/), [iTerm2 mouse reporting and Option override](https://iterm2.com/documentation-preferences-profiles-terminal.html).

## skampere3 and SNAP Pi follow-up

The original six-machine list came from step 4 of Brando's first setup request. On his subsequent request, added **skampere3**, preserving the existing whale ProxyJump. `herdr machine add skampere3 --label skampere3` returned a ready remote server; its explicit-target status returned reachable. There are now seven saved profiles.

The screenshot's Pi failures were two distinct routes: an exhausted inference-provider balance (HTTP 402), followed by local model connection errors. At the follow-up check, skampere1's `http://127.0.0.1:18127/health` returned 200, `/v1/models` listed `pi-qwen3.6-27b`, and Pi's custom `snap-qwen` provider pointed to that endpoint. The live session transcript subsequently recorded successful replies and tool use after the errors. Configuration/server changes predated this inspection, so this work does not claim credit for restarting the model server. Existing GPUs, provider keys, and saved configuration alone do not prove a working route. An isolated Pi test successfully edited its disposable file to the exact expected contents, but the process exceeded its 90-second completion deadline; record this as tool execution verified, completion timeout—not an unqualified pass. Persistent default provider/model were absent; after checking the installed settings schema, set `defaultProvider=snap-qwen` and `defaultModel=pi-qwen3.6-27b`, preserving other settings and a backup. Fresh plain `pi` sessions use that local route; existing sessions retain their selected model.

Read-only skampere3 inventory verified eight NVIDIA B200 GPUs (183359 MiB reported each), two AMD EPYC 9565 processors, 72 physical cores/socket, 144 total cores, 288 logical threads, Ubuntu 24.04.3 LTS, and 3,246,223,564,800 bytes of operating-system-visible RAM. Local scratch filesystem size is 91,796,928,036,864 bytes; that is capacity, not available space. Published the row in the [Koyejo wiki](https://ilwiki.stanford.edu/doku.php?id=koyejo-servers:koyejo) and verified the rendered row plus last-modified attribution to brando at 20:48 PDT. The four existing rows were preserved. CPU base frequency (3.15 GHz) comes from the [AMD specification](https://www.amd.com/en/products/processors/server/epyc/9005-series/amd-epyc-9565.html), not an instantaneous clock measurement.

## Agent errors, fixes and remaining limits

| Symptom | Fix or next action | Verified result |
|---|---|---|
| Herdr profiles show disabled | User explicitly authorized all six automatic connections; enabled each saved profile. | skampere1/2 and mercury1/2 reachable. Sherlock/FarmShare authentication refused; credentials and prompts untouched. Reachability does not prove remote agent control. |
| Missing agent applications/integrations | Installed requested missing clients under the home directory and used official Herdr integration installers. | All 17 requested integrations current; experimental Letta was not in the request. Full coding/authentication tests were not performed for every client. |
| omp hook installation fails: missing extensions directory | Verified omp installed, created `~/.omp/agent/extensions`, reran installer. | omp integration current v10. |
| npm install fails with ENOSPC | Inspected disposable caches; removed 957 cache files older than 24 hours by access and modification time, 3,465,956,630 bytes; reran installation. | Requested npm clients installed; version/help checks recorded. |
| Devin: `agy_acp_server.par` missing | Install official Antigravity Agent Client Protocol (ACP) adapter; the ordinary CLI is a different executable. Preserve the existing working adapter symlink. | Antigravity initialization completed at 20:23:47. |
| Devin: OpenCode command not found | Installed `opencode-ai` under `~/.local`; ensure that bin directory is in Devin's PATH. | Both OpenCode adapters initialized. |
| Devin: Minion Code 0.1.44 imports incompatible ACP schema | Installed Minion Code 0.1.45 and registered **Minion Code (repaired)** in `~/.windsurf/acp/registry.json`; old entry remains disabled. | Repaired entry initialized at 20:23:39. Older ACP dependency pins did not repair 0.1.44. |
| Devin: fast-agent 0.10.1 dependency resolution fails | Installed fast-agent-acp 0.10.47; added repaired local registry entry. | Installation complete; repaired entry reload/handshake still pending. |
| Devin: MiniMax 0.2.7 exits before handshake | Installed 0.6.12 in isolated `~/.local/opt/minimax-code`, rebuilt its native dependency; registered repaired entry. | Installation/rebuild complete; repaired entry reload/handshake still pending. |
| Devin: poolside expected `pool-darwin-arm64` | Added expected executable alias to the installed official binary. | Initialization completed at 20:25:01. |
| Hermes installer cannot find downloaded uv | Used stable v0.22.4 installer and pinned uv 0.12.3, verified official archive SHA-256, installed without sudo/login. | Install completed; Hermes integration current v5. |
| Devin connected-service authentication errors | A configured endpoint does not transfer authorization from Codex. Use each service's supported connection flow in Devin. | Connection setup remains pending; do not retry blindly or copy raw credentials. |

Initialization proves adapter startup, not provider entitlement or a successful coding task. Preserve failed attempts; make one evidence-based repair and verify it, then record a remaining blocker rather than retrying indefinitely. All times above are local PDT on 10-22-2026.

**TLDR-end:** [agents-config: Herdr input and agent repair] Persistent Herdr input settings are applied; the iTerm2 profile and live input acceptance check remain pending. Agent failures and concrete recovery results are retained for the next machine.
