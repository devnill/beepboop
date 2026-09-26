#!/bin/bash
# Test all beepboop hook sounds in sequence.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLAY="$SCRIPT_DIR/play-sound.sh"

HOOKS=(
  SessionStart
  Setup
  UserPromptSubmit
  UserPromptExpansion
  MessageDisplay
  PreToolUse
  PermissionRequest
  PermissionDenied
  PostToolUse
  PostToolUseFailure
  PostToolBatch
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
  StopFailure
  TaskCreated
  PostCompact
  PreModelSwitch
  PostModelSwitch
  CwdChanged
  DirectoryAdded
  FileChanged
  Elicitation
  ElicitationResult
)

for HOOK in "${HOOKS[@]}"; do
  echo "$HOOK"
  "$PLAY" "$HOOK"
  
done
