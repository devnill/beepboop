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
/beepboop:config disable notifications  # turn notifications off
/beepboop:config set Stop Hero          # change Stop hook sound
```

Config file: `~/.claude/plugins/cache/beepboop/beepboop/<version>/settings.json`

## Notifications

Requires Ghostty with `desktop-notifications = true` in `~/.config/ghostty/config`.
