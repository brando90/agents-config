# MacBook Pro: Pi and Herdr — 10-22-2026

**Doc link:** <https://github.com/brando90/agents-config/blob/main/machine/mac-pi-herdr-10-22-2026.md>

**Google Doc:** <https://docs.google.com/document/d/1VkkBXmcezvHvq_XRrV1gw4Q_yPZ6Ni73-efcMhkoCm4/edit>

**TLDR:** `pi-gemini` is installed for VeriBench with Allen's existing key; `pi-local` remains the free fallback. Gemini connectivity, local repair and 17 Herdr integrations are verified; remote-control limits remain.

## Install and use

1. Verified **M1 Max / 64 GiB RAM**. Approved removal of an unused 2023 model cache recovered 19.7 GiB from 5.3 GiB free.
2. Installed **Pi 1.4.0**, **Ollama 0.40.8** and **Herdr 0.9.5** under `~/.local`, without sudo. Pi uses `npm install -g --prefix ~/.local @earendil-works/pi-coding-agent@1.4.0`; official Ollama/Herdr release checksums were verified.
3. `pi-local` uses Qwen3.5 9B Q4_K_M (6.6 GB), a loopback-only Ollama LaunchAgent, disabled cloud features and 32,768-token context. Ollama's local identity file was approved.
4. `pi-gemini` loads `~/keys/gemini_allen_key.txt` only at runtime and uses a separate profile. Default: Gemini 3 Flash Preview, minimal thinking, 8,192 output tokens. Use `PI_GEMINI_MODEL=gemini-3.1-pro-preview pi-gemini` to select another Gemini model. Brando authorized VeriBench use; prompts/context go to Google and usage follows the key's project. No key was copied or created; billing settings were not changed.
5. From a repository, run either launcher. For local handoff: `pi-takeover CHECKPOINT.md -p`; quota recovery: `pi-resilient CHECKPOINT.md --error-log quota.log -p`. Stop the previous writer first. Switching is explicit; these start fresh checkpoint-based sessions.

## Verification and timings

Local repair: **2/10 → 10/10 passing**, Pi **40.984 s**, independent rerun **0.059 s**, tests unchanged. This single disposable task is not the Air benchmark. [Frozen local proof](pi-local-proof-10-22-2026.json).

Gemini's prior live Pi test returned **PONG in 1.58 s**, **53 input / 2 output tokens**; connectivity only. The new wrappers passed **15 deterministic checks**. Both installed launchers emitted session/idle events through the Herdr hook to a local test socket, without generation. [Gemini proof](pi-gemini-proof-10-22-2026.json).

Model download/registration: **48.9 min** (30-second polling resolution). Multipart stalls were recovered with a **4:30** single-stream download, verified by SHA-256. A 27B download was abandoned before inference. Install durations were not separately measured.

## Herdr and remote outcome

All **17 requested integrations** now report current, including the initially missing clients. Both Pi launchers load Herdr's Pi hook. Full session restore was not tested. [Integration receipts](herdr-integrations-proof-10-22-2026.json).

Existing Secure Shell (SSH) aliases preserve whale jumps for **skampere1/2, mercury1/2** and Sherlock ControlMaster. Four initial Herdr status checks passed; later skampere1 agent-list control timed out. **Sherlock** refused once (**1.08 s**), but its private command bridge worked. **FarmShare** refused once (**4.80 s**). During the initial manual phase, refusals were not retried; one brief mercury2/Sherlock overlap was recorded. A subsequent explicit skampere1 agent-list check succeeded and reported Pi idle; sending work and full remote control through Herdr remain unverified.

Brando subsequently authorized **all six profiles enabled for automatic connection**, superseding the initial one-at-a-time mode. Added skampere3 on the follow-up request and verified it reachable: **seven saved profiles, five SNAP nodes reachable**; Sherlock and FarmShare still return authentication errors. [Latest machine receipt](herdr-machines-proof-10-22-2026.json). Passwords, keytabs and login prompts were untouched.

Persistent Herdr mouse capture and copy-on-select are enabled; validation passed and the live server accepted reload without diagnostics. iTerm2 profile and live gesture checks remain unverified because computer control denied iTerm2 access. [Mouse/clipboard setup and agent error/fix guide](herdr-mouse-agent-repairs-10-22-2026.md).

**Artifacts:** [launchers](../../scripts/pi_gemini.py), [skill](../../skills/pi-local-herdr/SKILL.md), [PR #87](https://github.com/brando90/agents-config/pull/87) (ported to main). Local steps/receipts: `~/.local/share/pi-local-setup/10-22-2026/`.

**TLDR-end:** [VeriBench: Pi and Herdr] Gemini launcher installed; free local fallback preserved; integrations installed and remote limitations documented.
