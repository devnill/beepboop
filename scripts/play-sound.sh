#!/bin/sh
# Play a macOS system sound for the given Claude hook event.
# Usage: play-sound.sh <HookName>
HOOK="${1:-}"
SETTINGS="${CLAUDE_PLUGIN_ROOT}/settings.json"

[ -z "$HOOK" ] && exit 0
[ -f "$SETTINGS" ] || exit 0

grep -q '"sounds_enabled": *false' "$SETTINGS" && exit 0

SOUND=$(grep "\"$HOOK\":" "$SETTINGS" | sed 's/.*": *"\(.*\)".*/\1/')

[ -n "$SOUND" ] && afplay "$SOUND" &
exit 0
