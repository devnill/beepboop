#!/bin/sh
# Send a Ghostty OSC 777 desktop notification.
# Usage: notify.sh <title> <body>
# Requires: desktop-notifications = true in ~/.config/ghostty/config
TITLE="${1:-Claude Code}"
BODY="${2:-}"
SETTINGS="${CLAUDE_PLUGIN_ROOT}/settings.json"

[ -f "$SETTINGS" ] && grep -q '"notifications_enabled": *false' "$SETTINGS" && exit 0

printf '\033]777;notify;%s;%s\a' "$TITLE" "$BODY" > /dev/tty
exit 0
