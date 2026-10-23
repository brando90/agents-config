# MacBook Pro: local Pi and Herdr — 10-22-2026

**Doc link:** <https://github.com/brando90/agents-config/blob/codex/mac-pi-herdr-10-22-2026/machine/mac-pi-herdr-10-22-2026.md>

**Google Doc:** <https://docs.google.com/document/d/1VkkBXmcezvHvq_XRrV1gw4Q_yPZ6Ni73-efcMhkoCm4/edit>

**TLDR:** Pi 1.4.0, Ollama 0.40.8 and Herdr 0.9.5 are installed without sudo on this M1 Max/64 GiB Mac. Model download and coding verification are in progress; four initial SNAP Herdr status checks passed, while Sherlock/FarmShare SSH require authentication.

## Installation

1. Inspected chip, memory, disk and existing configuration. Only 5.3 GiB was free. With explicit permission, removed an unused 2023 Hugging Face model-download cache (21,113,714,475 bytes; no open files reported), recovering about 19.7 GiB.
2. Installed Pi with `npm install -g --prefix ~/.local @earendil-works/pi-coding-agent@1.4.0`. Extracted the official [Ollama release](https://github.com/ollama/ollama/releases/tag/v0.40.8) into `~/.local/opt/ollama-0.40.8`; linked `~/.local/bin/ollama`. Installed the official [Herdr ARM64 binary](https://github.com/herdrdev/herdr/releases/tag/v0.9.5) as `~/.local/bin/herdr`.
3. Configured user LaunchAgent `com.brando.ollama-local`: loopback only, cloud disabled, 32,768-token context. User explicitly allowed Ollama's first-run local identity file. No provider key, paid service, subscription or charge was added; passwords, keytabs and login prompts were untouched.
4. Selected `ollama pull qwen3.5:9b-q4_K_M` (6.6 GB). A 27B download was stopped before inference after a multi-hour estimate. [Pi profile](pi-local-models.example.json), [launcher source](../scripts/pi_local.py), and [loadable skill](../skills/pi-local-herdr/SKILL.md) reproduce the configuration.

## Checks and usage

Eight launcher contract checks passed. The disposable Python repair baseline is **2/10 passing, 8 failing**. Pi repair and independent verification are pending the model download; no inference success is claimed yet. Install durations were not separately measured.

From a repository, run `pi-local`. For a saved task: `pi-takeover CHECKPOINT.md -p`; quota recovery: `pi-resilient CHECKPOINT.md --error-log quota.log -p`. Ensure the previous writer has stopped; `--previous-pid PID` verifies a known process. Recovery uses a new local session, records a checkpoint hash, and never invokes a paid primary agent.

## Cross-machine outcome

- **skampere1, skampere2, mercury1, mercury2:** Herdr setup and individual `machine status` checks succeeded through the existing whale gateway. A later skampere1 agent-list command timed out in its server-status probe; actual agent control is not established by the earlier checks.
- **Sherlock:** existing ControlMaster configuration preserved; single SSH probe refused (1.08 s). Its existing private `sherlockctl` bridge executed `hostname` successfully and found Herdr. This does not establish a working Herdr SSH connection.
- **FarmShare:** existing alias preserved; single SSH probe refused (4.80 s). Profile saved but unverified. No refusal retries on either host.

All six profiles are disabled after testing to avoid automatic reconnects; final `herdr machine status --json` reports six disabled profiles. To address one target, enable its profile, run `herdr --machine skampere1 agent list`, then disable it; disabled profiles reject direct commands. Local Herdr server startup and workspace listing passed, then the test server was stopped. One sequencing mistake briefly overlapped mercury2 setup with the Sherlock probe; subsequent host calls were serialized.

**Evidence:** local step log and receipts: `~/.local/share/pi-local-setup/10-22-2026/`. Prior Pi cluster note: [PR #86](https://github.com/brando90/agents-config/pull/86). Google Doc is viewable by link; this change is for an unmerged pull request.
