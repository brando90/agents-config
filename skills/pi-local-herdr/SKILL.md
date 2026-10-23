---
name: pi-local-herdr
description: Run the free local Pi coding fallback on Brando's Mac, resume a saved task after quota exhaustion, or inspect the saved Herdr machine profiles. Use for this installed setup, not unrelated remote-job scheduling.
---

# Local Pi and Herdr

**TLDR:** Use the installed local Pi launchers for bounded coding work and saved-task recovery. Herdr has six saved profiles; four SNAP setup/status checks passed on 10-22-2026, but a later skampere1 agent-list command timed out. Sherlock and FarmShare SSH need human authentication.

## Local coding and recovery

- Run `~/.local/bin/pi-local` from the repository, or `pi-local -p "task"` for a single task. Pi 1.4.0 talks only to the configured loopback Ollama model by default. Current profile: `~/.local/share/pi-local/models.json`.
- `pi-resilient CHECKPOINT.md --error-log quota.log -p` starts a fresh local session from a saved quota/context failure. It does not invoke or monitor the paid primary agent. `pi-takeover CHECKPOINT.md -p` handles other saved tasks. These are checkpoint handoffs, not native Codex/Claude conversation resumes.
- Ensure the old writer has stopped or handed over ownership. Supply `--previous-pid PID` when known; the wrapper refuses a live process. Recovery wrappers share a per-repository lock, preserve the checkpoint hash, and log receipts under `~/.local/state/pi-local/`. A zero exit is not task acceptance: rerun the requested tests independently.
- Preserve failed gates, scientific model pins, budgets, and other owners' work. A small local model is not a substitute for a specifically required reviewer.
- Ollama runs as user LaunchAgent `com.brando.ollama-local`, bound to `127.0.0.1:11434`, with cloud features disabled. `ollama list`, `ollama ps`, and `launchctl print gui/$(id -u)/com.brando.ollama-local` inspect it. No provider keys or paid calls are part of this route.

## Cross-machine control

- Inspect `herdr machine list --json`. Profiles are deliberately disabled after testing to prevent automatic reconnects. An unqualified `herdr machine status` reports those disabled states without connecting.
- Enable only the selected profile by its ID, run one explicit-target command such as `herdr --machine skampere1 agent list`, then disable it again. Disabled profiles reject direct commands. Keep the multi-machine UI closed during these one-shot checks; its reconnect loop conflicts with the no-retry requirement.
- SNAP aliases use the existing `ProxyJump` through whale; Sherlock uses the existing ControlMaster socket. Preserve existing SSH configuration and normal host-key verification.
- Connect to one node at a time. After a refusal, stop attempts on that route; do not run reconnect loops. Passwords, keytabs and login prompts are outside this setup's scope. Ask Brando for an actual Duo step.
- Sherlock's existing `sherlockctl` bridge worked while its SSH login was refused. This is separate from a working Herdr SSH connection. FarmShare has only a saved, unverified profile.

## Reproduction and evidence

Read the dated receipt in `~/agents-config/machine/mac-pi-herdr-10-22-2026.md` once its pull request lands; before then, use the installed copy at `~/.local/share/pi-local-setup/10-22-2026/`. Launcher source is `scripts/pi_local.py` in the same pull request. Local logs are not automatically published.

New installation must inspect available disk space as well as memory. Ollama creates a local identity file on first startup; honor any task-specific prohibition on new key files. Use only free tools and local inference, with no new paid service, provider key, subscription, or charge.
