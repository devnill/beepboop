# beepboop

A Claude Code plugin that plays macOS system sounds on every hook event and sends Ghostty OSC 777 desktop notifications when Claude needs attention.

## Features

- Plays a distinct system sound for each of the 18 Claude Code hook events
- Sends desktop notifications (via Ghostty OSC 777) when Claude finishes a task or needs input
- Fully configurable via `/beepboop:config` skill
- Takes over Stop and Notification hook responsibility from `~/.claude/settings.json`

## Install

From within Claude Code:

```
/plugin marketplace add /Users/dan/code/beepboop
/plugin install beepboop@beepboop
```

## Uninstall

```
/plugin uninstall beepboop@beepboop
/plugin marketplace remove beepboop
```

## Configuration

Use the `/beepboop:config` skill in Claude Code:

```
/beepboop:config                        # show current config
/beepboop:config enable sounds          # turn sounds on
/beepboop:config disable sounds         # turn sounds off
/beepboop:config enable notifications   # turn notifications on
/beepboop:config disable notifications  # turn notifications off
/beepboop:config set Stop Hero          # change Stop hook sound to Hero
```

Config file: `~/.claude/plugins/cache/beepboop/beepboop/1.0.0/settings.json`

## Sound Assignments

| Hook | Sound |
|------|-------|
| SessionStart | Pop |
| UserPromptSubmit | Tink |
| PreToolUse | Bottle |
| PermissionRequest | Basso |
| PostToolUse | Ping |
| PostToolUseFailure | Funk |
| Notification | Glass |
| SubagentStart | Purr |
| SubagentStop | Hero |
| Stop | Glass |
| TeammateIdle | Morse |
| TaskCompleted | Submarine |
| InstructionsLoaded | Blow |
| ConfigChange | Frog |
| WorktreeCreate | Sosumi |
| WorktreeRemove | Tink |
| PreCompact | Purr |
| SessionEnd | Pop |

## Notifications

Requires Ghostty with `desktop-notifications = true` in `~/.config/ghostty/config`.
