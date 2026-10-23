---
name: pi-local-herdr
description: Run Pi with Gemini for VeriBench or the free local Ollama fallback, continue a saved task, and manage this Mac's installed Herdr integrations and machine profiles. Use for this installed setup, not unrelated remote-job scheduling.
---

# Local Pi and Herdr

**TLDR:** Use `pi-gemini` for authorized VeriBench work and `pi-local` for free local inference; switching is explicit, not automatic. Qwen3.5 9B passed the disposable 10-test repair in 41.0 seconds on 10-22-2026; see the dated proof for scope. Herdr has seven saved profiles; five SNAP nodes have reachable receipts; after an earlier timeout, explicit-target skampere1 agent-list succeeded and reported Pi idle. Sherlock and FarmShare SSH need human authentication.

## Gemini for VeriBench

- Run `~/.local/bin/pi-gemini` from the working repository; add `-p "task"` for a noninteractive task. It loads the existing `~/keys/gemini_allen_key.txt` into Pi's `GEMINI_API_KEY` environment at runtime. Do not print, copy into configuration, or commit the credential. Its separate profile is `~/.local/share/pi-gemini/`.
- The default is `google/gemini-3-flash-preview`, minimal thinking, with an 8,192-token output limit. Select another Gemini model with `PI_GEMINI_MODEL=gemini-3.1-pro-preview pi-gemini` when appropriate; preserve required experiment/model pins. Provider selection stays on Google.
- Brando authorized this route for VeriBench on 10-22-2026 and clarified that the current setup/test is within that scope. Use the task's existing authorization and budget; do not add billing accounts, credits, subscriptions or keys. Gemini runs remotely and receives the prompts/context sent by Pi. It is not a guaranteed-free fallback.
- A live native Pi test returned `PONG` in 1.58 seconds (53 input / 2 output tokens). This verifies connectivity, not coding quality. The installed wrapper's routing and secret handling were checked without further generation.
- For local continuation, save a checkpoint, stop or hand off the old writer, then use `pi-takeover` or `pi-resilient` below. There is no automatic Gemini-to-local switch or native cross-provider conversation transfer.

## Local coding and recovery

- Run `~/.local/bin/pi-local` from the repository, or `pi-local -p "task"` for a single task. Pi 1.4.0 talks only to the configured loopback Ollama model by default. Current profile: `~/.local/share/pi-local/models.json`.
- `pi-resilient CHECKPOINT.md --error-log quota.log -p` starts a fresh local session from a saved quota/context failure. It does not invoke or monitor the paid primary agent. `pi-takeover CHECKPOINT.md -p` handles other saved tasks. These are checkpoint handoffs, not native Codex/Claude conversation resumes.
- Ensure the old writer has stopped or handed over ownership. Supply `--previous-pid PID` when known; the wrapper refuses a live process. Recovery wrappers share a per-repository lock, preserve the checkpoint hash, and log receipts under `~/.local/state/pi-local/`. A zero exit is not task acceptance: rerun the requested tests independently.
- Preserve failed gates, scientific model pins, budgets, and other owners' work. A small local model is not a substitute for a specifically required reviewer.
- Ollama runs as user LaunchAgent `com.brando.ollama-local`, bound to `127.0.0.1:11434`, with cloud features disabled. `ollama list`, `ollama ps`, and `launchctl print gui/$(id -u)/com.brando.ollama-local` inspect it. No provider keys or paid calls are part of this route.

## Installed Herdr integrations

- All 17 requested integrations report current: pi, omp, claude, codex, copilot, devin, droid, kimi, opencode, kilo, hermes, qodercli, qwen, cursor, mastracode, antigravity-cli and grok. Check `herdr integration status`; installation is not proof of provider authentication or coding success.
- Both Pi wrappers explicitly load `~/.pi/agent/extensions/herdr-agent-state.ts` while other extensions remain undiscovered. The official hook is inactive outside Herdr; in interactive mode it reports session and agent state through Herdr's local socket. Both installed wrappers emitted session and idle events in a local test. This does not establish remote control or full session-restore behavior.
- Resume a saved Pi session using the matching launcher, e.g. `pi-gemini --session PATH` or `pi-local --session PATH`, so its profile and authentication are available. Existing running clients may need their documented reload/restart to load newly installed hooks; installing files does not reload an active client.

## Cross-machine control

- Inspect `herdr machine list --json`. Brando explicitly authorized the original six profiles enabled for normal automatic connection on 10-22-2026, superseding the initial manual/no-retry mode. skampere3 was subsequently added and verified reachable; five SNAP nodes have reachable receipts. Sherlock/FarmShare are now temporarily disabled pending human login; the latest noninteractive checks stopped at host-key verification. Avoid adding redundant reconnect loops.
- SNAP aliases use the existing ProxyJump through whale; Sherlock uses the existing ControlMaster socket. Preserve normal host-key checks. Passwords, keytabs and login prompts remain outside this setup's scope; ask for an actual Duo step when required.
- Reachability and installed hooks do not prove remote agent control; the earlier skampere1 agent-list probe timed out, but a subsequent explicit-target check succeeded and reported Pi idle.

## Remote Pi parity

- Check actual shells, not only Herdr reachability: `command -v pi; pi --version`. Five SNAP nodes have Pi 1.4.0; use the shared `/dfs/scratch0/brando9/bin/pi` launcher, with each `~/.local/bin/pi` pointing to it. It resolves the existing node-local package and loads the existing Node version manager when needed.
- An already-open shell does not reread startup files. Immediate recovery: `export PATH="/dfs/scratch0/brando9/bin:$HOME/.local/bin:$PATH"; hash -r; pi --version`. Do not install Ubuntu's unrelated `apt` package named `pi`.
- `pi --check-local` checks the configured local route without generation. For the existing `snap-coder` loopback profile, the launcher reuses the current service or makes one bounded SSH tunnel attempt to skampere1. It never starts GPU workloads, loads provider keys or rewrites model settings. Explicit other providers remain unchanged. Keep host-key checks and human authentication boundaries.
- Current fresh-session provider/model: `snap-coder/qwen3-coder-30b`; skampere1 serves port 18201, other SNAP hosts forward loopback port 18127. The earlier 27B endpoint is unavailable. See `machine/pi-host-parity-10-22-2026.md` for proof and historical failures.
- Same command does not mean the same hardware or local model server. Sherlock/FarmShare require independent authentication and verification. Their pending user-level installer is `scripts/install_pi_remote.sh`; it installs Pi 1.4.0 with npm under the home directory, needs Node >=22.19.0, and preserves shell files with backups. Never infer successful installation from a copied script.

## Persistent mouse and clipboard

- Keep `ui.mouse_capture = true` and `ui.copy_on_select = true` in Herdr configuration. `herdr config check` and `herdr server reload-config` verified this Mac's settings applied; iTerm2 profile and live gestures are still unverified because computer control denied access to iTerm2.
- iTerm2's active saved profile must allow mouse reporting, wheel events, clicks and drags. Keep Command-C/Command-V as normal copy/paste; Option-drag temporarily gives native terminal selection. Do not disable mouse reporting to fix selection, because Herdr navigation needs it.
- Local images: Save to Temp File and Paste Path, optionally remember choice. Remote images: `keys.remote_image_paste = "ctrl+v"` works specifically in supported `herdr --remote` attachments; verify transfer. A Mac temporary path is not accessible on SNAP merely because it was pasted there.
- Follow `machine/herdr-mouse-agent-repairs-10-22-2026.md` for persistence acceptance checks and observed agent repairs. Do not claim input “always works” from configuration validation alone.

## Reuse before reinstalling

- Before recovery, inspect the existing versions, model store, machine catalog and integration status. Reuse healthy installations and connections; repair only observed drift. Do not create another Google Doc, pull request or duplicate machine profile.
- Preferred saved machine order: skampere1, skampere2, skampere3, mercury1, mercury2, Sherlock, FarmShare. `~/.local/bin/herdr-order` checks it; `herdr-order --apply` changes only order, backs up the catalog, and preserves all profiles/selection. Local remains first. The command is not a scheduled watcher.
- Canonical setup branch is `codex/mac-pi-herdr-10-22-2026`, unmerged PR #87 in brando90/agents-config. Until merged, main alone does not contain these files. Reuse Google Doc ID `1VkkBXmcezvHvq_XRrV1gw4Q_yPZ6Ni73-efcMhkoCm4` in Agent Archive; preserve sharing and update the matching section.
- Keep configuration and recovery instructions in GitHub, the readable guide in Google Drive, and credentials in each application's protected storage. Existing Codex connections do not automatically authorize Devin. Expired authentication calls for reconnecting that service, not reinstalling every client. No credentials belong in Git or the Google Doc.

## Reproduction and evidence

Read the dated receipt in `~/agents-config/machine/mac-pi-herdr-10-22-2026.md` once its pull request lands; before then, use the installed copy at `~/.local/share/pi-local-setup/10-22-2026/`. Launcher source is `scripts/pi_local.py` in the same pull request. Local logs are not automatically published.

New local-model installation must inspect available disk space as well as memory. Ollama creates a local identity file on first startup; honor any task-specific prohibition on new key files. Keep the local route free. The separately authorized Gemini route uses the existing key and task budget; do not change billing or create credentials.
