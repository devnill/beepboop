#!/bin/sh
# Send a desktop notification with terminal-aware degradation.
# Usage: notify.sh <title> <body>
#
# Detection order:
#   1. Ghostty  (GHOSTTY_RESOURCES_DIR set)   -> OSC 777
#   2. VSCode   (TERM_PROGRAM=vscode)         -> OSC 9
#   3. iTerm2   (TERM_PROGRAM=iTerm.app)      -> OSC 9
#   4. WezTerm  (WEZTERM_EXECUTABLE set)      -> OSC 9
#   5. Fallback                               -> osascript (macOS, focuses terminal on click)
TITLE="${1:-Claude Code}"
BODY="${2:-}"
SETTINGS="${CLAUDE_PLUGIN_ROOT}/settings.json"

[ -f "$SETTINGS" ] && grep -q '"notifications_enabled": *false' "$SETTINGS" && exit 0

if [ -n "$GHOSTTY_RESOURCES_DIR" ]; then
    printf '\033]777;notify;%s;%s\a' "$TITLE" "$BODY" > /dev/tty
elif [ "$TERM_PROGRAM" = "vscode" ]; then
    printf '\033]9;%s\a' "$TITLE: $BODY" > /dev/tty
elif [ "$TERM_PROGRAM" = "iTerm.app" ]; then
    printf '\033]9;%s\a' "$TITLE: $BODY" > /dev/tty
elif [ -n "$WEZTERM_EXECUTABLE" ]; then
    printf '\033]9;%s\a' "$TITLE: $BODY" > /dev/tty
else
    case "$TERM_PROGRAM" in
        Apple_Terminal) TERM_APP="Terminal" ;;
        iTerm.app)      TERM_APP="iTerm2" ;;
        Hyper)          TERM_APP="Hyper" ;;
        *)              TERM_APP="Terminal" ;;
    esac
    osascript -e "tell application \"$TERM_APP\" to display notification \"$BODY\" with title \"$TITLE\""
fi

exit 0
