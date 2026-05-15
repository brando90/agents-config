# Manual macOS Permissions Checklist for AI Apps

**TLDR:** Use this after the automatable setup on each Mac to grant the Privacy & Security permissions that Apple requires a human to approve. It covers the runner apps, browser apps, and desktop-control permissions needed by Codex, Claude Code, Gemini, Cursor, ChatGPT, and Manus.

Use this checklist on each trusted Mac after running the automatable setup.

This is the part that Codex, Claude Code, Gemini, Cursor, ChatGPT, and Manus generally **cannot fully do for you** from the shell. Apple requires manual approval for many Privacy & Security permissions.

---

## Apps to enable wherever they appear

Enable these apps if you use them or if they appear in a permission pane:

- Terminal
- iTerm2
- Cursor
- Visual Studio Code
- `node`
- Codex
- Claude
- Claude Code
- Gemini
- ChatGPT
- Manus
- Google Chrome
- Safari

The most important apps are usually the **runner apps**:

- Terminal or iTerm2 if you run agents from a terminal.
- Cursor or Visual Studio Code if the agent runs inside the editor.
- `node` if Codex was installed with `npm` and macOS shows Node.js as the parent process.
- Manus if you use Manus Desktop / local computer-control workflows.
- Google Chrome or Safari if the agent controls the browser.

---

## Open Privacy & Security

Go to:

```text
Apple menu 
→ System Settings
→ Privacy & Security
```

Then complete each section below.

---

## 1. Full Disk Access

Path:

```text
Privacy & Security → Full Disk Access
```

Turn on:

- Terminal
- iTerm2
- Cursor
- Visual Studio Code
- `node`, if shown
- Codex, if shown
- Claude, if shown
- Gemini, if shown
- ChatGPT, if shown
- Manus, if shown
- Google Chrome, if you want browser automation to read/write downloaded/local files
- Safari, if you want Safari automation

Why this matters:

- Lets the app access protected files and app data.
- Most important permission for local file automation.

If an app is missing:

```text
Click +
→ Applications
→ select the app
→ Open
→ toggle it ON
```

For Terminal:

```text
Applications → Utilities → Terminal
```

For a command-line binary like `node`, first find its path:

```bash
which node
```

Then in the file picker, press:

```text
Command + Shift + G
```

Paste the directory path, select the binary if macOS allows it, and add it.

---

## 2. Accessibility

Path:

```text
Privacy & Security → Accessibility
```

Turn on:

- Terminal
- iTerm2
- Cursor
- Visual Studio Code
- `node`, if shown
- Codex, if shown
- Claude, if shown
- Gemini, if shown
- ChatGPT, if shown
- Manus, if shown
- Google Chrome
- Safari

Why this matters:

- Enables graphical user interface control: clicking, typing, inspecting windows, controlling apps.
- Important for computer-use agents, browser automation, and desktop workflows.

---

## 3. Screen & System Audio Recording

Path:

```text
Privacy & Security → Screen & System Audio Recording
```

Turn on:

- Terminal
- iTerm2
- Cursor
- Visual Studio Code
- Codex, if shown
- Claude, if shown
- Gemini, if shown
- ChatGPT, if shown
- Manus, if shown
- Google Chrome
- Safari

Why this matters:

- Lets agents take screenshots or inspect visual state.
- Necessary for many computer-use / desktop-control workflows.

Test command:

```bash
mkdir -p "$HOME/Desktop/ai-permission-test"
screencapture -x "$HOME/Desktop/ai-permission-test/screen-test.png"
```

If macOS prompts you, allow it. Then quit and reopen the app that requested permission.

---

## 4. Automation

Path:

```text
Privacy & Security → Automation
```

Expand every relevant parent app:

- Terminal
- iTerm2
- Cursor
- Visual Studio Code
- `node`
- Codex
- Claude
- Gemini
- ChatGPT
- Manus
- Google Chrome
- Safari

Under each one, enable target apps you want controlled:

- Finder
- System Events
- Google Chrome
- Safari
- Terminal
- iTerm2
- Messages
- Mail
- Calendar
- Reminders
- Photos
- Contacts
- Notes

Important:

- Automation entries often appear only after the parent app first tries to control another app.
- If something is missing, run the agent once and ask it to open/control Finder or Chrome.
- Then return to this pane and enable the new entries.

Harmless trigger commands:

```bash
osascript -e 'tell application "Finder" to get name of startup disk' || true
osascript -e 'tell application "System Events" to get name of first process' || true
open -a "Google Chrome" || true
open -a "Safari" || true
```

---

## 5. Developer Tools

Path:

```text
Privacy & Security → Developer Tools
```

Turn on:

- Terminal
- iTerm2
- Cursor
- Visual Studio Code
- Codex, if shown
- Claude, if shown
- Manus, if shown

Why this matters:

- Reduces friction for developer workflows.
- Useful for agents running builds, debuggers, local servers, package managers, and development tools.

---

## 6. Files & Folders

Path:

```text
Privacy & Security → Files & Folders
```

For each relevant app, enable:

- Desktop Folder
- Documents Folder
- Downloads Folder
- Removable Volumes
- Network Volumes

Apps to check:

- Terminal
- iTerm2
- Cursor
- Visual Studio Code
- Codex
- Claude
- Gemini
- ChatGPT
- Manus
- Google Chrome
- Safari

Note:

- Full Disk Access is broader, but Files & Folders can still show app-specific toggles.

---

## 7. Local Network

Path:

```text
Privacy & Security → Local Network
```

Turn on:

- Terminal
- iTerm2
- Cursor
- Visual Studio Code
- Codex
- Claude
- Gemini
- ChatGPT
- Manus
- Google Chrome
- Safari

Why this matters:

- Local servers.
- Model Context Protocol (MCP) servers.
- Browser automation.
- Devices on your local network.
- Remote-control / agent workflows that use localhost or LAN services.

---

## 8. App Management

Path:

```text
Privacy & Security → App Management
```

Turn on trusted apps if you want them to update, manage, or delete other apps:

- Terminal
- iTerm2
- Cursor
- Visual Studio Code
- Codex, if shown
- Claude, if shown
- Manus, if shown

Use this only for trusted local agent workflows.

---

## 9. Input Monitoring

Path:

```text
Privacy & Security → Input Monitoring
```

Turn on only for apps you want to allow to monitor keyboard/mouse input:

- Terminal
- iTerm2
- Cursor
- Visual Studio Code
- Codex, if shown
- Claude, if shown
- Manus, if shown

This is powerful. Use it only for tools that truly need desktop-control behavior.

---

## 10. Contacts, Calendars, Reminders, Photos, Camera, Microphone

Paths:

```text
Privacy & Security → Contacts
Privacy & Security → Calendars
Privacy & Security → Reminders
Privacy & Security → Photos
Privacy & Security → Camera
Privacy & Security → Microphone
```

Enable only for apps that need those categories.

For your likely workflows:

- Manus: enable if you want it to manage local files, photos, calendar/reminder workflows, camera/microphone workflows, or desktop automation.
- ChatGPT: enable if you want desktop app access to camera/microphone/photos.
- Google Chrome/Safari: enable if web workflows need camera/microphone/photos/files.
- Terminal/iTerm2/Cursor/Visual Studio Code: enable if agents running through them need direct access.

---

## 11. Browser-specific permissions

For Google Chrome:

```text
Chrome → Settings → Privacy and security → Site Settings
```

Check:

- Camera
- Microphone
- Screen sharing
- Notifications
- Pop-ups and redirects
- Automatic downloads
- Clipboard
- File system / local file access where applicable

For Safari:

```text
Safari → Settings → Websites
```

Check:

- Camera
- Microphone
- Screen Sharing
- Downloads
- Pop-up Windows
- Notifications

---

## 12. Restart apps after toggling

After changing permissions, quit and reopen:

- Terminal
- iTerm2
- Cursor
- Visual Studio Code
- Codex
- Claude
- Gemini
- ChatGPT
- Manus
- Google Chrome
- Safari

If an app still behaves as if permission is missing, reboot the Mac.

---

## 13. Optional: prevent sleep during agent work

For laptops:

```text
System Settings → Battery → Options
```

Consider enabling:

- Prevent automatic sleeping on power adapter when the display is off.
- Wake for network access, if available.

For long-running command sessions, you can also use:

```bash
caffeinate -dimsu
```

or run a single command under `caffeinate`:

```bash
caffeinate -dimsu codexd
```

---

## 14. Quick verification checklist

Run from the same app you use to launch agents, such as Terminal or iTerm2.

Check aliases:

```bash
source ~/.zshrc
sed -n '/# >>> ai full-trust aliases >>>/,/# <<< ai full-trust aliases <<</p' ~/.zshrc
```

Check Codex config:

```bash
python3 - <<'PY_CODEX_CHECK'
from pathlib import Path

path = Path.home() / ".codex" / "config.toml"
keys = {"model", "model_reasoning_effort", "approval_policy", "sandbox_mode", "web_search"}
for line in path.read_text().splitlines():
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or stripped.startswith("[") or "=" not in stripped:
        continue
    key = stripped.split("=", 1)[0].strip()
    if key in keys:
        print(line)
PY_CODEX_CHECK
```

Check Claude config:

```bash
python3 - <<'PY_CLAUDE_CHECK'
import json
from pathlib import Path

path = Path.home() / ".claude" / "settings.json"
permissions = json.loads(path.read_text()).get("permissions", {})
for key in ("defaultMode", "skipDangerousModePermissionPrompt"):
    if key in permissions:
        print(f"{key}: {permissions[key]}")
PY_CLAUDE_CHECK
```

Check screenshot permission:

```bash
mkdir -p "$HOME/Desktop/ai-permission-test"
screencapture -x "$HOME/Desktop/ai-permission-test/screen-test.png"
ls -lah "$HOME/Desktop/ai-permission-test/screen-test.png"
```

Check Automation permission prompts:

```bash
osascript -e 'tell application "Finder" to get name of startup disk'
osascript -e 'tell application "System Events" to get name of first process'
```

Check Full Disk Access carefully without printing private contents:

```bash
test -r "$HOME/Library/Messages/chat.db" \
  && echo "Can read protected Messages database path" \
  || echo "Cannot read protected Messages database path or it does not exist"
```

---

## 15. What cannot be fully automated from Codex/Claude

These usually require manual action:

- Turning on macOS Privacy & Security toggles.
- Approving Full Disk Access.
- Approving Accessibility.
- Approving Screen & System Audio Recording.
- Approving Automation target-app checkboxes.
- Approving Keychain access.
- Touch ID / passkey prompts.
- Browser site permissions.
- Some app-specific security prompts.
- Managed-device Privacy Preferences Policy Control (PPPC), unless your Mac is enrolled in Mobile Device Management (MDM).

Do not try to bypass these by editing TCC databases or disabling System Integrity Protection. Use the manual toggles.

---

## 16. Main run commands after setup

Use these in Terminal or iTerm2 after running the automatable setup:

```bash
source ~/.zshrc
```

Codex full trust:

```bash
codexd
```

Codex full trust with session-scoped sudo:

```bash
codexroot
```

Codex maximum bypass alias:

```bash
codex-yolo
```

Claude Code bypass mode:

```bash
clauded
```

Claude Code with session-scoped sudo:

```bash
clauderoot
```

Manual sudo keepalive:

```bash
ai-sudo-on
# do trusted agent work
ai-sudo-off
```
