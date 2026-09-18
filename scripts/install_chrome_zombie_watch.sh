#!/usr/bin/env bash
# install_chrome_zombie_watch.sh — launchd tripwire for a wedged Google Chrome zombie leak.
#
# TLDR: every 5 min runs chrome_zombie_watch.py --quit-if-wedged --notify; kills Chrome only
# when it already has >=100 zombie children (09-17-2026 stall), never on a healthy timer.
#
# Usage: bash ~/agents-config/scripts/install_chrome_zombie_watch.sh
#        bash ~/agents-config/scripts/install_chrome_zombie_watch.sh --uninstall
set -euo pipefail
label=com.brando.chrome-zombie-watch
plist="$HOME/Library/LaunchAgents/$label.plist"
watcher="$HOME/agents-config/scripts/chrome_zombie_watch.py"
uid=$(id -u)
python3=$(command -v python3)

if [[ "${1:-}" == "--uninstall" ]]; then
  launchctl bootout "gui/$uid/$label" 2>/dev/null || true
  rm -f "$plist"
  echo "uninstalled $label"
  exit 0
fi

chmod +x "$watcher"
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key><array>
    <string>$python3</string>
    <string>$watcher</string>
    <string>--quit-if-wedged</string>
    <string>--notify</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>StartInterval</key><integer>300</integer>
  <key>ProcessType</key><string>Background</string>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/chrome_zombie_watch.stdout.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/chrome_zombie_watch.stderr.log</string>
</dict></plist>
EOF

launchctl bootout "gui/$uid/$label" 2>/dev/null || true
launchctl bootstrap "gui/$uid" "$plist"
launchctl kickstart -k "gui/$uid/$label" 2>/dev/null || true
sleep 1
echo "installed $label (every 300s, SIGKILL Chrome only if zombie children >= 100)"
launchctl print "gui/$uid/$label" 2>/dev/null | grep -E "state = |pid = |runs =" | head -5
echo "check: python3 $watcher --check"
echo "log: ~/Library/Logs/chrome_zombie_watch.log"
