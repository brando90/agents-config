# AI Agent Automatable Setup: Codex, Claude Code, Cursor, ChatGPT, Manus

**TLDR:** Use this on each Mac to let Codex or Claude Code configure the shell-automatable parts of trusted local AI-agent workflows. It sets full-trust aliases/configs and opens macOS permission panes, but intentionally leaves Apple privacy approvals as manual clicks.

This file contains the setup that **Codex full-trust aliases (`codex-yolo` / `codexd`)** or **Claude Code `clauded`** can do for you as much as macOS allows from a shell.

It intentionally does **not** include instructions to bypass Apple's privacy system, modify macOS TCC databases, disable System Integrity Protection (SIP), or create permanent passwordless `sudo` for every command. Those are not normal user-consent toggles; they create machine-wide backdoors and can make a prompt-injection or malicious repository equivalent to root compromise.

The practical target is:

- Codex full-trust mode.
- Claude Code bypass-permissions mode.
- Shell aliases like `codexd`, `codexroot`, `clauded`, `clauderoot`.
- Session-scoped `sudo` keepalive: you type your Mac password once, then `sudo` stays warm while the agent command runs, and is revoked afterward.
- System Settings panes opened automatically so you can manually toggle the remaining macOS privacy permissions.
- Harmless permission-trigger commands so macOS exposes the relevant apps in Privacy & Security.

---

## Copy-paste prompt for `codex-yolo`, `codexd`, or `clauded`

Paste this into Codex or Claude Code on **each Mac**.

```txt
You are configuring this Mac for my trusted AI agent workflows.

Goal:
- Configure as much as possible from the shell for full-trust local AI agent use.
- Configure Codex and Claude Code to run in no-approval / full-trust modes.
- Add short shell commands similar to my `clauded` command.
- Add session-scoped sudo helpers so I can type my Mac password once and keep
  sudo warm while an agent is running.
- Open macOS Privacy & Security panes so I can manually grant the remaining
  permissions.
- Trigger harmless first-time permission prompts where possible.

Important boundaries:
- Do NOT modify /etc/sudoers.
- Do NOT create permanent passwordless sudo such as NOPASSWD:ALL.
- Do NOT run GUI apps as root.
- Do NOT modify macOS TCC privacy databases.
- Do NOT disable System Integrity Protection.
- Do NOT modify /Library, /System, /usr, /etc, Keychain, browser profiles,
  credentials, tokens, or ~/.ssh.
- Do NOT print secrets or environment variables that may contain secrets.
- Only modify files inside my home directory, except for opening System
  Settings panes for me to manually approve permissions.

Before editing, inspect and print:
- hostname
- whoami
- echo "$SHELL"
- echo "$HOME"
- pwd
- command -v codex || true
- codex --version || true
- command -v claude || true
- claude --version || true
- command -v cursor || true
- command -v node || true
- ls -lah ~/.zshrc ~/.bashrc ~/.bash_profile ~/.codex/config.toml ~/.claude/settings.json 2>/dev/null || true

Shell setup:
- Prioritize ~/.zshrc because macOS normally uses zsh.
- Also update ~/.bashrc.
- If ~/.bash_profile exists and does not source ~/.bashrc, add a safe block
  to source ~/.bashrc for interactive bash shells.
- Back up every file before editing it.
- Avoid duplicate aliases/functions.
- Preserve Homebrew, conda/mamba, pyenv, SSH setup, PATH settings, Claude
  aliases, Codex aliases, Cursor aliases, and any existing
  `clauded` command if present.
- Put all changes inside this marked block:
  # >>> ai full-trust aliases >>>
  ...
  # <<< ai full-trust aliases <<<

Add this block to ~/.zshrc and ~/.bashrc, replacing any previous block with
exactly these markers:

# >>> ai full-trust aliases >>>
# Session-scoped sudo helper for trusted AI agent work.
# This asks for my Mac password once, keeps sudo alive during the command,
# then revokes sudo when the command exits.
ai-sudo-session() {
  if [ "$#" -eq 0 ]; then
    echo "usage: ai-sudo-session <command> [args...]"
    return 2
  fi

  sudo -v || return 1

  (
    while true; do
      sudo -n true >/dev/null 2>&1 || exit
      sleep 60
    done
  ) &

  local keepalive_pid="$!"

  "$@"
  local status="$?"

  kill "$keepalive_pid" >/dev/null 2>&1 || true
  sudo -k >/dev/null 2>&1 || true

  return "$status"
}

# Manual sudo keepalive toggle. Use ai-sudo-off to revoke.
ai-sudo-on() {
  sudo -v || return 1

  if [ -f "$HOME/.ai-sudo-keepalive.pid" ]; then
    kill "$(cat "$HOME/.ai-sudo-keepalive.pid")" >/dev/null 2>&1 || true
    rm -f "$HOME/.ai-sudo-keepalive.pid"
  fi

  (
    while true; do
      sudo -n true >/dev/null 2>&1 || exit
      sleep 60
    done
  ) &

  echo "$!" > "$HOME/.ai-sudo-keepalive.pid"
  echo "sudo keepalive enabled for this user session. Run ai-sudo-off to revoke."
}

ai-sudo-off() {
  if [ -f "$HOME/.ai-sudo-keepalive.pid" ]; then
    kill "$(cat "$HOME/.ai-sudo-keepalive.pid")" >/dev/null 2>&1 || true
    rm -f "$HOME/.ai-sudo-keepalive.pid"
  fi
  sudo -k >/dev/null 2>&1 || true
  echo "sudo keepalive revoked."
}

# Codex: full filesystem/network access, no Codex approval prompts.
alias codexd='codex --sandbox danger-full-access --ask-for-approval never'
alias codexroot='ai-sudo-session codex --sandbox danger-full-access --ask-for-approval never'
alias codex-yolo='codex --dangerously-bypass-approvals-and-sandbox'
alias codex-safe='codex --sandbox workspace-write --ask-for-approval on-request'

# Claude Code: bypass permissions mode.
alias clauded='claude --dangerously-skip-permissions'
alias clauderoot='ai-sudo-session claude --dangerously-skip-permissions'

# GUI apps should not be launched with sudo. Use macOS Privacy & Security
# permissions instead.
alias cursorroot='echo "Do not launch GUI Cursor as root. Grant Cursor/Terminal/node Full Disk Access, Accessibility, Screen Recording, Developer Tools, and Automation in System Settings."'
alias chatgptroot='echo "Do not launch GUI ChatGPT as root. Grant ChatGPT/Terminal/node permissions manually in System Settings if listed."'
alias manusroot='echo "Do not launch GUI Manus as root. Grant Manus/Terminal/browser permissions manually in System Settings if listed."'
# <<< ai full-trust aliases <<<

Codex config:
- Create ~/.codex if needed.
- Back up ~/.codex/config.toml if it exists.
- Ensure ~/.codex/config.toml contains:
  model = "gpt-5.5"
  model_reasoning_effort = "xhigh"
  approval_policy = "never"
  sandbox_mode = "danger-full-access"
  web_search = "live"
- Preserve unrelated Codex settings.
- Do not store secrets in ~/.codex/config.toml.

Claude Code config:
- Create ~/.claude if needed.
- Back up ~/.claude/settings.json if it exists.
- Merge these settings into ~/.claude/settings.json without deleting other
  settings:

{
  "permissions": {
    "defaultMode": "bypassPermissions",
    "skipDangerousModePermissionPrompt": true
  }
}

- If jq is available, use jq to merge. Otherwise use a small Python script.
- Preserve unrelated Claude settings.

Open macOS Privacy & Security panes:
- Open the relevant System Settings panes for me.
- Do not try to bypass macOS privacy controls programmatically.
- Run these commands, ignoring failures:

open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_DeveloperTools" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Automation" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_FilesAndFolders" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_LocalNetwork" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_AppManagement" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Contacts" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Calendars" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Reminders" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Photos" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Camera" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone" || true

Trigger harmless first-time permission prompts where possible:
- Run these harmless commands, ignoring failures:

osascript -e 'tell application "Finder" to get name of startup disk' || true
osascript -e 'tell application "System Events" to get name of first process' || true
mkdir -p "$HOME/Desktop/ai-permission-test"
screencapture -x "$HOME/Desktop/ai-permission-test/screen-test.png" || true
open -a "Google Chrome" || true
open -a "Safari" || true
open -a "Cursor" || true
open -a "Visual Studio Code" || true
open -a "ChatGPT" || true
open -a "Claude" || true
open -a "Manus" || true

After editing:
- Show the final AI full-trust alias block from ~/.zshrc.
- Show the final AI full-trust alias block from ~/.bashrc.
- Show only the non-secret Codex settings you changed from ~/.codex/config.toml:
  model, model_reasoning_effort, approval_policy, sandbox_mode, web_search.
- Show only the relevant Claude permissions keys from ~/.claude/settings.json.
- Do not print unrelated config blocks, MCP env, tokens, credentials, or secrets.
- Tell me to run:
  source ~/.zshrc
- Tell me the main commands:
  codexd
  codexroot
  codex-yolo
  clauded
  clauderoot
  ai-sudo-on
  ai-sudo-off
- Remind me that macOS System Settings toggles still require manual clicks.
- Remind me to quit and reopen Terminal/iTerm2/Cursor/Visual Studio Code/
  Codex/Claude/ChatGPT/Manus after toggling permissions.
```

---

## Optional direct shell block

Use this only if you want to paste commands yourself instead of asking Codex/Claude to do it.

```bash
set -euo pipefail

stamp="$(date +%Y%m%d-%H%M%S)"

backup_if_exists() {
  local file="$1"
  if [ -e "$file" ]; then
    cp "$file" "$file.bak.$stamp"
  fi
}

replace_block() {
  local file="$1"
  mkdir -p "$(dirname "$file")"
  touch "$file"
  backup_if_exists "$file"
  perl -0pi -e 's/\n# >>> ai full-trust aliases >>>.*?# <<< ai full-trust aliases <<<\n?/\n/s' "$file"
  cat >> "$file" <<'ALIASES_BLOCK'

# >>> ai full-trust aliases >>>
ai-sudo-session() {
  if [ "$#" -eq 0 ]; then
    echo "usage: ai-sudo-session <command> [args...]"
    return 2
  fi
  sudo -v || return 1
  (
    while true; do
      sudo -n true >/dev/null 2>&1 || exit
      sleep 60
    done
  ) &
  local keepalive_pid="$!"
  "$@"
  local status="$?"
  kill "$keepalive_pid" >/dev/null 2>&1 || true
  sudo -k >/dev/null 2>&1 || true
  return "$status"
}

ai-sudo-on() {
  sudo -v || return 1
  if [ -f "$HOME/.ai-sudo-keepalive.pid" ]; then
    kill "$(cat "$HOME/.ai-sudo-keepalive.pid")" >/dev/null 2>&1 || true
    rm -f "$HOME/.ai-sudo-keepalive.pid"
  fi
  (
    while true; do
      sudo -n true >/dev/null 2>&1 || exit
      sleep 60
    done
  ) &
  echo "$!" > "$HOME/.ai-sudo-keepalive.pid"
  echo "sudo keepalive enabled. Run ai-sudo-off to revoke."
}

ai-sudo-off() {
  if [ -f "$HOME/.ai-sudo-keepalive.pid" ]; then
    kill "$(cat "$HOME/.ai-sudo-keepalive.pid")" >/dev/null 2>&1 || true
    rm -f "$HOME/.ai-sudo-keepalive.pid"
  fi
  sudo -k >/dev/null 2>&1 || true
  echo "sudo keepalive revoked."
}

alias codexd='codex --sandbox danger-full-access --ask-for-approval never'
alias codexroot='ai-sudo-session codex --sandbox danger-full-access --ask-for-approval never'
alias codex-yolo='codex --dangerously-bypass-approvals-and-sandbox'
alias codex-safe='codex --sandbox workspace-write --ask-for-approval on-request'
alias clauded='claude --dangerously-skip-permissions'
alias clauderoot='ai-sudo-session claude --dangerously-skip-permissions'
alias cursorroot='echo "Do not launch GUI Cursor as root. Grant macOS Privacy & Security permissions instead."'
alias chatgptroot='echo "Do not launch GUI ChatGPT as root. Grant macOS Privacy & Security permissions instead."'
alias manusroot='echo "Do not launch GUI Manus as root. Grant macOS Privacy & Security permissions instead."'
# <<< ai full-trust aliases <<<
ALIASES_BLOCK
}

replace_block "$HOME/.zshrc"
replace_block "$HOME/.bashrc"

if [ -f "$HOME/.bash_profile" ] && ! grep -q 'source "$HOME/.bashrc"' "$HOME/.bash_profile"; then
  backup_if_exists "$HOME/.bash_profile"
  cat >> "$HOME/.bash_profile" <<'BASH_PROFILE_BLOCK'

# >>> bashrc source >>>
if [ -f "$HOME/.bashrc" ]; then
  source "$HOME/.bashrc"
fi
# <<< bashrc source <<<
BASH_PROFILE_BLOCK
fi

mkdir -p "$HOME/.codex"
backup_if_exists "$HOME/.codex/config.toml"
python3 - <<'PY_CODEX'
from pathlib import Path

path = Path.home() / ".codex" / "config.toml"
text = path.read_text() if path.exists() else ""
keys = {
    "model": '"gpt-5.5"',
    "model_reasoning_effort": '"xhigh"',
    "approval_policy": '"never"',
    "sandbox_mode": '"danger-full-access"',
    "web_search": '"live"',
}
lines = text.splitlines()
out = []
seen = set()
inserted = False

def append_missing_root_settings():
    global inserted
    missing = [(key, value) for key, value in keys.items() if key not in seen]
    if missing:
        if out and out[-1].strip():
            out.append("")
        for key, value in missing:
            out.append(f"{key} = {value}")
    inserted = True

for line in lines:
    stripped = line.strip()
    if stripped.startswith("[") and not inserted:
        append_missing_root_settings()
    key = stripped.split("=", 1)[0].strip() if "=" in stripped else None
    if not inserted and key in keys and not stripped.startswith("#"):
        out.append(f"{key} = {keys[key]}")
        seen.add(key)
    else:
        out.append(line)
if not inserted:
    append_missing_root_settings()
path.write_text("\n".join(out).rstrip() + "\n")
PY_CODEX

mkdir -p "$HOME/.claude"
backup_if_exists "$HOME/.claude/settings.json"
python3 - <<'PY_CLAUDE'
import json
from pathlib import Path

path = Path.home() / ".claude" / "settings.json"
if path.exists() and path.read_text().strip():
    data = json.loads(path.read_text())
else:
    data = {}
permissions = data.setdefault("permissions", {})
permissions["defaultMode"] = "bypassPermissions"
permissions["skipDangerousModePermissionPrompt"] = True
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
PY_CLAUDE

open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_DeveloperTools" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Automation" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_FilesAndFolders" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_LocalNetwork" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_AppManagement" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Contacts" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Calendars" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Reminders" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Photos" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Camera" || true
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone" || true

osascript -e 'tell application "Finder" to get name of startup disk' || true
osascript -e 'tell application "System Events" to get name of first process' || true
mkdir -p "$HOME/Desktop/ai-permission-test"
screencapture -x "$HOME/Desktop/ai-permission-test/screen-test.png" || true
open -a "Google Chrome" || true
open -a "Safari" || true
open -a "Cursor" || true
open -a "Visual Studio Code" || true
open -a "ChatGPT" || true
open -a "Claude" || true
open -a "Manus" || true

echo "Done. Now run: source ~/.zshrc"
echo "Then use: codexd, codexroot, codex-yolo, clauded, clauderoot, ai-sudo-on, ai-sudo-off"
```

---

## What this can automate

- Add shell aliases and functions.
- Configure Codex to full-access/no-approval mode.
- Configure Claude Code to bypass-permissions mode.
- Keep `sudo` authenticated for a session after you type your password once.
- Open System Settings panes.
- Trigger permission prompts so the apps appear in macOS Privacy & Security.
- Launch apps so they can request permissions.

## What still needs manual action

- Turning on Full Disk Access.
- Turning on Accessibility.
- Turning on Screen & System Audio Recording.
- Expanding Automation entries and enabling target apps.
- Granting Camera, Microphone, Photos, Contacts, Calendar, Reminders.
- Entering your password / Touch ID / passkey / Keychain prompts.
- Granting app-specific browser or desktop permissions.
- Restarting apps after permissions are changed.
