#!/bin/sh
# Play a sound for the given Claude Code hook event.
# Checks sounds/ directory first, falls back to settings.json path.
# Usage: play-sound.sh <HookName>
HOOK="${1:-}"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
SETTINGS="${PLUGIN_ROOT}/settings.json"

[ -z "$HOOK" ] && exit 0
[ -f "$SETTINGS" ] || exit 0

grep -q '"sounds_enabled": *false' "$SETTINGS" && exit 0

# Prefer bundled WAV from sounds/ directory
SOUND="${PLUGIN_ROOT}/sounds/${HOOK}.wav"

# Fall back to path specified in settings.json
if [ ! -f "$SOUND" ]; then
  SOUND=$(grep "\"$HOOK\":" "$SETTINGS" | sed 's/.*": *"\(.*\)".*/\1/')
fi

VOLUME=$(grep '"volume":' "$SETTINGS" | sed 's/.*: *\([0-9.]*\).*/\1/')
VOLUME="${VOLUME:-0.2}"

[ -n "$SOUND" ] && [ -f "$SOUND" ] && afplay -v "$VOLUME" "$SOUND" &
exit 0
