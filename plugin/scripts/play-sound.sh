#!/bin/sh
# Play a sound for the given Claude Code hook event.
# Checks sounds/ directory first, falls back to settings.json path.
# Usage: play-sound.sh <HookName>
HOOK="${1:-}"
SETTINGS="${CLAUDE_PLUGIN_ROOT}/settings.json"

[ -z "$HOOK" ] && exit 0
[ -f "$SETTINGS" ] || exit 0

grep -q '"sounds_enabled": *false' "$SETTINGS" && exit 0

# Prefer bundled WAV from sounds/ directory
SOUND="${CLAUDE_PLUGIN_ROOT}/plugin/sounds/${HOOK}.wav"

# Fall back to path specified in settings.json
if [ ! -f "$SOUND" ]; then
  SOUND=$(grep "\"$HOOK\":" "$SETTINGS" | sed 's/.*": *"\(.*\)".*/\1/')
fi

[ -n "$SOUND" ] && [ -f "$SOUND" ] && afplay "$SOUND" &
exit 0
