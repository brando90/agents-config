# Pi command parity across SNAP, Sherlock and FarmShare — 10-22-2026

**Doc link:** <https://github.com/brando90/agents-config/blob/codex/mac-pi-herdr-10-22-2026/machine/pi-host-parity-10-22-2026.md>

**Google Doc:** <https://docs.google.com/document/d/1VkkBXmcezvHvq_XRrV1gw4Q_yPZ6Ni73-efcMhkoCm4/edit>

**TLDR:** All five Stanford Network Analysis Project (SNAP) nodes resolve Pi 1.4.0 through one shared launcher and reach the existing Qwen3-Coder 30B service. Sherlock and FarmShare remain unverified: host-key verification stopped the single noninteractive access attempt for each, and Sherlock's existing runner is offline.

## What failed and what changed

The reported `pi: command not found` was not reproduced in fresh login or interactive shells: Pi 1.4.0 was already present on all five nodes. The exact original shell environment was unavailable. An older PATH is a likely explanation, not a proven cause. The shared command directory had no `pi` entry, leaving older shells dependent on the newer node-local PATH entry. Ubuntu's suggested `apt install pi` is unrelated to the coding agent.

Added `/dfs/scratch0/brando9/bin/pi`, backed up and repointed each node's `~/.local/bin/pi` to it, and verified the command on each host. The launcher resolves the node-local npm package, preserves arguments and provider overrides, and loads the existing Node version manager when needed. Pi 1.4.0's package requires Node >=22.19.0; the nodes have 24.14.0. No hardcoded Node-version directory was added to PATH.

The old `snap-qwen/pi-qwen3.6-27b` route also failed: skampere1 no longer had a listener on port 18127, and the other nodes had no working local backend there. Two existing user-owned vLLM services on skampere1 advertised `qwen3-coder-30b`. Reused the service on loopback port 18201, adding a distinct `snap-coder` provider and making it the default for fresh sessions. Previous model entries were preserved, with private settings backups. This is a model change, not a renamed 27B model.

skampere1 uses port 18201 directly. The other four nodes use a loopback-only SSH forward on port 18127 to skampere1:18201. The launcher checks the expected model catalog, reuses a working route, and makes at most one bounded tunnel attempt when needed. Host-key checking remains enabled. No provider key was loaded, paid inference invoked, or new GPU workload started. Tool execution and file edits stay on the node running Pi; inference is on skampere1.

Two tunnel implementation errors were repaired: an overlong Unix control-socket path and a detached SSH process retaining output pipes. Final sockets use short names in host-specific directories, with a nonblocking setup lock and detached standard streams. The earlier failed attempts remain in private receipts.

## Verification and limits

| Host | Command | Configured model route |
|---|---|---|
| skampere1 | Pi 1.4.0 | Qwen3-Coder 30B catalog verified |
| skampere2 | Pi 1.4.0 | Qwen3-Coder 30B catalog verified |
| skampere3 | Pi 1.4.0 | Qwen3-Coder 30B catalog verified |
| mercury1 | Pi 1.4.0 | Qwen3-Coder 30B catalog verified |
| mercury2 | Pi 1.4.0 | Qwen3-Coder 30B catalog verified |
| Sherlock | Unverified | SSH host-key verification failed; no retry; runner offline |
| FarmShare | Unverified | SSH host-key verification failed; no retry |

Five offline launcher tests pass: version/help/catalog checks do not require SSH, explicit other providers and literal arguments survive, and a missing package fails clearly. Syntax and instruction-link checks pass.

The first skampere3 repair changed only a disposable Python implementation; independent verification passed 3/3 unchanged tests. Pi did not exit within 90.016 seconds and was stopped. That run proves file editing and test correctness, not successful completion. An isolated follow-up disables unrelated context discovery and Model Context Protocol (MCP) connections for this disposable test only; it exited successfully in 54.733 seconds, and an independent rerun passed 3/3 unchanged tests. Native Pi logs confirmed the actual provider/model `snap-coder/qwen3-coder-30b`, file-tool calls and normal completion. This is one small disposable repair, not a broad coding benchmark.

## Recovery without reinstalling

In an already-open SNAP shell:

```bash
export PATH="/dfs/scratch0/brando9/bin:$HOME/.local/bin:$PATH"
hash -r
pi --version
pi --check-local
pi
```

`pi --check-local` performs the configured local-route preflight without inference. A successful catalog check is not a coding-task result. Resume an old Pi session only with awareness that its stored provider/model may differ from the fresh-session default. Model-server availability and authentication can expire; the wrapper reports failures rather than buying access or starting competing GPU jobs.

For Sherlock/FarmShare, complete normal host-key verification, password and Duo yourself and retain a shared SSH connection. Once connected, an agent can run `bash scripts/install_pi_remote.sh` from this branch; it needs the host's existing supported Node runtime, uses the official npm package with `--ignore-scripts`, and installs under the home directory. It preserves shell files and settings and does not copy credentials or assume a SNAP model route exists. GPU inference on those clusters must follow their scheduler policies. Do not report either host installed until its own version, fresh-shell and model checks succeed.

Private receipts: `~/.local/share/pi-local-setup/10-22-2026/pi-parity-*.json` on the Mac. Keep these separate from public documentation and preserve the unmerged pull request.
