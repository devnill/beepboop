# beepboop

A Claude Code plugin that plays sounds on every hook event and sends Ghostty OSC 777 desktop notifications when Claude needs attention.

## Features

- Plays a distinct sound for each of the 18 Claude Code hook events
- Sends desktop notifications (via Ghostty OSC 777) when Claude finishes a task or needs input
- Configurable via `/beepboop:config` skill

## Install

From within Claude Code:

```
/plugin marketplace add /path/to/beepboop
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
/beepboop:config disable notifications   # turn notifications off
/beepboop:config set Stop Hero           # change Stop hook sound
/beepboop:config volume 0.5             # set playback volume (0.0–1.0, default 0.2)
```

Config file: `~/.claude/plugins/cache/beepboop/beepboop/<version>/settings.json`

## Notifications

Notifications work across multiple terminals with automatic detection:

- **Ghostty** — OSC 777 (requires `desktop-notifications = true` in `~/.config/ghostty/config`)
- **VSCode, iTerm2, WezTerm** — OSC 9 escape sequence
- **Other terminals on macOS** — `osascript` system notification (clicking focuses your terminal app, not Script Editor)
