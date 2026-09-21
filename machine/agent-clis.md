# Agent coding CLIs (Cursor, Grok, Antigravity)

**Doc link:** <https://github.com/brando90/agents-config/blob/main/machine/agent-clis.md>

**TLDR:** One installer, `~/agents-config/scripts/install_agent_clis.sh`, puts Cursor Agent (`agent`), Grok Build (`grok`), and Antigravity (`agy`) on both Macs and every SNAP node. Google-model coding-agent work uses `agy` with a Google account. The deprecated `gemini` npm CLI is not installed. Grok also ships a binary named `agent`; Cursor keeps that name.

## What lives where

| Command | Product | Install | Auth (subscription, not a provider API key) |
|---|---|---|---|
| `agent` / `cursor-agent` | Cursor Agent CLI | `curl https://cursor.com/install -fsS \| bash` | `agent login` (browser). Status: `agent status`. |
| `grok` | Grok Build (SpaceXAI) | `curl -fsSL https://x.ai/cli/install.sh \| bash` | `grok login` (browser). Do **not** export `XAI_API_KEY`. |
| `agy` / `antigravity` | Antigravity CLI (Google) | `curl -fsSL https://antigravity.google/cli/install.sh \| bash` | First run signs into a Google account. On SSH: printed URL + paste-back code. Do **not** export `GEMINI_API_KEY`. |
| `claude` / `clauded` | Claude Code | existing NVM / native installer | existing profiles (`~/.claude`, `~/.claude-vals`, `~/.claude-su`) |
| `codex` / `codexd` | Codex | existing NVM / brew | existing profiles (`~/.codex`, `~/.codex-vals`, `~/.codex-su`) |

Do **not** install `@google/gemini-cli`. Hard Rule 7/9: Antigravity replaces that CLI. The consumer **Gemini.app** GUI on a Mac is unrelated and may stay. If an old `gemini` binary is already on a Mac, leave it; do not copy it to SNAP.

`origin` is Cursor's git-forge CLI (`origin.cursor.com`), not a coding agent. Skip it unless a Cursor-hosted repo is in use. Docs: https://cursor.com/docs/origin/cli

## Why Grok must not own `agent`

Grok's official installer links **both** `grok` and `agent` into `~/.local/bin` and prepends `~/.grok/bin` to `PATH`. Cursor's CLI is also named `agent`. The shared installer:

1. Runs Grok's installer with `SHELL=` so it does not rewrite `.bashrc` / `.zshrc`.
2. Symlinks **only** `grok` onto `PATH`.
3. Restores Cursor's `agent` / `cursor-agent` if Grok overwrote them.

Never put `$HOME/.grok/bin` ahead of Cursor on `PATH`.

## Install / update

On **this Mac, Sanmi's Mac, or any SNAP node**:

```bash
git -C ~/agents-config pull --ff-only
bash ~/agents-config/scripts/install_agent_clis.sh
bash ~/agents-config/scripts/install_agent_clis.sh --status
```

`--update` is the same idempotent path (safe from the SessionStart hook). `--status` prints versions and login state without secrets.

On SNAP the script detects `/dfs/scratch0/brando9`, installs binaries under that DFS home, and writes wrappers in `/dfs/scratch0/brando9/bin` (`agent`, `cursor-agent`, `grok`, `agy`, `antigravity`). One node is enough; the other direct-SSH nodes pick the wrappers up from the shared `PATH`. From a Mac, SSH to the FQDN (`skampere1.stanford.edu`); short names are not in `~/.ssh/config`. `snap_health.sh` now appends `.stanford.edu` for you.

`~/agents-config/scripts/auto-update-tools.sh` calls this installer after the Claude Code / Codex NVM updates.

## Login (human browser once per machine class)

Do not paste tokens into chat. Do not author API-calling code.

| Host | Cursor | Grok | Antigravity |
|---|---|---|---|
| Mac | `agent login` | `grok login` | `agy` (opens browser) |
| SNAP SSH | `NO_OPEN_BROWSER=1 agent login` then open the printed URL locally | `grok login` (device/URL flow if printed) | `agy` prints a URL; paste the code back into the SNAP tty |

Verified 09-20-2026: this Mac and all five canonical SNAP nodes can complete real calls through all three clients. Cursor uses `brandojazz@gmail.com`; Grok uses `brando@vals.ai`; Antigravity uses the existing approved Google login. The SNAP acceptance check returned the requested token for **15/15 calls** (three clients × five nodes). Credentials remain private, mode `0600`, and are never committed.

For SNAP recovery, authenticate one node through the browser/device flow, then copy only the three clients' private credential files to the other node-local homes and verify them:

```bash
SOURCE_HOST=mercury1 bash ~/agents-config/scripts/sync_agent_cli_auth_snap.sh
bash ~/agents-config/scripts/verify_agent_clis_snap.sh
```

For Sanmi's Mac, pull this repository and run `install_agent_clis.sh` as above. Then run `agent login`, `grok login --device-auth`, and `agy`; complete each browser login using Sanmi's intended subscription accounts. Run one bounded print-mode call through each client. Do not copy Brando's Mac Keychain, browser profile, or private credentials to Sanmi's computer. If Sanmi is administering these same SNAP nodes, the existing node-local credentials should already pass `verify_agent_clis_snap.sh`; refresh them from an authenticated SNAP source only when status or a real call fails.

Full-access SNAP launchers stay the Claude/Codex ones in Trigger Rule 51. Cursor/Grok/Antigravity are extra eligible executors under Trigger Rule 48 once the target host shows an authenticated client — verify with `--status` before dispatching work onto them.

## Meta Muse Code — optional, no new spending

Install on a Mac or each compute node with:

```bash
bash ~/agents-config/scripts/install_muse_cli.sh
bash ~/agents-config/scripts/install_muse_cli.sh --check
```

The command is `muse`. This separate installer uses Meta's official installer,
preserves shell startup files, and checks version plus the local `echo` provider
in an empty temporary workspace. It does not authenticate, invoke a model,
buy a subscription, add a payment method, or enable metered usage. Add
`~/.local/bin` to PATH if that host does not already include it.

For Muse, install the binary in each node's local `~/.local/bin`; keep each
host's credentials local. This avoids depending on the distributed filesystem
for binary startup. A version check is not an authentication or model-capability
test. Existing Cursor/Grok/Antigravity paths are unchanged.

Verified September 20, 2026: Muse Code `1.3.0 (1.3.0-R3401.1)` installed on
Brando's Mac and `skampere1`, `skampere2`, `skampere3`, `mercury1`, `mercury2`.
Sanmi's Mac was unreachable by its known network name; run the same script
there when available. `muse login` uses the Meta browser/device flow. Brando's
browser account was recognized, but authentication stopped at SMS two-factor
verification. No authenticated inference or free account allowance is claimed.

Mercury initially rejected the offline check when its workspace was under
`/tmp`, reporting that temporary tool output was inside the workspace or
repository. The check script uses an explicit disposable workspace under the
user's home and a separate temporary runtime under `/var/tmp`; this passed
on Mercury without disabling Muse's protections.

Meta advertises Muse Code subscriptions starting at $5/month as well as metered
Model API usage. The consumer Muse app's free allowance does not establish a
free Muse Code entitlement. The user requested no payment: leave Muse out of
unattended dispatch until an applicable no-charge allowance is verified. Do not
select the Contributor model merely to lower cost: Meta says its inputs and
outputs may be used for model training. Never submit private benchmark material
to that tier without the applicable authorization.

Official references: [overview](https://dev.meta.ai/docs/overview),
[authentication](https://dev.meta.ai/docs/muse-code/auth),
[plans](https://dev.meta.ai/products/muse-code), and
[pricing/data tiers](https://dev.meta.ai/docs/pricing-rate-limits).

**TLDR-end:** Muse is installed as an optional client on the six reachable hosts;
offline checks establish startup only. Sign-in and no-charge entitlement remain
unverified; paid usage is not authorized.

## Other agent documentation

- Cursor CLI: https://cursor.com/docs/cli/overview
- Cursor auth: https://cursor.com/docs/cli/reference/authentication
- Grok Build: https://docs.x.ai/build/overview
- Antigravity install/auth: https://antigravity.google/docs/cli/install/
- Claude/Codex multi-account wrappers: [`~/agents-config/workflows/multi-account-agent-clis.md`](../workflows/multi-account-agent-clis.md)
