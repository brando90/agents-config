#!/usr/bin/env bash
# pre-grant-tcc-automation.sh
#
# Batch-trigger macOS Automation TCC prompts for `node` controlling each
# app OpenClaw might script.  Brando clicks "Allow" once per app; the
# (node → <App>) pair is then permanent.  After running this once per
# host, the agent will never block on an Automation TCC dialog mid-task.
#
# Usage:
#   bash ~/agents-config/experiments/01_self_hosted_openclaw/scripts/pre-grant-tcc-automation.sh
#
# Per app, it sends a harmless `osascript -e 'tell application "X" to count windows'`
# which forces macOS to show the prompt.  Click "Allow" on each.  Closing
# without allowing means the agent will hit the prompt later.
#
# To check what's already granted:
#   System Settings → Privacy & Security → Automation → expand "node"
#
# Add new entries to APPS=( ... ) as the agent's surface grows.

set -u

APPS=(
  "Mail"                        # Apple Mail
  "Microsoft Outlook"           # Stanford email client
  "Calendar"                    # Apple Calendar
  "Reminders"
  "Notes"
  "Messages"                    # iMessage bridge
  "Music"                       # Apple Music control
  "Photos"                      # Drive→social photo pipeline (if Photos used)
  "Safari"                      # for Playwright fallback flows
  "Google Chrome"               # ditto
  "Finder"                      # generic file ops
  "Slack"                       # Lean-AI / community pings
  "Discord"                     # Lean-AI server
  "Spotify"                     # optional, "play music" QoL
  "System Events"               # AppleScript GUI scripting (only if Accessibility flow needed)
)

echo "🦞 OpenClaw — pre-granting macOS Automation TCC prompts for node"
echo "Total apps: ${#APPS[@]}"
echo "Watch for: \"node wants access to control \"<App>\"\" prompts; click Allow on each."
echo

for app in "${APPS[@]}"; do
  printf "  %-22s ... " "$app"
  # `count windows` is harmless and works on any scriptable app.
  # `&` so we don't block on the prompt itself; the prompt blocks osascript
  # but we want all prompts to fire roughly in sequence so Brando can
  # click through them.  Use a 3s grace per app.
  ( osascript -e "tell application \"$app\" to count windows" >/dev/null 2>&1 || true ) &
  sleep 3
  echo "prompt fired"
done

wait
echo
echo "Done. Open System Settings → Privacy & Security → Automation → 'node' to confirm."
echo "Apps you didn't see prompts for are either already granted or not installed."
