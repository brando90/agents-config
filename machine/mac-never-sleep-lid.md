# Mac Lid Never Sleeps Prompt
**TLDR:** Use this prompt when Brando says a Mac should never sleep, especially when the lid closes. The durable core is `pmset disablesleep 1`; if the live lid flag still says closing the lid causes sleep, enable Amphetamine Closed-Display Mode and report that fallback explicitly.

## Copy-Paste User Prompt

```text
This Mac must never sleep, including when I close the lid. Do not store my Mac login password anywhere, including ~/keys. Make the setting durable across reboot and login, run it now, and verify the lid-close flag.

Implementation requirements:
- Use `sudo pmset -a disablesleep 1 sleep 0 disksleep 0 displaysleep 0 standby 0 autopoweroff 0 powernap 0` as the core command.
- Install a root LaunchDaemon at `/Library/LaunchDaemons/com.brando.never-sleep.pmset.plist` that runs that exact `pmset` command at load and every 300 seconds.
- If `AppleClamshellCausesSleep` remains `Yes` after `pmset`, configure Amphetamine Closed-Display Mode with AppleScript and verify it is enabled.
- If adding a caffeinate fallback, use `/usr/bin/caffeinate -dims`, not `-dimsu`; `-u` is a short user-active pulse and can cause a launchd restart loop.
- If adding a shell startup fallback in `~/.zshrc`, make it duplicate-safe and use `sudo -n` only after configuring a narrow sudoers rule for the exact `pmset` command.
- Never save a plaintext Mac password. Use an interactive sudo prompt once, or a narrowly scoped sudoers rule for the exact command.

Verification requirements:
- `pmset -g live` must show `SleepDisabled 1`, `sleep 0`, `displaysleep 0`, `disksleep 0`, and `standby 0`.
- `ioreg -r -k AppleClamshellCausesSleep -d 1 | /usr/bin/grep -E 'AppleClamshellCausesSleep|AppleClamshellState|SleepDisabled'` must be checked and reported. The ideal result is `AppleClamshellCausesSleep = No` and `SleepDisabled = Yes`; if it remains `Yes`, do not claim the lid-close path is solved until Amphetamine Closed-Display Mode is enabled and verified.
- If Amphetamine is used, `osascript -e 'tell application "Amphetamine" to enable closed display mode'` must exit `0`, `session is active` must return `true`, and `display sleep allowed` must return `false`. If the installed Amphetamine dictionary supports `closed display mode enabled`, that query must return `true`; if it is unsupported, report that explicitly and include the supported AppleScript checks instead.
- `launchctl print system/com.brando.never-sleep.pmset` must show the daemon is loaded, `run interval = 300 seconds`, and `last exit code = 0` after it runs.
- Report the exact files installed and the verification output.
```

## Agent Procedure

1. Refresh `~/agents-config` and load `~/agents-config/INDEX_RULES.md`, then load `~/agents-config/machine/mac.md`.
2. Inspect the current state:

```bash
pmset -g live
pmset -g custom
ioreg -r -k AppleClamshellCausesSleep -d 1 | /usr/bin/grep -E 'AppleClamshellCausesSleep|AppleClamshellState|SleepDisabled'
```

3. Run the no-sleep setting immediately:

```bash
sudo /usr/bin/pmset -a disablesleep 1 sleep 0 disksleep 0 displaysleep 0 standby 0 autopoweroff 0 powernap 0
```

4. Install this LaunchDaemon as root-owned, mode `0644`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.brando.never-sleep.pmset</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/pmset</string>
    <string>-a</string>
    <string>disablesleep</string>
    <string>1</string>
    <string>sleep</string>
    <string>0</string>
    <string>disksleep</string>
    <string>0</string>
    <string>displaysleep</string>
    <string>0</string>
    <string>standby</string>
    <string>0</string>
    <string>autopoweroff</string>
    <string>0</string>
    <string>powernap</string>
    <string>0</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>StartInterval</key>
  <integer>300</integer>
  <key>StandardOutPath</key>
  <string>/var/log/never-sleep-pmset.log</string>
  <key>StandardErrorPath</key>
  <string>/var/log/never-sleep-pmset.err</string>
</dict>
</plist>
```

Save the XML above to `/tmp/com.brando.never-sleep.pmset.plist`, then install it:

```bash
plutil -lint /tmp/com.brando.never-sleep.pmset.plist
sudo install -o root -g wheel -m 0644 /tmp/com.brando.never-sleep.pmset.plist /Library/LaunchDaemons/com.brando.never-sleep.pmset.plist
sudo launchctl bootout system /Library/LaunchDaemons/com.brando.never-sleep.pmset.plist 2>/dev/null || true
sudo launchctl bootstrap system /Library/LaunchDaemons/com.brando.never-sleep.pmset.plist
sudo launchctl enable system/com.brando.never-sleep.pmset
sudo launchctl kickstart -k system/com.brando.never-sleep.pmset
```

5. Check the lid-close flag. If it remains `Yes`, enable Amphetamine Closed-Display Mode:

```bash
ioreg -r -k AppleClamshellCausesSleep -d 1 | /usr/bin/grep -E 'AppleClamshellCausesSleep|AppleClamshellState|SleepDisabled'
if osascript -e 'id of app "Amphetamine"' >/dev/null 2>&1; then
  osascript -e 'tell application "Amphetamine" to start new session with options {duration:0, interval:minutes, displaySleepAllowed:false}'
  osascript -e 'tell application "Amphetamine" to enable closed display mode'
  osascript -e 'tell application "Amphetamine" to session is active'
  osascript -e 'tell application "Amphetamine" to display sleep allowed'
  osascript -e 'tell application "Amphetamine" to closed display mode enabled' 2>/dev/null || \
    echo "Amphetamine dictionary did not expose 'closed display mode enabled'; report supported AppleScript checks above."
else
  echo "Amphetamine is not installed; install/configure it interactively if AppleClamshellCausesSleep remains Yes."
fi
```

Expected supported Amphetamine outputs are exit `0` for enabling Closed-Display
Mode, then `true` for `session is active` and `false` for `display sleep
allowed`. If the optional `closed display mode enabled` query works, it must
return `true`. If Amphetamine is not installed and the lid flag remains `Yes`,
tell Brando that `pmset` is applied but the Mac still needs a closed-display
helper before the request is complete. If Amphetamine asks to install Power
Protect or a closed-display helper script on Apple Silicon, complete that setup
interactively with Touch ID/admin authentication; do not automate or save the
password.

6. Optional shell fallback in `~/.zshrc`:

Only add the `sudo -n pmset` line after installing the exact narrow sudoers rule
below. Without that rule, omit the sudo line and rely on the root LaunchDaemon.
Do not broaden the rule with wildcards or alternate command paths.

```bash
if [[ -o interactive && "$OSTYPE" == darwin* ]]; then
  /usr/bin/sudo -n /usr/bin/pmset -a disablesleep 1 sleep 0 disksleep 0 displaysleep 0 standby 0 autopoweroff 0 powernap 0 2>/dev/null || true

  if ! /usr/bin/pgrep -fq "^/usr/bin/caffeinate -dims$"; then
    /usr/bin/caffeinate -dims >/tmp/caffeinate-never-sleep.log 2>&1 < /dev/null &!
  fi
fi
```

If `sudo -n` should work in shell startup, install only this narrow sudoers rule:

```sudoers
<mac-username> ALL=(root) NOPASSWD: /usr/bin/pmset -a disablesleep 1 sleep 0 disksleep 0 displaysleep 0 standby 0 autopoweroff 0 powernap 0
```

Validate any sudoers file before installing:

```bash
sudo visudo -cf /tmp/codex-pmset-never-sleep.sudoers
sudo install -o root -g wheel -m 0440 /tmp/codex-pmset-never-sleep.sudoers /etc/sudoers.d/codex-pmset-never-sleep
sudo visudo -cf /etc/sudoers
```

7. Optional user-space `caffeinate` LaunchAgent:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.brando.caffeinate-never-sleep</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/caffeinate</string>
    <string>-dims</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>/tmp/caffeinate-never-sleep.launchd.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/caffeinate-never-sleep.launchd.err</string>
</dict>
</plist>
```

8. Final verification:

```bash
pmset -g ps
pmset -g live
ioreg -r -k AppleClamshellCausesSleep -d 1 | /usr/bin/grep -E 'AppleClamshellCausesSleep|AppleClamshellState|SleepDisabled'
launchctl print system/com.brando.never-sleep.pmset | sed -n '1,120p'
osascript -e 'tell application "Amphetamine" to session is active' 2>/dev/null || true
osascript -e 'tell application "Amphetamine" to closed display mode enabled' 2>/dev/null || true
osascript -e 'tell application "Amphetamine" to display sleep allowed' 2>/dev/null || true
launchctl print gui/$(id -u)/com.brando.caffeinate-never-sleep 2>/dev/null | sed -n '1,120p' || true
```

## Notes

- The preferred lid-close success condition is `AppleClamshellCausesSleep = No`; do not report success using only `caffeinate` assertions.
- On some MacBook power states, especially battery, `SleepDisabled = Yes` can coexist with `AppleClamshellCausesSleep = Yes`. In that case, use Amphetamine Closed-Display Mode and report both the `ioreg` value and the Amphetamine AppleScript state.
- Amphetamine can hold `PreventUserIdleSystemSleep` and `PreventUserIdleDisplaySleep` without proving Closed-Display Mode is enabled; do not treat generic power assertions as a substitute for the Amphetamine AppleScript checks above.
- Amphetamine's public AppleScript docs document `enable closed display mode`,
  `session is active`, and `display sleep allowed`; use those supported checks,
  and treat `closed display mode enabled` as an optional local-dictionary query.
- `caffeinate -s` only creates the system-sleep assertion on AC power. It is useful as a fallback but is not the durable lid-close control.
- Never put a Mac login password in `~/keys`, `.zshrc`, LaunchDaemon plists, shell history, or scripts.
