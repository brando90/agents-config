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
python3 ~/agents-config/scripts/install_dotfiles.py --diff   # preview exact changes
python3 ~/agents-config/scripts/install_dotfiles.py --apply  # install
```

The installer preserves unrelated settings and comments, appends a marked Cursor override block, and adds a Ghostty `config-file` reference to the tracked fragment. Re-running is idempotent. Existing files are backed up privately under `~/.local/state/agents-config/dotfiles/backups/`. Credentials and unrelated live settings are not imported into Git.

Cursor watches its keybindings file. In Ghostty press **Command+Shift+comma** to reload configuration, then test the split keys inside Herdr. Configuration validation is not proof of live key delivery; confirm that only the right pane area splits and the sidebar stays singular. Reloading does not restart agents. Control+B followed by minus remains a fallback.

To undo, remove the marked blocks from the live Cursor and Ghostty files, or restore the private backups (taking care not to overwrite newer edits). No shell startup files are installed by this command.

## Legacy migration — 10-23-2026

All 14 files tracked at `.dotfiles` revision `86f080658c572fcaa09b15fe1930c084332b93cf` were copied byte-for-byte to `legacy/`, including hidden shell files, editor configuration, setup scripts, original README and MIT license. `legacy-manifest.json` records the source revision and SHA-256 checksums; the installer verifies every checksum. The old GitHub repository retains its complete commit history as a read-only archive after the migration notice is published.

**Legacy does not mean active:** these older scripts include machine-specific paths and historical package choices. Preserve them as references; do not source or install them wholesale over the current Mac or remote hosts. New maintained configuration belongs under `~/agents-config/dotfiles/` (or an existing app-specific `config/` directory), with an explicit installer and host verification. Secrets stay outside Git.

Only this Mac's Cursor/Ghostty configuration is installed by this task. Remote hosts and other Macs are not implicitly changed, and running agents do not reload their instruction files merely because this repository is updated.

## Zed — 10-26-2026

`dotfiles/zed/` holds the shared Cursor preset (`base_keymap: "Cursor"`), keyboard bindings, panel layout and look: theme mode Light with Gruvbox Light (dark stays One Dark), as set in Zed > Settings > Appearance > Theme on 10-27-2026. The second look he uses, Gruvbox Dark Soft, is a profile with the same layout and keybindings. Cmd+B toggles the left file sidebar immediately, regardless of whether the editor or tree has focus. Cmd+Shift+E focuses the project tree. Cmd+Alt+B toggles the right agent dock; Cmd+E toggles Zed's separate Threads sidebar (Cursor's Toggle Agent layout), and Cmd+Alt+S is Save All, as in Cursor. The rest of Cursor's shortcuts are mapped too: see [`zed/README.md`](zed/README.md) for the table and the few Cursor shortcuts Zed cannot do.

**Install the bindings and layout together.** Cmd+B uses `workspace::ToggleLeftDock`, with `project_panel.dock` set to `left` and `agent.dock` set to `right`. `agent.threads_sidebar.auto_open` is `false` so opening another project does not automatically expose the extra Threads column. If that column is already visible, hide it once with Cmd+E; it is separate from the left dock. Keep Vim mode and unrelated host preferences when merging these settings.

`install_dotfiles.py` installs both files into `~/.config/zed/`, with a private backup under `~/.local/state/agents-config/dotfiles/backups/` before any change. It is merge-safe and idempotent. `keymap.json` goes in as one marked `agents-config pane shortcuts` block that keeps your own bindings and comments. From `settings.json` it sets only `base_keymap`, `theme` (mode `light`, light `Gruvbox Light`, dark `One Dark`), `icon_theme` (system mode, Zed (Default)), one settings profile named `Gruvbox Dark Soft` (the same look with Gruvbox Dark Soft as the light-mode theme; pick it in Zed's settings-profile selector, and your other profiles stay as they are), `agent.dock`, `agent.threads_sidebar`, `project_panel.dock`, `git_panel.dock` and `outline_panel.dock`. Vim mode, fonts, agent servers and every other preference stay as they are, and a second run reports `Unchanged`. Comments inside a rewritten top-level value (for example inside `agent`) are not kept, so use the backup if you need them. Secrets stay outside Git.

Test without touching your real files: `python3 scripts/install_dotfiles.py --home "$(mktemp -d)" --diff`.

Verify with a real folder and a file open: focus the editor, press Cmd+B once to hide the tree and once to restore it; then repeat while the tree has focus. Every press must change sidebar visibility, with no intermediate focus-only step. `project_panel::Toggle` and `project_panel::ToggleFocus` do not reproduce this behavior. An empty workspace has no directory tree to display.
