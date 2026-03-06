---
name: config
description: Configure beepboop plugin settings (sounds and notifications)
argument-hint: "[enable sounds | disable sounds | enable notifications | disable notifications | set <hook> <soundname> | show]"
allowed-tools: Read, Edit, Bash
disable-model-invocation: true
user-invocable: true
---

Manage the beepboop plugin configuration at `$HOME/.claude/plugins/beepboop/settings.json`.

**Settings file path:** `$HOME/.claude/plugins/beepboop/settings.json`

## Available macOS system sounds

The following sound names are available in `/System/Library/Sounds/`:
Basso, Blow, Bottle, Frog, Funk, Glass, Hero, Morse, Ping, Pop, Purr, Sosumi, Submarine, Tink

Use the full path when setting: `/System/Library/Sounds/<Name>.aiff`

## Commands

**No args or "show":** Read the settings file and display a human-friendly summary:
- Show `sounds_enabled` and `notifications_enabled` as Enabled/Disabled
- Show a table with each hook name and its assigned sound (just the filename, not full path)
- Format as a readable table with aligned columns

**"enable sounds":** Set `sounds_enabled` to `true`

**"disable sounds":** Set `sounds_enabled` to `false`

**"enable notifications":** Set `notifications_enabled` to `true`

**"disable notifications":** Set `notifications_enabled` to `false`

**"set <HookName> <SoundName>":** Update `hook_sounds.<HookName>` to `/System/Library/Sounds/<SoundName>.aiff`
- Example: `set Stop Hero` → sets Stop hook to `/System/Library/Sounds/Hero.aiff`
- Validate that the sound file exists before writing

After any change, confirm what was updated and show the new value.
