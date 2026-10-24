---
description: Configure beepboop plugin settings (sounds and notifications)
argument-hint: "[show | enable sounds | disable sounds | enable notifications | disable notifications | volume <0.0-1.0> | player <path>]"
allowed-tools: Read, Edit, Bash
---

Manage the beepboop plugin configuration.

Find the settings file:
```bash
find ~/.claude/plugins/cache -path '*/beepboop/*' -name settings.json | sort -V | tail -1
```

Use the path returned above for all read/write operations. The plugin dir is the directory containing that settings.json.

## Actions

**No args or "show":** Read the settings file and display a summary:
- Show `sounds_enabled` and `notifications_enabled` as Enabled/Disabled
- Show `volume` as a decimal value
- Show `player` value (or "auto-detect" if empty)
- List the bundled sounds: the hook names from `<plugin dir>/sounds/*.wav` (filename without `.wav`), with a count

**"enable sounds":** Set `sounds_enabled` to `true`

**"disable sounds":** Set `sounds_enabled` to `false`

**"enable notifications":** Set `notifications_enabled` to `true`

**"disable notifications":** Set `notifications_enabled` to `false`

**"volume <value>":** Set `volume` to the given float value (0.0–1.0) in the settings file. This controls the playback volume multiplier (supported players: afplay, paplay).

**"player <path>":** Set `player` to the given executable path in the settings file. Use an empty string (`player ""`) to reset to auto-detect on next run. Supported players: `afplay`, `aplay`, `paplay`, `pw-play`, `powershell`, `powershell.exe`.

After any change, confirm what was updated and show the new value.
