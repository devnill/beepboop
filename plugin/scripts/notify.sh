#!/bin/sh
# Send a desktop notification via OSC escape sequences.
# Priority: OSC 777 > OSC 9 > osascript (macOS fallback)
# Multiplexers: wraps sequences in DCS passthrough for tmux and GNU screen.

TITLE="${1:-Claude Code}"
BODY="${2:-}"
SETTINGS="${CLAUDE_PLUGIN_ROOT}/settings.json"

# Skip if explicitly disabled
[ -f "$SETTINGS" ] && grep -q '"notifications_enabled": *false' "$SETTINGS" && exit 0

# --- Multiplexer detection ---

in_tmux() {
    [ -n "$TMUX" ] && return 0
    case "$TERM" in tmux*) return 0 ;; esac
    return 1
}

in_screen() {
    [ -n "$STY" ] && return 0
    case "$TERM" in screen*) return 0 ;; esac
    return 1
}

# --- OSC capability of the outer terminal ---
# Returns: "osc777", "osc9", or "none"

osc_type() {
    # OSC 777: Ghostty
    [ -n "$GHOSTTY_RESOURCES_DIR" ] && echo "osc777" && return
    # OSC 9: iTerm2, WezTerm, VSCode, Hyper
    [ "$TERM_PROGRAM" = "iTerm.app" ] && echo "osc9" && return
    [ -n "$WEZTERM_EXECUTABLE" ] && echo "osc9" && return
    [ "$TERM_PROGRAM" = "vscode" ] && echo "osc9" && return
    [ "$TERM_PROGRAM" = "Hyper" ] && echo "osc9" && return
    echo "none"
}

# --- Sequence builders ---

build_osc777() { printf '\033]777;notify;%s;%s\a' "$TITLE" "$BODY"; }
build_osc9()   { printf '\033]9;%s: %s\a' "$TITLE" "$BODY"; }

# --- Output with optional DCS passthrough ---

send_seq() {
    seq="$1"
    if in_tmux; then
        # tmux requires inner ESC to be doubled
        printf '\033Ptmux;\033%s\033\\' "$seq" > /dev/tty
    elif in_screen; then
        printf '\033P%s\033\\' "$seq" > /dev/tty
    else
        printf '%s' "$seq" > /dev/tty
    fi
}

# --- macOS fallback ---

macos_notify() {
    if command -v terminal-notifier >/dev/null 2>&1; then
        terminal-notifier -title "$TITLE" -message "$BODY" 2>/dev/null
        return
    fi
    osascript -e "display notification \"$BODY\" with title \"$TITLE\"" 2>/dev/null
}

# --- Main ---

TYPE="$(osc_type)"
case "$TYPE" in
    osc777) send_seq "$(build_osc777)" ;;
    osc9)   send_seq "$(build_osc9)" ;;
    none)   ;;
esac

# On macOS, always fire a system notification as a reliable fallback.
# OSC passthrough in tmux requires `set -g allow-passthrough on` in .tmux.conf
# (disabled by default since tmux 3.3), so system notifications are the only
# guaranteed path inside tmux.
[ "$(uname)" = "Darwin" ] && macos_notify

exit 0
