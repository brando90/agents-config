# MacBook Pro: local Pi and Herdr — 10-22-2026

**Doc link:** <https://github.com/brando90/agents-config/blob/codex/mac-pi-herdr-10-22-2026/machine/mac-pi-herdr-10-22-2026.md>

**Google Doc:** <https://docs.google.com/document/d/1VkkBXmcezvHvq_XRrV1gw4Q_yPZ6Ni73-efcMhkoCm4/edit>

**TLDR:** Free local Pi works: Qwen3.5 9B repaired a disposable Python project in **41.0 seconds**, with **10/10 tests independently passing**. Herdr has six saved profiles; remote access has the limitations below.

## Install and use

1. Verified **Apple M1 Max, 64 GiB RAM**. With permission, removed an unused 2023 model-download cache (21,113,714,475 bytes; no open files), recovering about 19.7 GiB from an initial 5.3 GiB free.
2. Installed Pi **1.4.0** using `npm install -g --prefix ~/.local @earendil-works/pi-coding-agent@1.4.0`; installed official [Ollama 0.40.8](https://github.com/ollama/ollama/releases/tag/v0.40.8) and [Herdr 0.9.5](https://github.com/herdrdev/herdr/releases/tag/v0.9.5) ARM64 releases under `~/.local`, with verified release checksums and no sudo.
3. Configured Ollama's user LaunchAgent on loopback, cloud disabled, 32,768-token context; installed `qwen3.5:9b-q4_K_M` (6.6 GB). Its local identity file was explicitly approved. No provider keys, paid services, subscriptions or charges were added; passwords, keytabs and login prompts were untouched.
4. From a repository: `pi-local`. Saved-task handoff: `pi-takeover CHECKPOINT.md -p`. Quota recovery: `pi-resilient CHECKPOINT.md --error-log quota.log -p`. Stop the previous writer first; `--previous-pid PID` checks a known process. Recovery starts a fresh checkpoint-based local session and saves a hash receipt.

## Verification and timings

The repair baseline was **2/10 passing**. Pi fixed tail-chunk handling and nonpositive-size validation in **40.984 s**; an independent rerun passed **10/10** in **0.059 s**, with tests unchanged. Eight launcher checks passed. This is one small functional test, not the Air benchmark or a performance comparison. [Frozen proof and test source](pi-local-proof-10-22-2026.json).

Download-to-registration took **48.9 minutes** (30-second polling resolution). Ollama's multipart download repeatedly stalled and rolled back progress; a resumable single-stream official-registry download completed in **4:30**, passed SHA-256 verification, then `ollama pull` finalized it. A 27B download was abandoned before inference. Install durations were not separately measured.

## Remote outcome

Existing Secure Shell (SSH) aliases already supplied whale jumps for **skampere1/2 and mercury1/2**, plus Sherlock ControlMaster; preserved them. All four initial Herdr setup/status checks passed. A later skampere1 agent-list probe timed out, so agent control remains unverified.

**Sherlock** refused one SSH attempt (1.08 s); its existing private command bridge successfully executed `hostname` and found Herdr. **FarmShare** refused one attempt (4.80 s). Neither refusal was retried; their profiles remain unverified. One sequencing mistake briefly overlapped mercury2 setup and the Sherlock probe; later calls were serialized.

Local Herdr startup/listing passed. All six profiles are now disabled; final `herdr machine status --json` confirms this. Enable one selected profile for a one-shot command, then disable it. Human authentication is still needed for the refused SSH routes.

**Artifacts:** [launcher](../scripts/pi_local.py), [profile](pi-local-models.example.json), [installed skill source](../skills/pi-local-herdr/SKILL.md), [unmerged PR #87](https://github.com/brando90/agents-config/pull/87); prior Pi note: [PR #86](https://github.com/brando90/agents-config/pull/86). Step logs and receipts: `~/.local/share/pi-local-setup/10-22-2026/`.

**TLDR-end:** [agents-config: local Pi and Herdr] Local fallback verified; remote profiles saved with authentication and control limits.
