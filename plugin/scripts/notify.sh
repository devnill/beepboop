#!/bin/sh
# Send a desktop notification via OSC escape sequences.
# Usage: notify.sh <title> <body>
#
# Terminals:
#   - Ghostty: OSC 777 (notify;title;body)
#   - iTerm2/VSCode/WezTerm: OSC 9 (title: body)
#   - tmux/screen: wrap OSC in DCS passthrough
#   - Unknown + macOS: fallback to osascript or terminal-notifier

TITLE="${1:-Claude Code}"
BODY="${2:-}"
SETTINGS="${CLAUDE_PLUGIN_ROOT}/settings.json"

# Skip if explicitly disabled
[ -f "$SETTINGS" ] && grep -q '"notifications_enabled": *false' "$SETTINGS" && exit 0

# Check if we're in a known terminal that supports OSC
is_known_terminal() {
    [ -n "$GHOSTTY_RESOURCES_DIR" ] && return 0
    [ "$TERM_PROGRAM" = "iTerm.app" ] && return 0
    [ "$TERM_PROGRAM" = "vscode" ] && return 0
    [ "$TERM_PROGRAM" = "Apple_Terminal" ] && return 0
    [ "$TERM_PROGRAM" = "Hyper" ] && return 0
    [ -n "$WEZTERM_EXECUTABLE" ] && return 0
    case "$TERM" in tmux*|screen*) return 0 ;; esac
    [ -n "$TMUX" ] && return 0
    return 1
}

# Build the OSC sequence
build_osc() {
    if [ -n "$GHOSTTY_RESOURCES_DIR" ]; then
        printf '\033]777;notify;%s;%s\a' "$TITLE" "$BODY"
    else
        printf '\033]9;%s: %s\a' "$TITLE" "$BODY"
    fi
}

# Fallback for macOS with unknown terminal
macos_fallback() {
    # Prefer terminal-notifier if available (doesn't open Script Editor on click)
    if command -v terminal-notifier >/dev/null 2>&1; then
        terminal-notifier -title "$TITLE" -message "$BODY" 2>/dev/null
        return
    fi
    # Fall back to osascript (clicking opens Script Editor)
    osascript -e "display notification \"$BODY\" with title \"$TITLE\"" 2>/dev/null
}

# Main logic
if is_known_terminal; then
    SEQ="$(build_osc)"
    # Wrap in DCS passthrough for tmux/screen
    case "$TERM" in
        tmux*|screen*)
            printf '\033Ptmux;\033%s\033\\' "$SEQ"
            ;;
        *)
            printf '%s' "$SEQ"
            ;;
    esac
elif [ "$(uname)" = "Darwin" ]; then
    macos_fallback
fi

exit 0