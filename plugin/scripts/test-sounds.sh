#!/bin/bash
# Test all beepboop hook sounds in sequence.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLAY="$SCRIPT_DIR/play-sound.sh"

HOOKS=(
  SessionStart
  UserPromptSubmit
  PreToolUse
  PermissionRequest
  PostToolUse
  PostToolUseFailure
  Notification
  SubagentStart
  SubagentStop
  Stop
  TeammateIdle
  TaskCompleted
  InstructionsLoaded
  ConfigChange
  WorktreeCreate
  WorktreeRemove
  PreCompact
  SessionEnd
)

for HOOK in "${HOOKS[@]}"; do
  echo "$HOOK"
  "$PLAY" "$HOOK"
  
done
