#!/bin/sh
# Play a sound for the given Claude Code hook event.
# Checks sounds/ directory first, falls back to settings.json path.
# Auto-detects an available audio player on first run and caches it in settings.json.
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

[ -n "$SOUND" ] && [ -f "$SOUND" ] || exit 0

# --- Player detection and caching ---

detect_player() {
  case "$(uname -s)" in
    Darwin)
      echo "/usr/bin/afplay"
      ;;
    Linux)
      if [ -n "$WSL_DISTRO_NAME" ] || grep -qi microsoft /proc/version 2>/dev/null; then
        for cmd in aplay paplay pw-play; do
          command -v "$cmd" >/dev/null 2>&1 && command -v "$cmd" && return
        done
        command -v powershell.exe >/dev/null 2>&1 && command -v powershell.exe
      else
        for cmd in aplay paplay pw-play; do
          command -v "$cmd" >/dev/null 2>&1 && command -v "$cmd" && return
        done
      fi
      ;;
    MINGW*|MSYS*)
      command -v powershell >/dev/null 2>&1 && command -v powershell
      ;;
  esac
}

PLAYER=$(python3 -c "import json; f=open('$SETTINGS'); cfg=json.load(f); f.close(); print(cfg.get('player',''))" 2>/dev/null)

if [ -z "$PLAYER" ]; then
  PLAYER=$(detect_player)
  if [ -n "$PLAYER" ]; then
    python3 -c "
import json
with open('$SETTINGS') as f: cfg = json.load(f)
cfg['player'] = '$PLAYER'
with open('$SETTINGS', 'w') as f: json.dump(cfg, f, indent=2)
" 2>/dev/null
  fi
fi

[ -n "$PLAYER" ] || exit 0

# --- Invoke player ---

PLAYER_BIN=$(basename "$PLAYER")
case "$PLAYER_BIN" in
  afplay)
    "$PLAYER" -v "$VOLUME" "$SOUND" &
    ;;
  paplay)
    PA_VOL=$(python3 -c "print(int($VOLUME * 65536))" 2>/dev/null || echo "13107")
    "$PLAYER" --volume="$PA_VOL" "$SOUND" &
    ;;
  aplay|pw-play)
    "$PLAYER" "$SOUND" &
    ;;
  powershell|powershell.exe)
    WIN_PATH=$(wslpath -w "$SOUND" 2>/dev/null || echo "$SOUND")
    "$PLAYER" -c "(New-Object Media.SoundPlayer '$WIN_PATH').PlaySync()" &
    ;;
  *)
    "$PLAYER" "$SOUND" &
    ;;
esac

exit 0
