#!/usr/bin/env python3
"""Install automatic Mac agent updates, preserving other settings and private backups."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import time

from auto_update_agent_apps import lock_path, update_lock
from install_dotfiles import blank_comments, parse_jsonc, top_level_values

ROOT = Path(__file__).resolve().parents[1]
LABEL = "com.brando90.agent-cli-updates"
SETTINGS = {
    "Cursor": ("Library/Application Support/Cursor/User/settings.json", "update.mode", "default"),
    "Devin": ("Library/Application Support/Devin/User/settings.json", "update.mode", "default"),
    "Antigravity IDE": ("Library/Application Support/Antigravity IDE/User/settings.json", "update.mode", "default"),
    "Visual Studio Code": ("Library/Application Support/Code/User/settings.json", "update.mode", "default"),
    "Visual Studio Code - Insiders": ("Library/Application Support/Code - Insiders/User/settings.json", "update.mode", "default"),
    "Zed": (".config/zed/settings.json", "auto_update", True),
    # The native Antigravity storage service stores Boolean settings as strings.
    "Antigravity": ("Library/Application Support/Antigravity/app_storage.json", "autoCheckForUpdates", "true"),
}
SPARKLE_APPS = ("ChatGPT", "Codex")
NATIVE_APPS = ("Claude", "Antigravity", "Gemini", "Grok Bot", "Manus Studio")


def setting(text, key, value):
    """Edit only a top-level setting; preserve comments, other keys, and line endings."""
    text = text if text.strip() else "{}\n"
    live = parse_jsonc(text)
    if not isinstance(live, dict):
        raise ValueError("settings must be a JSON-with-comments object")
    if key in live and live[key] == value:
        return text
    spans, close = top_level_values(text)
    rendered = json.dumps(value)
    if key in spans:
        start, end = spans[key]
        result = text[:start] + rendered + text[end:]
    else:
        index = len(blank_comments(text[:close]).rstrip())
        separator = "" if text[index - 1] in "{," else ","
        newline = "\r\n" if "\r\n" in text else "\n"
        result = (text[:index] + separator + text[index:close].rstrip() + newline
                  + f"  {json.dumps(key)}: {rendered}" + newline + text[close:])
    expected = {**live, key: value}
    if parse_jsonc(result) != expected:
        raise ValueError("settings edit would change unrelated content")
    return result


def agent_plist(home, existing=None):
    config = dict(existing or {})
    state = home / ".local/state/agent-cli-updates"
    config.update(
        Label=LABEL,
        ProgramArguments=[str(home / ".local/bin/auto-update-agent-clis")],
        WorkingDirectory=str(home),
        RunAtLoad=True,
        StartCalendarInterval={"Hour": 10, "Minute": 17},
        StartInterval=3600,
        StandardOutPath=str(state / "launchd.out.log"),
        StandardErrorPath=str(state / "launchd.err.log"),
    )
    return config


class Installer:
    def __init__(self, home, applications, apply):
        self.home, self.applications, self.apply = home, applications, apply
        self.state = home / ".local/state/agent-cli-updates"
        self.backup = self.state / "backups" / (datetime.now().strftime("%m-%d-%Y_%H%M%S") + f"_{os.getpid()}")
        self.defaults_before = {}
        self.changes = []

    def file(self, path, content, mode=None):
        # Preserve an existing symlink rather than replacing it with a regular file.
        destination = path.resolve()
        if not destination.is_relative_to(self.home.resolve()):
            raise ValueError(f"configuration target is outside this home: {path}")
        before = destination.read_bytes() if destination.exists() else None
        if before == content:
            if self.apply and mode is not None:
                destination.chmod(mode)
            return
        print(f"{'Apply' if self.apply else 'Would update'}: {path}")
        self.changes.append(str(path))
        if not self.apply:
            return
        if before is not None:
            backup = self.backup / destination.relative_to(self.home.resolve())
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup)
            backup.chmod(0o600)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if (destination.read_bytes() if destination.exists() else None) != before:
            raise RuntimeError(f"file changed during installation: {path}")
        temporary = destination.with_name(destination.name + f".{os.getpid()}.tmp")
        try:
            temporary.write_bytes(content)
            temporary.chmod(mode if mode is not None else (destination.stat().st_mode & 0o777 if before is not None else 0o600))
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)

    def preference(self, domain, key, value):
        previous = subprocess.run(["defaults", "read", domain, key], capture_output=True, text=True, timeout=10)
        wanted = "1" if value else "0"
        if previous.returncode == 0 and previous.stdout.strip() == wanted:
            return
        print(f"{'Apply' if self.apply else 'Would update'}: {domain} {key}={value}")
        self.defaults_before.setdefault(domain, {})[key] = previous.stdout.strip() if previous.returncode == 0 else None
        if self.apply:
            self.backup.mkdir(parents=True, exist_ok=True)
            (self.backup / "defaults-before.json").write_text(json.dumps(self.defaults_before, indent=2) + "\n")
            subprocess.run(["defaults", "write", domain, key, "-bool", str(value).lower()], check=True, timeout=10)
            observed = subprocess.run(["defaults", "read", domain, key], check=True, capture_output=True, text=True, timeout=10)
            if observed.stdout.strip() != wanted:
                raise RuntimeError(f"preference verification failed: {domain} {key}")

    def desktop_settings(self):
        for name, (relative, key, value) in SETTINGS.items():
            if not (self.applications / (name + ".app")).exists():
                continue
            path = self.home / relative
            text = path.read_bytes().decode() if path.exists() else "{}\n"
            self.file(path, setting(text, key, value).encode())
        for name in SPARKLE_APPS:
            app = self.applications / (name + ".app")
            if not (app / "Contents/Frameworks/Sparkle.framework").exists():
                continue
            info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
            for key in ("SUEnableAutomaticChecks", "SUAutomaticallyUpdate"):
                self.preference(info["CFBundleIdentifier"], key, True)
        # Native Claude policy key from the installed desktop configuration schema.
        # This changes user preferences, not managed device policy.
        if (self.applications / "Claude.app").exists():
            self.preference("com.anthropic.claudefordesktop", "disableAutoUpdates", False)
        for name in NATIVE_APPS:
            if (self.applications / (name + ".app")).exists():
                print(f"Native desktop updater retained: {name}; no app was quit or relaunched.")

    def install(self):
        self.desktop_settings()
        launcher = ROOT / "dotfiles/agent-updates/auto-update-agent-clis"
        self.file(self.home / ".local/bin/auto-update-agent-clis", launcher.read_bytes(), 0o755)
        plist = self.home / "Library/LaunchAgents" / (LABEL + ".plist")
        existing = plistlib.loads(plist.read_bytes()) if plist.exists() else {}
        self.file(plist, plistlib.dumps(agent_plist(self.home, existing)), 0o644)
        if self.apply:
            self.state.mkdir(parents=True, exist_ok=True)
            self.state.chmod(0o700)
            for name in ("update.log", "launchd.out.log", "launchd.err.log"):
                path = self.state / name
                path.touch(exist_ok=True)
                path.chmod(0o600)
        return plist


def reload_job(plist):
    domain = f"gui/{os.getuid()}"
    service = f"{domain}/{LABEL}"
    # Hold the same package-manager lock across reload. A PID-only check races
    # with calendar/session-start launches and misses direct updater invocations.
    for _ in range(61):
        with update_lock(lock_path(Path.home())) as acquired:
            if acquired:
                status = subprocess.run(["launchctl", "print", service], capture_output=True, text=True, timeout=10)
                if status.returncode == 0:
                    subprocess.run(["launchctl", "bootout", service], check=True, timeout=20)
                subprocess.run(["launchctl", "enable", service], check=True, timeout=20)
                subprocess.run(["launchctl", "bootstrap", domain, str(plist)], check=True, timeout=20)
                break
        time.sleep(5)
    else:
        raise RuntimeError("existing updater is still running; configuration saved, reload deferred")
    # No -k: an already running job must not be killed. RunAtLoad may have
    # observed the held lock, so also request a normal start after releasing it.
    subprocess.run(["launchctl", "kickstart", service], check=True, timeout=20)
    observed = subprocess.run(["launchctl", "print", service], check=True, capture_output=True, text=True, timeout=10)
    if str(plist) not in observed.stdout:
        raise RuntimeError("loaded job does not match the installed plist")
    print("LaunchAgent loaded and enabled; login/daily checks plus hourly retries are active.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write settings and install the LaunchAgent")
    parser.add_argument("--no-reload", action="store_true", help="write configuration without changing the loaded job")
    args = parser.parse_args(argv)
    if sys.platform != "darwin":
        parser.error("the installer requires macOS")
    os.umask(0o077)
    installer = Installer(Path.home(), Path("/Applications"), args.apply)
    plist = installer.install()
    if args.apply and not args.no_reload:
        reload_job(plist)
    if args.apply and installer.backup.exists():
        print(f"Private backups: {installer.backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
