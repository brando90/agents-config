# Zed: Cursor shortcut parity

**Doc link:** <https://github.com/brando90/agents-config/blob/main/dotfiles/zed/README.md>

**TLDR:** Zed runs with `base_keymap: "Cursor"` plus `keymap.json`, so the shortcuts Brando uses in Cursor do the same thing in Zed. The table lists every Cursor shortcut checked, the Zed action behind it, and where the binding comes from. The last section lists what Cursor has that Zed cannot do.

**Sources.** Cursor's shortcut page (<https://cursor.com/docs/configuration/kbd>), which names VS Code's keybindings as Cursor's baseline; VS Code's macOS defaults; Brando's own Cursor bindings (`dotfiles/cursor/keybindings.json`). Zed side: Zed's `default-macos.json` and its Cursor preset (`assets/keymaps/macos/cursor.json`), with every action name in `keymap.json` checked against Zed's published action list (<https://zed.dev/docs/all-actions>). **Not yet run in Zed on a Mac.** The bindings rest on Zed's rule that the deeper context wins and the user keymap loads last; the checks at the end of this file confirm them.

**Install:** `python3 ~/agents-config/scripts/install_dotfiles.py --apply` (see `../README.md`). The installer adds `keymap.json` as one marked block and keeps your own bindings.

Where the binding comes from: **Zed** = Zed's default, **preset** = Zed's Cursor preset, **here** = this `keymap.json`.

## Cursor-specific (agent and chat)

| Cursor shortcut | Cursor action | Zed binding and action | From |
|---|---|---|---|
| Cmd+I, Cmd+L | Toggle side panel | agent::ToggleFocus; inside the chat input, workspace::ToggleRightDock | preset, here |
| Cmd+L, Cmd+Shift+L in a file | Add selection to chat | agent::AddSelectionToThread | preset |
| Cmd+Shift+I | Toggle side panel (Zed's preset; not on Cursor's page) | agent::ToggleFocus; inside the chat input, workspace::ToggleRightDock | preset, here |
| Cmd+K | Inline edit (editor and terminal). Cursor's page lists Cmd+K next to Cmd+L (side panel, add selection); Zed's preset keeps the inline edit that Cursor is known for, and this file does not change that | assistant::InlineAssist | preset |
| Cmd+E | Toggle Agent layout | multi_workspace::ToggleWorkspaceSidebar (Zed's Threads sidebar; nearest match; `workspace::UseAgenticLayout` and `UseClassicLayout` exist but are two actions, not a toggle) | here |
| Cmd+. | Mode menu | agent::ToggleProfileSelector | preset, here |
| Cmd+/ | Loop between AI models | agent::CycleFavoriteModels | here |
| Cmd+Opt+/ | Model toggle | agent::ToggleModelSelector | Zed |
| Cmd+Shift+J | Cursor settings | agent::OpenSettings | preset |
| Shift+Tab | Rotate between Agent modes | agent::CycleModeSelector | Zed |
| Cmd+N, Cmd+R | New chat | agent::NewThread | Zed, preset, here |
| Cmd+[ , Cmd+] | Previous, next chat | multi_workspace::PreviousThread, NextThread | here |
| Cmd+W | Close chat | workspace::ToggleRightDock (hides the panel; the thread stays) | preset, here |
| Cmd+Enter | Force send message (Zed's Cmd+Enter was send and follow; with Zed's `use_modifier_to_send` on it no longer sends normally) | agent::SendImmediately | here |
| Cmd+Enter with changes | Accept all changes | agent::KeepAll | preset, here |
| Cmd+Shift+Backspace with changes | Reject all changes | agent::RejectAll (the preset puts it on Cmd+Backspace; both work) | preset, here |
| Cmd+Shift+Backspace in the chat | Cancel generation | editor::Cancel (the preset's choice; Zed's own key there removes the first queued message) | preset, here |
| Return | Queue message | agent::Chat; Zed queues while the agent works (Cmd+Shift+Enter sends immediately) | Zed |
| Cmd+Shift+V | Add clipboard to input box | agent::PasteRaw | Zed |
| Tab | Accept suggestion | edit prediction accept | Zed |
| Cmd+Right | Accept next word of suggestion | editor::AcceptNextWordEditPrediction | preset |
| Cmd+R then Cmd+S | Open Keyboard Shortcuts | zed::OpenKeymap (plain Cmd+R is unbound outside the chat) | here |
| Cmd+Shift+P | Command palette | command_palette::Toggle | Zed |
| Cmd+, | General settings | zed::OpenSettings | Zed |

## Layout and navigation (VS Code baseline)

| Cursor shortcut | Cursor action | Zed binding and action | From |
|---|---|---|---|
| Cmd+B | Toggle left sidebar | workspace::ToggleLeftDock, repeated for editor and terminal focus | Zed, here |
| Cmd+Opt+B | Toggle right sidebar | workspace::ToggleRightDock | Zed |
| Cmd+Shift+E | Explorer | project_panel::ToggleFocus; in a full editor Zed's own binding reveals the file in the tree instead, left as it is | Zed |
| Cmd+J | Toggle bottom panel | workspace::ToggleBottomDock | Zed |
| Ctrl+` | Toggle terminal | terminal_panel::Toggle | Zed |
| Cmd+P | Quick open | file_finder::Toggle | Zed |
| Cmd+Shift+F | Search in files | pane::DeploySearch | Zed |
| Cmd+Shift+H | Replace in files | pane::DeploySearch with replace | Zed |
| Cmd+F, Cmd+G, Cmd+Shift+G | Find, next, previous | buffer_search::Deploy, search::SelectNextMatch, SelectPreviousMatch | Zed |
| Cmd+Opt+F | Replace in file | buffer_search::DeployReplace (Zed uses this key for its text finder) | here |
| Cmd+T | Symbol in workspace | project_symbols::Toggle | Zed |
| Cmd+Shift+O | Symbol in file | outline::Toggle | Zed |
| Ctrl+G | Go to line | go_to_line::Toggle | Zed |
| Ctrl+Shift+G | Source control | git_panel::ToggleFocus | Zed |
| Cmd+Shift+X, Cmd+Shift+D, Cmd+Shift+M | Extensions, debug, problems | zed::Extensions, debug_panel::ToggleFocus, diagnostics::Deploy | Zed |
| Cmd+Opt+S | Save all | workspace::SaveAll (the Threads sidebar used to sit here; it is now on Cmd+E) | Zed, here |
| Cmd+S, Cmd+N, Cmd+O, Cmd+Shift+N | Save, new file, open, new window | workspace::Save, NewFile, Open, NewWindow | Zed |
| Cmd+W, Cmd+Shift+W, Cmd+Shift+T | Close tab, close window, reopen tab | pane::CloseActiveItem, workspace::CloseWindow, pane::ReopenClosedItem | Zed |
| Ctrl+Tab, Ctrl+Shift+Tab | Next, previous tab (recent order) | tab_switcher::Toggle | Zed |
| Cmd+Opt+Left, Cmd+Opt+Right, Cmd+Shift+[ , Cmd+Shift+] | Previous, next tab | pane::ActivatePreviousItem, ActivateNextItem | Zed |
| Cmd+1 to Cmd+9 | Focus editor group | workspace::ActivatePane | Zed |
| Ctrl+1 to Ctrl+9 | Open tab by number | pane::ActivateItem | Zed |
| Ctrl+Cmd+Down, Ctrl+Cmd+Right | Split below, split right (Brando's Cursor keys; also bound in the editor, edit prediction and terminal, where Zed uses them for syntax-node selection and accepting predictions) | pane::SplitDown, pane::SplitRight | here |
| Ctrl+Opt+Cmd+arrows | Focus group left, down, up, right (Brando's Cursor keys) | workspace::ActivatePaneLeft, Down, Up, Right | here |
| Cmd+\ | Split editor | pane::SplitRight | Zed |
| Ctrl+- , Ctrl+Shift+- | Back, forward | pane::GoBack, pane::GoForward | Zed |
| Ctrl+` , Ctrl+Shift+` | Toggle terminal, new terminal | terminal_panel::Toggle, workspace::NewTerminal (`ctrl-~`) | Zed |
| Ctrl+Space | Trigger suggestions | editor::ShowCompletions | Zed |
| Ctrl+Cmd+F | Full screen | zed::ToggleFullScreen | Zed |
| Cmd+=, Cmd+-, Cmd+0 | Zoom in, out, reset | buffer font size actions (VS Code zooms the whole window) | Zed |

## Editing (VS Code baseline)

| Cursor shortcut | Cursor action | Zed binding and action | From |
|---|---|---|---|
| Cmd+D | Add next occurrence | editor::SelectNext | Zed |
| Cmd+F2 | Select all occurrences (Cmd+Shift+L is chat in Cursor) | editor::SelectAllMatches | Zed |
| Cmd+/ | Toggle line comment | editor::ToggleComments (empty lines skipped, as in VS Code) | here |
| Opt+Up, Opt+Down | Move line | editor::MoveLineUp, MoveLineDown | Zed |
| Shift+Opt+Up, Shift+Opt+Down | Copy line | editor::DuplicateLineUp, DuplicateLineDown | Zed |
| Cmd+Shift+K | Delete line | editor::DeleteLine | Zed |
| Cmd+Enter, Cmd+Shift+Enter | Insert line below, above | editor::NewlineBelow, NewlineAbove | Zed |
| Cmd+], Cmd+[ | Indent, outdent | editor::Indent, Outdent | Zed |
| Cmd+Shift+\ | Jump to matching bracket | editor::MoveToEnclosingBracket (Zed writes the key as `cmd-\|`) | Zed |
| Cmd+Opt+Up, Cmd+Opt+Down | Add cursor above, below | editor::AddSelectionAbove, AddSelectionBelow | Zed |
| Cmd+U | Undo last cursor action | editor::UndoSelection | Zed |
| Shift+Opt+F | Format document | editor::Format (Cmd+Shift+I is the chat in Cursor, so Zed's own key is gone) | here |
| Shift+Opt+I | Cursor at end of each selected line | editor::SplitSelectionIntoLines | here |
| Ctrl+Shift+Cmd+Right, Left | Expand, shrink selection | editor::SelectLargerSyntaxNode, SelectSmallerSyntaxNode | here |
| Opt+Z | Toggle word wrap | editor::ToggleSoftWrap | here |
| Cmd+Opt+[ , Cmd+Opt+] | Fold, unfold | editor::Fold, editor::UnfoldLines | Zed |
| Cmd+Shift+Space | Parameter hints (VS Code meaning kept; Cursor uses it for voice mode, which Zed lacks) | editor::ShowSignatureHelp | here |
| F12, Cmd+click | Go to definition | editor::GoToDefinition | Zed |
| Cmd+F12 | Go to implementation | editor::GoToImplementation | here |
| Shift+F12 | Find all references | editor::FindAllReferences | here |
| F2 | Rename symbol | editor::Rename | Zed |
| Cmd+. | Quick fix | editor::ToggleCodeActions | Zed |
| F8, Shift+F8 | Next, previous problem | editor::GoToDiagnostic, GoToPreviousDiagnostic | Zed |

## Cursor shortcuts with no Zed equivalent

- **Cmd+Shift+Space, voice mode:** Zed has no voice input.
- **Cmd+T, new chat tab:** Zed's chat has no thread tabs; Cmd+N and Cmd+R start a new thread instead.
- **Tab, cycle to next chat message:** no Zed action found (only scrolling to the next message).
- **Esc, unfocus the chat field:** not bound. `workspace::FocusCenterPane` exists, but Esc is also Zed's key for other chat actions, so it is left alone.
- **Cmd+Enter, search codebase in chat:** no Zed action found.
- **Cmd+K chords (Cmd+K Cmd+F, Cmd+K Z, Cmd+K F12):** Cursor itself uses Cmd+K for inline edit, so these VS Code chords do not work in either editor. With the Cursor preset Zed's own Cmd+K chords (including Cmd+K Cmd+S) are shadowed in the editor too, which is why Cmd+R then Cmd+S is bound.
- **Alt+F12, peek definition:** Zed has no inline peek; its Alt+F12 opens the definition in a split.
- **Cmd+K Z, Zen Mode:** no Zed equivalent (`workspace::ToggleCenteredLayout` only centers the editor).
- **Cmd+Shift+B, run build task:** Zed's key opens the outline panel; not changed.
- **Cursor features without a key** (Agents Window, Design Mode, Bugbot, Cloud Agents) are not shortcuts and are not mapped.

## How to check it on a Mac

1. `git pull`, then `python3 ~/agents-config/scripts/install_dotfiles.py --diff`, then `--apply`; restart Zed.
2. Press Cmd+Shift+P, type `zed: open keymap`, and search for any key above; Zed's keymap editor lists the actions bound to it.
3. Spot checks: Cmd+B twice (tree hides and shows), Cmd+Opt+S (saves all), Cmd+E (Threads sidebar), Cmd+Opt+F (find and replace), Cmd+Enter in the chat (sends now), Cmd+R then Cmd+S from the editor (keymap opens), Cmd+R in the chat (new thread at once, no delay), Ctrl+Cmd+Down with the cursor in a file (splits).
