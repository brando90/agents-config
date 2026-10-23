# Shared dotfiles and pane shortcuts

**Doc link:** <https://github.com/brando90/agents-config/blob/main/dotfiles/README.md>

**TLDR:** `agents-config` is now the canonical repository for shared agent instructions, dotfiles and app shortcuts; do not add new configuration to `brando90/.dotfiles`. Cursor and Ghostty running Herdr share Control+Command+Down/Right for splits, keeping Herdr's machines-and-agents sidebar intact.

## One shortcut vocabulary

| Action | Cursor editor groups | Ghostty running Herdr |
|---|---|---|
| Split below | Control+Command+Down | Control+Command+Down |
| Split right | Control+Command+Right | Control+Command+Right |
| Focus left/down/up/right | Control+Option+Command+arrow | Control+Option+Command+arrow |

Cursor's existing Control+Command+Down shortcut is the anchor. Ghostty translates these chords to Herdr's existing Control+B prefix commands (`-`, `v`, `h`, `j`, `k`, `l`); this avoids depending on Command-key encoding inside a terminal. No Herdr restart or key changes are needed. Mouse capture and copy-on-select remain unchanged.

**Scope:** Cursor commands split editor groups, not its integrated terminals or agent chat panels. Ghostty translation is intended for Herdr: outside Herdr it sends Control+B and a character to the foreground program, not a native Ghostty split. The shared split keys replace Ghostty's default split-resize bindings on those two chords. Native Command+D / Command+Shift+D remain unchanged and split Ghostty itself; they do not preserve a single Herdr sidebar.

## Install and reload

```bash
python3 ~/agents-config/scripts/install_dotfiles.py          # preview
python3 ~/agents-config/scripts/install_dotfiles.py --apply  # install
```

The installer preserves unrelated settings and comments, appends a marked Cursor override block, and adds a Ghostty `config-file` reference to the tracked fragment. Re-running is idempotent. Existing files are backed up privately under `~/.local/state/agents-config/dotfiles/backups/`. Credentials and unrelated live settings are not imported into Git.

Cursor watches its keybindings file. In Ghostty press **Command+Shift+comma** to reload configuration, then test the split keys inside Herdr. Configuration validation is not proof of live key delivery; confirm that only the right pane area splits and the sidebar stays singular. Reloading does not restart agents. Control+B followed by minus remains a fallback.

To undo, remove the marked blocks from the live Cursor and Ghostty files, or restore the private backups (taking care not to overwrite newer edits). No shell startup files are installed by this command.

## Legacy migration — 10-23-2026

All 14 files tracked at `.dotfiles` revision `86f080658c572fcaa09b15fe1930c084332b93cf` were copied byte-for-byte to `legacy/`, including hidden shell files, editor configuration, setup scripts, original README and MIT license. `legacy-manifest.json` records the source revision and SHA-256 checksums; the installer verifies every checksum. The old GitHub repository retains its complete commit history as a read-only archive after the migration notice is published.

**Legacy does not mean active:** these older scripts include machine-specific paths and historical package choices. Preserve them as references; do not source or install them wholesale over the current Mac or remote hosts. New maintained configuration belongs under `~/agents-config/dotfiles/` (or an existing app-specific `config/` directory), with an explicit installer and host verification. Secrets stay outside Git.

Only this Mac's Cursor/Ghostty configuration is installed by this task. Remote hosts and other Macs are not implicitly changed, and running agents do not reload their instruction files merely because this repository is updated.
