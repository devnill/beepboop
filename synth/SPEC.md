# Beepboop Sound Synthesizer — Spec

## Goal

Generate a set of robot-style WAV files for each Claude Code hook event, replacing macOS system sounds. Character: R2D2-style beeps/boops/chirps. Output files are played via `afplay` and live in `synth/output/`.

---

## Technical Stack

| Concern | Decision |
|---|---|
| Language | Python 3.11+ |
| Libraries | `numpy`, `scipy` (build-time only, not bundled in plugin) |
| WAV format | 44100 Hz, 16-bit, mono |
| Output | `synth/output/<HookName>.wav` |
| Playback | `afplay` via existing `scripts/play-sound.sh` |
| Amplitude | 70% (0.7 peak) — matches macOS system sound levels |
| Regeneration | Overwrites existing files unconditionally |

---

## Synthesis Primitives

| Primitive | Use |
|---|---|
| **Sine wave** | Clean, smooth boops and chirps |
| **Square wave** | Harsh, digital tones (errors only) |
| **Frequency sweep** | Rising/falling chirps via phase accumulation (`np.cumsum`) |
| **FM synthesis** | Carrier + modulator for metallic/urgent robot tones |
| **ADSR envelope** | Exponential curves on every sound for natural feel |

---

## Sound Design Map — 12 Mapped Hooks

| Hook | Character | Waveform | Freq (Hz) | Duration | Notes |
|---|---|---|---|---|---|
| SessionStart | Warm startup chirp | Sine × 2 | 300 boop → 420→780 sweep | ~360ms | Two boops: low then rising |
| UserPromptSubmit | Short acknowledgment boop | Sine | 520 | 150ms | Clean, unobtrusive |
| PreToolUse | Quick click/tick | Sine | 900 | 60ms | Snappy, barely-there |
| PermissionRequest | Alert/question tone | FM | 480→576 (2 notes) | ~420ms | FM mod_index=3, rising inflection |
| PostToolUse | Soft confirmation bip | Sine | 660 | 100ms | Gentle, higher than submit |
| PostToolUseFailure | Low error buzz | Square, detuned | 160 + 170 | 450ms | Pulsed at 8Hz, beating dissonance |
| Notification | Bright ping | Sine + 2nd harmonic | 880 + 1760 | 350ms | Bell-like, long decay |
| SubagentStart | Rising chirp | Sine sweep | 400→1000 | 200ms | Fast upward sweep |
| SubagentStop | Descending chirp | Sine sweep (log) | 1000→350 | 220ms | Exponential down |
| Stop | Done/complete tone | Sine × 2 | 440→330 | ~380ms | Descending 2-note, conclusive |
| TaskCompleted | Happy multi-boop | Sine arpeggio | C5/E5/G5 (523/659/784) | ~430ms | Major triad, cheerful |
| TeammateIdle | Soft idle blip | Sine | 420 | 80ms | Extra quiet (~40% amplitude) |

---

## Sound Design Map — 6 Unmapped Hooks (Creative)

| Hook | Character | Waveform | Freq (Hz) | Duration | Notes |
|---|---|---|---|---|---|
| InstructionsLoaded | Data-reading chirp burst | Sine × 4 | 400/520/640/800 | ~330ms | 4 rapid ascending tones, R2D2 "reading" |
| ConfigChange | Settings switch | Sine × 2 | 440→370 | ~230ms | Descending major 2nd, mechanical click feel |
| WorktreeCreate | Branch spawn | Sine × 3 + ping | 330/440/550 + 880 | ~440ms | 3 ascending + bright ping (summoning) |
| WorktreeRemove | Branch dissolve | Sine sweep + wobble | 700→200 (log) + wobble | 300ms | Warbly falling sweep, "dissolving" |
| PreCompact | Memory compress | Sine sweep + fast wobble | 800→300 + 25Hz wobble | 350ms | Rapid descending warble, R2D2 "processing" |
| SessionEnd | Goodbye | Sine sweep + sine | 780→420 sweep + 300 | ~380ms | Mirror of SessionStart, reversed/softer |

---

## Synthesis Details

### ADSR (all sounds)
Exponential curves — more natural than linear:
- **Attack**: `1 - exp(-5t)` — quick rise
- **Decay/Release**: `exp(-5t) * (1-sustain) + sustain` — smooth fall

### Frequency Sweeps
Phase accumulation to avoid artifacts:
```python
phase = 2π * cumsum(freq_array) / sample_rate
signal = sin(phase)
```

### Detuning (PostToolUseFailure)
Two square waves at 160 Hz + 170 Hz — 10Hz beating creates dissonance without complex ring mod.

### FM (PermissionRequest)
`carrier=480Hz, modulator=480Hz, mod_index=3` → metallic urgency.
Second note at 576Hz (minor third up) creates rising question inflection.

### Creative Sounds
- **WorktreeRemove**: FM wobble fades out over time (`wobble * (1 - t/duration)`) for "dissolving" effect
- **PreCompact**: Fast 25Hz wobble on a descending sweep = R2D2 rapid processing chatter
- **InstructionsLoaded**: 4-tone rapid scan mirrors R2D2 reading an R2 unit

---

## App Structure

```
synth/
  SPEC.md          ← this file
  generate.py      ← run to regenerate all sounds
  requirements.txt ← numpy, scipy
  output/          ← generated WAV files (gitignored or committed)
    SessionStart.wav
    UserPromptSubmit.wav
    ... (18 total)
```

Run: `python synth/generate.py`
