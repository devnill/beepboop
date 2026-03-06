---
description: Configure beepboop plugin settings (sounds and notifications)
argument-hint: "[show | enable sounds | disable sounds | enable notifications | disable notifications | set <hook> <soundname> | volume <0.0-1.0>]"
allowed-tools: Read, Edit, Bash
---

Manage the beepboop plugin configuration.

Find the settings file:
```bash
find ~/.claude/plugins/cache/beepboop -name "settings.json" | sort -V | tail -1
```

Use the path returned above for all read/write operations.

## Actions

**No args or "show":** Read the settings file and display a summary:
- Show `sounds_enabled` and `notifications_enabled` as Enabled/Disabled
- Show `volume` as a decimal value
- Show a table with each hook name and its assigned sound (filename only, not full path)

**"enable sounds":** Set `sounds_enabled` to `true`

**"disable sounds":** Set `sounds_enabled` to `false`

**"enable notifications":** Set `notifications_enabled` to `true`

**"disable notifications":** Set `notifications_enabled` to `false`

**"set <HookName> <SoundName>":** Update `hook_sounds.<HookName>` in the settings file.

**"volume <value>":** Set `volume` to the given float value (0.0–1.0) in the settings file. This controls the `afplay -v` playback multiplier.

After any change, confirm what was updated and show the new value.
