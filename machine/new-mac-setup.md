# Set up a new Mac with Brando's coding tools

**Doc link:** <https://github.com/brando90/agents-config/blob/main/machine/new-mac-setup.md>

**TLDR:** Give any capable agent the prompt below to install the coding tools, merge the shared settings, and verify their actual behavior on a new Mac. Existing files are backed up, configuration diffs are shown before writes, and the completion report separates installed software from working integrations and human-only steps.

## Copy-ready starting prompt

This is a bounded setup task: if selecting an execution model, GPT-6.1 Sol with medium reasoning is proportionate. Keep the client's configured defaults otherwise; model selection advice is separate from the prompt.

```text
Set up this new computer using https://github.com/brando90/agents-config/blob/main/machine/new-mac-setup.md.

First verify the actual computer, operating system, user account and processor architecture. If they differ from my intended target, resolve that before changing anything. Clone or refresh ~/agents-config, read its instructions and the setup guide, and complete the applicable steps.

Install or reuse Homebrew, Cursor, Ghostty, Zed, herdr, and the Codex, Claude Code and Pi command-line clients. Use official sources and existing package managers. Configure herdr's Codex, Claude and Pi integrations. Apply the shared Cursor-style Zed layout and keyboard bindings together, keep Vim mode enabled, and include the shared Cursor/Ghostty shortcuts.

Back up existing settings and show the exact configuration diffs before applying them. Preserve unrelated preferences and active work. Show shell-startup changes before writing them; make Ghostty the default terminal only if I explicitly confirm. Use administrator privileges only where unavoidable and identify the reason.

Launch the apps and test the behavior, including Cmd+B from editor/tree/terminal focus, the hidden Threads sidebar, herdr panes, and mouse selection/copy/paste. Distinguish installation, integration registration, account access and interactive verification. Complete the authorized work; report only genuine human-only steps or unavailable capabilities as remaining.

TL;DR: Reproduce my coding setup on the verified new computer, using agents-config as the source of truth, and return versions, actual test results, backups and remaining manual steps.
```

## 1. Identify and inventory the destination

Read the shared index and applicable rules first. This guide targets macOS; when the destination is another operating system, select its maintained host route from [the catalog](../CATALOG.md) and adapt the procedure before executing macOS commands. A MacBook model or hostname in an earlier chat is not evidence of the current target.

Record `sw_vers`, `sysctl -n hw.model`, `sysctl -n hw.optional.arm64`, `id -un`, the actual home directory, and available package managers. `uname -m` alone can reflect Rosetta translation. Inspect installed versions, application paths, existing profiles and running agents. Reuse working installations and preserve concurrent installations instead of racing or killing them.

Use one canonical checkout at `~/agents-config`. If absent, clone its public HTTPS remote; if Git or the Apple command-line tools are missing, use the supported installer and identify any human-only prompt. Otherwise refresh with `git -C ~/agents-config pull --ff-only`, preserving local changes. Keep an inventory of owned changes for the final receipt.

## 2. Use the right sources and installers

| Component | Maintained source and action |
|---|---|
| Homebrew | Check `brew --version` and `brew --prefix` first. Install only if missing, using [brew.sh](https://brew.sh/). Respect an existing working prefix; do not migrate it as an incidental setup step. |
| Cursor, Ghostty, Zed | Confirm current casks with `brew info --cask cursor ghostty zed`, then install missing apps. Use a user-writable application directory when appropriate. Official sites: [Cursor](https://cursor.com/), [Ghostty](https://ghostty.org/), [Zed](https://zed.dev/). |
| herdr | Confirm [herdr.dev](https://herdr.dev/) and the current Homebrew formula. Herdr runs inside a terminal; it is not a separate desktop editor. Install with the supported package manager and verify `herdr --version`. |
| Codex and Claude Code | Inspect existing installations, then use their supported package manager or current official native install instructions: [Codex](https://developers.openai.com/codex/cli), [Claude Code](https://code.claude.com/docs/en/setup). Follow [client/profile routing](../workflows/multi-account-agent-clis.md) for authorized accounts. |
| Pi | Use the official [Pi repository](https://github.com/earendil-works/pi) and [shared Pi configuration guide](../config/pi/README.md). Verify the currently supported package and runtime instead of copying a dated installation command. |

Use the installed Node version manager where present. Install dependencies only when a selected tool needs them. Package registration, process startup, sign-in and successful model use are separate observations.

The default scope above is the coding workspace. Additional applications, remote hosts, automatic synchronization services and broader trusted-agent permissions follow the user's requested scope and their own maintained guides. The old `dotfiles/legacy/setup_my_mac.sh` is a historical reference, not this bootstrap. The [advanced agent-access guide](macos-ai-apps/ai_agent_automatable_setup_codex_clauded.md) has a broader scope than ordinary app installation; do not treat its full contents as an implicit baseline.

## 3. Preview, back up and merge configuration

Put private timestamped backups under `~/.local/state/agents-config/dotfiles/backups/`, preserving relative paths. Capture absence as well as existing content so rollback can remove newly created files. Read current files again immediately before a write to detect concurrent changes. Show actual diffs with secret values redacted; a list of filenames is not a diff.

- **Shared instructions:** use the preservation-oriented [README quick start](../README.md#quick-start). Resolve active client-profile paths. Merge routing into existing instruction files; verify links and discovery in a fresh session. Do not overwrite a whole settings file merely to install shared instructions.
- **Cursor and Ghostty shortcuts:** read [dotfiles/README.md](../dotfiles/README.md), then run `python3 ~/agents-config/scripts/install_dotfiles.py --diff`. This previews changes without applying them. After presenting the diff, use `--apply`; the installer backs up existing files. It currently manages Cursor and Ghostty, not Zed.
- **Zed:** merge the bindings from `dotfiles/zed/keymap.json` and the layout below together. Preserve unrelated preferences. The shared full settings file also contains optional themes, agent servers and other preferences; do not overwrite a host's entire settings file just to configure the keyboard.
- **Pi:** begin with `python3 ~/agents-config/config/pi/install.py --check` and inspect its manifest. Apply through the [Pi guide](../config/pi/README.md) after previewing changes. Its managed resource arrays replace existing arrays: preserve wanted additions through its supported host overrides. A provider menu is not proof of funded or authenticated access.
- **herdr integrations:** inspect installed help and `herdr integration status`. Preview each installer's settings/hook changes from its supported preview or implementation before running `herdr integration install codex`, `herdr integration install claude` and `herdr integration install pi` where missing or outdated. Preserve other hooks. Check registration afterward; Herdr owns its Pi extension.

Required Zed layout values, merged into existing JSON-with-comments:

```json
{
  "base_keymap": "Cursor",
  "vim_mode": true,
  "project_panel": { "dock": "left" },
  "agent": {
    "dock": "right",
    "threads_sidebar": { "auto_open": false }
  }
}
```

Cmd+B is `workspace::ToggleLeftDock` in the shared Workspace, Editor and Terminal contexts. It changes visibility immediately. `project_panel::Toggle` and `project_panel::ToggleFocus` introduce focus-dependent behavior and do not match Cursor's Cmd+B. Keep Cmd+Shift+E for focusing the project tree. If Zed's separate Threads column is already visible, hide it once with Cmd+Option+S; disabling automatic opening does not close an existing column.

Keep credentials in their authorized private stores. For migration, use [verified-host bootstrap](../workflows/verified-host-bootstrap.md) to select portable configuration and verify the receiving host; host-specific paths, runtimes and sign-ins need destination-specific treatment. Check account status through supported non-secret output. Existing budget and credential-owner scopes apply to any model request. Record model access as untested unless actually verified.

## 4. Launch and verify real behavior

Use a disposable project or a known folder with no unsaved changes. Open it in the editor, and open herdr inside Ghostty using the installed program paths. On macOS, Ghostty's supported launch route is `open -na Ghostty.app --args -e /absolute/path/to/herdr`; inspect current help and the actual application location first. Keep the default-terminal choice separate from launching Ghostty.

Follow the installed Herdr skill's control boundary: agents operating panes must run inside a Herdr-managed pane. A desktop agent outside Herdr should use an authorized interactive route or arrange the in-pane test. Do not pretend an external process listing proves which pane is visible. Tool-enforced application restrictions remain binding; report the specific unverified interaction instead of claiming success.

| Check | Required observation |
|---|---|
| Versions and launch | Each selected tool reports its installed version; each app visibly opens. Record macOS approval prompts that require the user. |
| Zed with editor focus | With a real file open and tree visible, one Cmd+B hides it and one restores it. No focus-only intermediate press. |
| Zed with tree and terminal focus | Repeat from each context. Every press changes file-sidebar visibility; it does not toggle the agent chat or Threads column. |
| Zed layout persistence | Open another project in the existing window. File tree is left, editor center, agent chat right when shown, and the extra Threads column remains hidden. Vim mode remains enabled. |
| herdr integrations | Codex, Claude and Pi report current integrations. Start only the disposable verification sessions needed to confirm detection; distinguish registration from observed sidebar status and session restoration. |
| Shared split shortcuts | In Ghostty running herdr, Control+Command+Down/Right splits herdr's pane area while preserving one sidebar. The shared keys send herdr prefix sequences; outside herdr they do not mean native Ghostty splits. |
| Mouse and clipboard | Select a known harmless text string and verify copy/paste round-trips in Ghostty and inside herdr, including Command+C/Command+V and the configured mouse-selection gesture. Read [the mouse/clipboard guide](herdr-mouse-agent-repairs-10-22-2026.md); record the gesture actually tested. |
| Rerun | Repeat previews/checks. Already-applied managed settings produce no further change; local preferences and other owners' work remain intact. |

A successful command or configuration parse is not a successful visual/keyboard test. If computer control is unavailable, report those rows as **unverified**, with the precise manual step. Authentication, operating-system permission prompts and existing unsaved work can require human action; complete independent work while those remain pending.

## 5. Deliver and retain a concise receipt

Return the actual machine, date, repository revision, tool/version/installed table, and an observed pass/fail/unverified result for each applicable interaction. Include backup locations, rollback steps and only the remaining human actions. Record the receipt under `~/.local/state/agents-config/new-computer/` on the destination; keep private account and host details out of this public repository.

For rollback, restore only the owned changes from backups, accounting for edits made since setup. Remove only newly created files belonging to this setup, and clean up its disposable sessions. Future application updates may change action names or behavior, so repeat the interaction checks instead of treating this guide as permanent proof.

**Validation status — 10-26-2026:** the Zed layout and editor/tree Cmd+B behavior were observed on the existing MacBook Air with Zed 1.25.3. The complete fresh-machine procedure has not yet been run on a new Mac; a separate Mac virtual-machine test was requested in [the agent inbox](https://github.com/brando90/agents-config/issues/68#issuecomment-6427572699). That request is not a passing test result.

**TLDR-end:** [New Mac: coding workspace] Install through current official routes, preview and merge shared settings, then prove the keyboard, layout, terminal and integration behavior on the destination.
