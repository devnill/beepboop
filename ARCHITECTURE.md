# beepboop — Audio System Architecture

## Overview

beepboop plays a distinct synthesized sound for each of Claude Code's 25 hook events. On macOS, audio is routed through a persistent mixing daemon that prevents corruption when multiple hooks fire in rapid succession. On Linux and WSL, sounds are played directly by the shell script using available system players.

---

## Component Map

```
Claude Code hook fires
        │
        ▼
  hooks/hooks.json          ← Registers which script to call per event
        │
        ▼
  scripts/play-sound.sh     ← Entry point for every hook; fire-and-forget
        │
        ├─── [Linux/WSL] ──► aplay / paplay / pw-play / powershell.exe (direct)
        │
        └─── [macOS] ──────► background subshell ( ... ) &
                                      │
                                      ▼
                              beepboop-daemon.py  ← Persistent daemon (one per user)
                                      │
                                      ▼
                               /usr/bin/afplay    ← Single afplay process at a time
```

---

## Request Flow (macOS)

### Normal path — daemon already running

```
Hook fires (e.g. PreToolUse)
  │
  └─► play-sound.sh PreToolUse
        ├─ reads settings.json → sound path, volume
        ├─ checks daemon socket exists (/tmp/beepboop-<uid>.sock)
        ├─ spawns background subshell: ( IPC send ) 2>/dev/null &
        └─ returns immediately  ← hook timeout never at risk

Background subshell:
  └─► python3 IPC client
        ├─ socket.connect(sock_path)
        ├─ sends JSON: {"path": "/path/Sound.wav", "volume": 0.2}
        └─ closes connection
```

### Cold start — daemon not yet running

```
Hook fires (e.g. SessionStart — first event of the session)
  │
  └─► play-sound.sh SessionStart
        └─ spawns background subshell: ( ... ) 2>/dev/null &
              └─ socket file absent → launch daemon:
                    python3 beepboop-daemon.py &
                    poll for /tmp/beepboop-<uid>.sock (10 × 50ms = 0.5s max)
                    if socket appears → IPC send
                    if socket never appears → exit 0 silently

play-sound.sh returns immediately (daemon start is in background)
∴ first sound (SessionStart) may not play on a cold system
  — accepted trade-off for GP-05 compliance
```

---

## Audio Mixing Daemon (`beepboop-daemon.py`)

### Purpose

macOS afplay is a single-file player. Spawning multiple concurrent `afplay` processes causes the audio subsystem to glitch and corrupt output until the driver is reloaded. The daemon serializes all sound requests into a single `afplay` instance using **interrupt-and-remix** mixing.

### Lifecycle

```
 ┌─────────────────────────────────────────────────────────┐
 │  main()                                                  │
 │                                                          │
 │  1. PID guard                                            │
 │     ├─ PID file exists + process alive? → exit 0        │
 │     └─ stale PID file? → remove and continue            │
 │                                                          │
 │  2. _daemonize()  (double-fork)                          │
 │     ├─ fork #1: parent exits (os._exit)                 │
 │     ├─ child: setsid(), chdir('/')                       │
 │     ├─ fork #2: parent exits (os._exit)                 │
 │     └─ grandchild: redirect stdio → /dev/null           │
 │                                                          │
 │  3. Probe-connect (TOCTOU guard)                         │
 │     ├─ connect to sock_path                              │
 │     ├─ success → another daemon won the race → exit 0   │
 │     └─ failure → proceed                                 │
 │                                                          │
 │  4. Write PID file                                       │
 │  5. Bind Unix domain socket, chmod 600                   │
 │  6. Register SIGTERM / SIGINT handler                    │
 │  7. _serve() — accept loop (1s timeout, checks shutdown) │
 │                                                          │
 │  On SIGTERM:                                             │
 │     _cleanup(): kill afplay, close socket, unlink        │
 │                 socket file + PID file                   │
 └─────────────────────────────────────────────────────────┘
```

### Double-Fork Daemonization

Standard Unix daemonization prevents the daemon from re-acquiring a controlling terminal and ensures it is reparented to init/launchd.

```
play-sound.sh (shell)
  └─► python3 beepboop-daemon.py
        ├─ fork #1
        │    ├─ parent → os._exit(0)  ← shell's child; exits so shell doesn't wait
        │    └─ child (session leader)
        │         setsid()            ← new session, no controlling terminal
        │         chdir('/')          ← detach from any mounted filesystem
        │         fork #2
        │           ├─ parent → os._exit(0)  ← session leader exits
        │           └─ grandchild            ← the actual daemon
        │                stdio → /dev/null
        │                continues to serve...
```

`os._exit()` is used (not `sys.exit()`) in the fork parents to avoid flushing Python atexit handlers or stdio buffers in the intermediate processes.

### TOCTOU Race Prevention

Without the probe-connect guard, two concurrent hook invocations that both pass the PID guard before either writes the PID file would each daemonize and race to bind the socket. The second daemon's `os.unlink(sock_path)` would delete the first's socket, leaving the first daemon bound to nothing and the second winning.

The probe-connect block resolves this by running inside the grandchild *before* unlinking the socket:

```python
# After _daemonize(), before os.unlink(_SOCK_PATH):
_probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
try:
    _probe.connect(_SOCK_PATH)
    _probe.close()
    sys.exit(0)          # Another daemon won — this one exits quietly.
except (FileNotFoundError, ConnectionRefusedError):
    pass                 # No live daemon — safe to proceed.
finally:
    _probe.close()       # Always close the probe socket.
```

This ensures only one daemon ever binds the socket, regardless of how many instances are started concurrently.

---

## Interrupt-and-Remix Mixing

When a new sound request arrives while `afplay` is already playing:

```
Timeline:
  t=0    Sound A starts playing (0.8s total)
  t=0.3  Sound B arrives

  Without mixing:  B waits → plays after A ends (0.8s + 0.4s)
  With remix:      at t=0.3:
                     estimate consumed samples = 0.3s × 44100 = 13,230
                     remaining_A = A[13230:]     (0.5s of A left)
                     mixed = remaining_A + B      (element-wise sum, clipped to int16)
                     kill current afplay
                     write mixed[] to temp WAV
                     start new afplay(mixed.wav)
```

Key properties:
- **Single afplay**: Only one `afplay` process is ever active. No audio driver saturation.
- **No silence gap**: Remix starts immediately from the estimated playback position.
- **Clipping, not wrapping**: `max(-32767, min(32767, sa + sb))` prevents int16 overflow artifacts.
- **Sample rate**: 44,100 Hz, 16-bit PCM mono, matching the synthesized WAV output from `synth generate`.

Elapsed-samples estimation uses wall time (`time.monotonic()`), which is approximate. Minor drift is acceptable — the perceptual effect is correct overlap with no glitching.

---

## IPC Protocol

Communication between `play-sound.sh` and the daemon uses a Unix domain socket with a simple line-delimited JSON protocol:

**Socket path**: `/tmp/beepboop-<uid>.sock` (mode 0600 — owner only)

**Request** (client → server, newline-terminated):
```json
{"path": "/abs/path/to/Sound.wav", "volume": 0.2}
```

**Response**: None. The client closes the connection immediately after sending.

**Error handling**: The client wraps the entire connect-send-close sequence in `try/except Exception: pass`. Any failure (socket not ready, daemon restarting, permission error) is silently discarded — consistent with GP-03 (silent failure) and P-2 (fire-and-forget audio).

---

## Daemon Management

### Files

| File | Purpose |
|------|---------|
| `/tmp/beepboop-<uid>.sock` | Unix domain socket for IPC |
| `/tmp/beepboop-<uid>.pid` | Daemon PID (written after daemonize) |
| `/tmp/beepboop-*/` | Temp directory for mixed WAV chunks (cleaned on exit) |

Both files use the real UID (`os.getuid()`) to namespace per-user — safe on multi-user systems.

### Lifecycle triggers

| Event | Action |
|-------|--------|
| First hook fires, socket absent | `play-sound.sh` background subshell starts daemon |
| `SessionEnd` hook | `hooks.json` chains `stop-daemon.sh` unconditionally after sound |
| SIGTERM | Daemon kills `afplay`, removes socket + PID file, cleans temp dir |

### stop-daemon.sh

Sends SIGTERM then polls for PID file disappearance (daemon removes it in `_cleanup()`):

```sh
kill -TERM "$pid" 2>/dev/null || true
i=0
while [ $i -lt 20 ] && [ -f "$pid_file" ]; do
    sleep 0.05; i=$((i+1))       # max 1 second wait
done
rm -f "$pid_file"                 # fallback only — daemon normally removes it
```

The `rm -f` at the end is a safety net for the case where the daemon exits without cleanup (e.g. SIGKILL). It does not race with the daemon's own cleanup because by the time the poll exits, the daemon has either removed the file or is dead.

---

## Cross-Platform Paths

### macOS

All sounds routed through `beepboop-daemon.py` → `afplay`. The daemon is the only active audio process.

### Linux (native)

```
play-sound.sh → aplay / paplay / pw-play (whichever is found first)
```

Player is detected once and cached in `settings.json`. Each sound spawns an independent player process. No mixing daemon — Linux audio systems (PulseAudio, PipeWire, ALSA) handle concurrent playback in the server.

### WSL

Tries Linux players first (`aplay`, `paplay`, `pw-play`), then falls back to `powershell.exe` with `Media.SoundPlayer.PlaySync()`.

### Player detection and caching

`play-sound.sh` calls `detect_player()` on first run, writes the result to `settings.json["player"]`, and reads it back on subsequent runs — one `python3` call instead of repeated `command -v` probes.

---

## Sound Synthesis

Sounds are defined in `sounds.py` as NumPy arrays using primitives from the `synth` submodule:

```
synth.toml         ← maps function names to output filenames
sounds.py          ← 25 synthesis functions + SOUNDS dict
synth/             ← submodule: sine, square, sweep, fm, adsr, seq, silence
generate.sh        ← runs `synth generate` to produce plugin/sounds/*.wav
```

`generate.sh` creates a `.venv` if absent, installs `synth` in editable mode, and runs generation. Output WAVs land in `plugin/sounds/` and are committed to the repo — users do not need Python or NumPy to run the plugin.

`play-sound.sh` resolves sounds in priority order:
1. `plugin/sounds/<HookName>.wav` (bundled WAV — always preferred)
2. `settings.json["hook_sounds"]["<HookName>"]` (system sound fallback path)

---

## Hook Coverage

All 25 Claude Code hooks are registered:

| Hook | Character |
|------|-----------|
| SessionStart | Warm 2-note rising chirp |
| SessionEnd | Descending mirror of SessionStart |
| UserPromptSubmit | Short clean acknowledgment boop |
| PreToolUse | Quick tick — minimal |
| PostToolUse | Soft confirmation bip |
| PostToolUseFailure | Detuned square buzz pulsed at 8Hz |
| PermissionRequest | FM alert with rising 2-note inflection |
| Notification | Bright bell-like ping |
| Stop | Descending 2-note conclusion |
| StopFailure | Glitchy descending minor sequence |
| TaskCompleted | C5-E5-G5 major arpeggio |
| TaskCreated | Short ascending 2-note chirp |
| SubagentStart | Fast rising sweep — spawning |
| SubagentStop | Exponential falling sweep — winding down |
| TeammateIdle | Quiet idle blip |
| InstructionsLoaded | 4-tone ascending scan sequence |
| ConfigChange | Descending 2-tone mechanical click |
| WorktreeCreate | 3 ascending tones + bright ping |
| WorktreeRemove | Warbly falling sweep |
| PreCompact | Rapid descending R2D2 warble |
| PostCompact | Rising warble + confirming ping |
| CwdChanged | Short directional 2-tone flick |
| FileChanged | Short soft sine ping |
| Elicitation | Rising inquisitive FM 2-note |
| ElicitationResult | Short affirmative 2-tone resolution |
