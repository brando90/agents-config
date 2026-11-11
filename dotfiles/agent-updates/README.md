# Mac agent tools: automatic updates

**Doc link:** <https://github.com/brando90/agents-config/blob/main/dotfiles/agent-updates/README.md>

**TLDR:** One locked background job maintains installed agent command-line interfaces (CLIs); desktop applications keep their native automatic updaters. This Mac is enrolled. Routine updates need no manual command, account change, or forced desktop restart.

## Schedule and installation

The existing `com.brando90.agent-cli-updates` LaunchAgent runs at login, daily at **10:17 local time**, and hourly. Successful per-tool checks remain fresh for 24 hours; failed or deferred tools become eligible again after one hour. A normal pass has a 900-second execution budget plus brief timeout cleanup. Sleep, logout, and network outages can delay a check.

```bash
# Preview; does not write files or start updates:
python3 ~/agents-config/scripts/install_agent_updates.py
# Install preferences, private backups, launcher, and enabled LaunchAgent:
python3 ~/agents-config/scripts/install_agent_updates.py --apply
```

The installed `~/.local/bin/auto-update-agent-clis` calls the canonical Python source in `~/agents-config`. The Mac branch of `scripts/auto-update-tools.sh` delegates to the same job/lock rather than starting a competing Node.js package-manager (`npm`) installation. The Linux route, including the Stanford Network Analysis Project (SNAP) cluster, is unchanged. No remote host is enrolled by this Mac installer.

The installer preserves unrelated settings, comments, existing configuration links, and unrelated LaunchAgent fields. Reapplying is idempotent. It waits for an in-flight updater before reloading the job; it does not stop that updater midway through an installation.

## Current command-line coverage

Only installed commands found on the updater's search path are enrolled. Aliases use the same underlying installation; inactive copies in other prefixes are not silently replaced. `--list` is the authoritative live inventory.

| Route | Tools |
|---|---|
| Native maintenance command | Pi, Claude Code, Cursor Agent, Herdr, Oh My Pi, Droid, Kimi, Hermes, Antigravity (`agy`), Grok, Goose, Cortex, Harn, Kimchi, Stakpak, VT Code, Pool, OpenClaw (legacy-version safeguard below) |
| Actual active npm prefix | Codex, Copilot, Kilo, Qoder CLI, Qwen, Mastra Code, OpenCode, Auggie |
| Existing Python `uv` tool environment | Crow CLI, Fast-agent, Minion Code, Mistral Vibe |
| Existing Homebrew installation | Devin CLI |
| Supported synchronous launcher update | Muse |
| Vendor-managed startup update | Junie, through its official managed shim |
| Explicitly preserved integration builds | `amp-acp`, `corust-agent-acp`, `minimax-code-repaired` |

The deprecated Gemini CLI is not installed or updated. Gemini's desktop application is separate. Evaluation tools such as Harbor and Valkyrie, and the separately installed Ollama model-serving runtime, are outside this agent-client updater.

### Compatibility and session safeguards

- Native maintenance subcommands must appear in the installed client's help before execution. Unknown positional arguments must not turn into model prompts. All commands run from a maintenance directory, not a research checkout.
- npm uses the prefix inferred from the active executable, not npm's potentially different default prefix. Prerelease installations are retained rather than silently switched to stable. Package metadata and executable health are checked after updating.
- Python `uv` upgrades bind both the tool-store directory and the exported-command directory to the active installation, rather than adopting a different shell default.
- Mastra Code and the Python tools use distribution metadata plus `--help` because some do not implement `--version`. A broken client does not block its independent package manager from attempting repair on a later pass.
- Fast-agent's Agent Client Protocol (ACP) command remains `fast-agent-acp`, but its maintained distribution is **`fast-agent-mcp`**. The separate `fast-agent-acp` 0.10.54 wheel omitted its own Python module. On this Mac it was replaced by the publisher's recommended main distribution, and the command passed its help check.
- Pi runs `pi update --self --no-approve`: it does not bulk-update extensions or model catalogs, change provider selection, or rewrite the separate shared-configuration service.
- Hermes source with local changes is deferred, never stashed or reset. Its update uses `--no-gateway-restart`; Herdr does not receive `--handoff`.
- VT Code retains version pins. Its updater requires a terminal confirmation even though the wider client has a skip-confirmations flag. A bounded pseudo-terminal answers only the documented binary-install question; no forced reinstall or unpin is requested. When advertised by the installed version, `--without-desktop` prevents an additional desktop-app installation prompt.
- Stakpak is deferred while it is running because its native updater can restart autopilot. If its vendor release-cache endpoint fails, the job checks the official GitHub release. An already-current binary is reported with that caveat. A newer release uses the publisher's matching Mac archive, its supplied checksum, staged version verification, and atomic replacement with rollback; Homebrew-managed installations stay with Homebrew. Only the binary member is read from the archive, not arbitrary archive paths.
- OpenClaw uses `--no-restart` without accepting downgrades or changing channels. Pre-July releases are deferred: the vendor requires a one-time **2026.9.5** bridge migration with its background Gateway service stopped. This Mac's **2026.4.24** installation was restored after the newer Doctor refused its legacy configuration. Configuration bytes and the running Gateway were preserved; this is **not** an updated client. Routine updates can proceed after the documented migration, without forcing that maintenance window now.
- Junie's installed managed shim applies pending updates on ordinary launch. A bare symlink to an old version bypasses that mechanism and is not accepted as proof that startup updates work. The official shim was restored on this Mac; its accounts and model configuration were not replaced.

The job submits no model prompts and contains no credential values. `--force` bypasses freshness only, not the installation/session safeguards.

## Desktop applications

| Application | Verified update mechanism / preference |
|---|---|
| Cursor, Devin, Antigravity IDE, Visual Studio Code, Visual Studio Code Insiders | `update.mode: "default"` in their user settings |
| Zed | `auto_update: true`; no competing Homebrew cask replacement |
| Antigravity | Native storage preference `autoCheckForUpdates: "true"`; its updater downloads automatically and installs on ordinary quit |
| Claude | User preference `disableAutoUpdates: false`; managed device policy is not overridden |
| ChatGPT | Its installed Sparkle updater has automatic checks and installation enabled, using the bundle's actual identifier |
| Gemini | Registered with Google's existing hourly updater; verified loaded with a successful last exit |
| Grok Bot | Existing native periodic updater and idle-update mechanism retained |
| Manus Studio | Existing native periodic checks/downloads and task/recording-aware installation retained |

These settings were checked against installed application code or supported settings, not guessed preference names. No app was forced to quit or relaunch. A vendor may finish an update on normal quit/reopen or when its tasks are idle; enabling automatic updates is **not** a claim that every desktop binary has already been replaced.

## Verification and private records

Verified on **11-11-2026**: Pi is **1.5.2** (previously 1.4.0), Junie is **26.11.1 / build 4020.7** with its managed shim, and the scheduled job completed with exit code **0**. The final inventory has **36** command-line entries, with no failed latest receipt; legacy OpenClaw is explicitly deferred. All **45** updater/installer tests and **14** dotfiles regression tests passed. Live passes updated other clients and exercised recovery from unsupported version flags, terminal-only confirmation, and the broken Fast-agent wrapper. The Stakpak release fallback downloaded and checked the current official archive; its binary remained byte-identical. Unit tests separately exercise newer-binary replacement, checksum rejection, rollback, and archive-path protection.

```bash
~/.local/bin/auto-update-agent-clis --list
~/.local/bin/auto-update-agent-clis                     # freshness-aware pass
~/.local/bin/auto-update-agent-clis --only pi --force   # optional immediate check
launchctl print "gui/$(id -u)/com.brando90.agent-cli-updates"
python3 -m unittest discover -s ~/agents-config/tests -p 'test_agent_updates.py' -v
```

By default, private records are under `~/.local/state/agent-cli-updates/`. A custom `XDG_STATE_HOME` relocates updater receipts and per-tool logs, not the shared lock or installed scheduler logs:

- `status.json`: latest recorded attempt per tool, including its status and log path. Historical entries can remain after a route is retired; compare with `--list` for current enrollment.
- `runs/<timestamp>/`: per-tool output and a receipt for each pass that attempted work. A fully fresh pass exits without downloading packages.
- `update.log`, `launchd.out.log`, `launchd.err.log`: maintenance and scheduler logs.
- `update.flock`: the common lock for updates and installer reloads, even when receipt directories differ.
- `backups/`: original preference/configuration files, including values needed to undo an edit without replacing newer unrelated work.
- `recoveries/11-11-2026/`: installation-repair and release-verification evidence.

`checked`, `updated`, `on-launch`, `preserved`, `deferred`, and `failed` are distinct outcomes. A version probe or vendor-managed route is not presented as an installed update. Failures are recorded and retried, not suppressed as success. Do not publish these private records or full live preference files.

For intentional maintenance, the existing `AGENT_CLI_UPDATE_SKIP=1` environment setting suppresses both entry points in that environment. To remove the scheduled job, wait until `launchctl print` shows it is not running, then boot out its exact service and disable it; do not terminate an active package installation. Preferences can be restored selectively from the private backups. Leave the canonical checkout in place because the installed launcher uses it.

Implementation: [updater](../../scripts/auto_update_agent_apps.py), [installer](../../scripts/install_agent_updates.py), [tests](../../tests/test_agent_updates.py). Vendor references: [Junie installer](https://junie.jetbrains.com/install.sh), [Fast-agent installation](https://github.com/evalstate/fast-agent#readme), [Stakpak releases](https://github.com/stakpak/agent/releases), [VT Code update handler](https://github.com/vinhnx/vtcode/blob/0.182.0/src/cli/update.rs), [OpenClaw legacy migration](https://docs.openclaw.ai/install/updating#upgrading-very-old-versions).

**TLDR-end:** [agents-config: automatic updates] This Mac maintains ordinary agent tools through a single scheduled updater and supported desktop mechanisms. Pinned integrations, accounts, model selections, and active desktop sessions remain separate from software maintenance.
