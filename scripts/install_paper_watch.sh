#!/usr/bin/env bash
# install_paper_watch.sh — install (or reinstall) the writer-independent paper auto-compile watcher as a
# macOS launchd user agent, so every paper PDF refreshes itself after ANY edit (Cursor, agents, git pull),
# on every login and after reboots.
#
# TLDR: writes ~/Library/LaunchAgents/com.brando.paper-watch.plist running scripts/paper_watch.py over the
# given repos (default: ~/veribench), loads it with launchctl, and prints its status. Re-run to change repos.
#
# Usage: bash ~/agents-config/scripts/install_paper_watch.sh [REPO ...]
#        bash ~/agents-config/scripts/install_paper_watch.sh --uninstall
set -euo pipefail
label=com.brando.paper-watch
plist="$HOME/Library/LaunchAgents/$label.plist"
watcher="$HOME/agents-config/scripts/paper_watch.py"
uid=$(id -u)

if [[ "${1:-}" == "--uninstall" ]]; then
  launchctl bootout "gui/$uid/$label" 2>/dev/null || true
  rm -f "$plist"; echo "uninstalled $label"; exit 0
fi

repos=("$@"); [[ ${#repos[@]} -eq 0 ]] && repos=("$HOME/veribench")
python3=$(command -v python3)
args=""
for r in "${repos[@]}"; do args+="    <string>$r</string>"$'\n'; done

mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key><array>
    <string>$python3</string>
    <string>$watcher</string>
    <string>--interval</string><string>2</string>
$args  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ProcessType</key><string>Background</string>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/paper_watch.stdout.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/paper_watch.stderr.log</string>
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>/usr/local/texlive/2024/bin/universal-darwin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
  </dict>
</dict></plist>
EOF

launchctl bootout "gui/$uid/$label" 2>/dev/null || true
launchctl bootstrap "gui/$uid" "$plist"
launchctl kickstart -k "gui/$uid/$label" 2>/dev/null || true
sleep 2
echo "installed $label watching: ${repos[*]}"
launchctl print "gui/$uid/$label" 2>/dev/null | grep -E "state = |pid = " | head -2
echo "log: ~/Library/Logs/paper_watch.log"; tail -n 3 "$HOME/Library/Logs/paper_watch.log" 2>/dev/null || true
