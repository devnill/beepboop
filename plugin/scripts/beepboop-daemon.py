#!/usr/bin/env python3
"""
beepboop-daemon.py — Audio mixing daemon for macOS.

Listens on a Unix domain socket, accepts JSON sound-play requests, and
plays them through a single afplay process at a time.  Concurrent requests
are mixed (summed + clipped) before playback so that only one afplay
instance is ever active.

Protocol (per connection):
    Client writes one newline-terminated JSON line:
        {"path": "/abs/path/Sound.wav", "volume": 0.8}
    then closes the connection.  Server sends no response.

Lifecycle:
    Start:  double-fork daemonize, write PID file, bind socket.
    Idle:   block on accept(); mix + play incoming requests.
    Stop:   SIGTERM → cleanup → exit 0.
    Guard:  if PID file present and process alive → exit 0 immediately.
"""

import array
import json
import os
import signal
import socket
import struct  # noqa: F401 — listed in allowed stdlib set (WI-001 AC-9)
import subprocess
import sys
import tempfile
import threading
import time
import wave

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_UID = os.getuid()
_SOCK_PATH = f"/tmp/beepboop-{_UID}.sock"
_PID_PATH  = f"/tmp/beepboop-{_UID}.pid"

# ---------------------------------------------------------------------------
# WAV helpers
# ---------------------------------------------------------------------------

_SAMPLE_RATE   = 44100
_SAMPLE_WIDTH  = 2        # bytes (int16)
_CHANNELS      = 1
_WAV_HEADER_SZ = 44       # standard PCM WAV header size


def _read_wav_samples(path: str, volume: float) -> array.array:
    """
    Read a 16-bit PCM WAV file and return an array of int16 samples scaled
    by *volume*.  Returns an empty array on any error (silent fallback).
    """
    try:
        with wave.open(path, "rb") as wf:
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)
        samples = array.array("h")
        samples.frombytes(raw)
        if volume != 1.0:
            for i in range(len(samples)):
                samples[i] = int(samples[i] * volume)
        return samples
    except Exception:
        return array.array("h")


def _mix_samples(a: array.array, b: array.array) -> array.array:
    """
    Mix two int16 sample arrays by summing and clipping to [-32767, 32767].
    The result has the length of the longer array.
    """
    la, lb = len(a), len(b)
    length = max(la, lb)
    result = array.array("h", b"\x00\x00" * length)
    for i in range(length):
        sa = a[i] if i < la else 0
        sb = b[i] if i < lb else 0
        result[i] = max(-32767, min(32767, sa + sb))
    return result


def _write_wav(samples: array.array, path: str) -> None:
    """Write int16 PCM samples to a WAV file at *path*."""
    with wave.open(path, "wb") as wf:
        wf.setnchannels(_CHANNELS)
        wf.setsampwidth(_SAMPLE_WIDTH)
        wf.setframerate(_SAMPLE_RATE)
        wf.writeframes(samples.tobytes())


# ---------------------------------------------------------------------------
# Playback state — protected by _lock
# ---------------------------------------------------------------------------

_lock           = threading.Lock()
_shutdown       = threading.Event()

# Current afplay subprocess (or None if idle).
_afplay_proc: subprocess.Popen | None = None
# Samples not yet played: array("h") of remaining + queued samples.
_pending: array.array = array.array("h")
# Approximate sample position that afplay has consumed so far.
_play_start_time: float = 0.0       # wall time when current afplay started

# Temp dir for WAV chunks handed to afplay.
_tmp_dir: str = ""


def _kill_afplay() -> None:
    """Kill the running afplay process (caller holds _lock)."""
    global _afplay_proc
    if _afplay_proc is not None:
        try:
            _afplay_proc.terminate()
            _afplay_proc.wait(timeout=1)
        except Exception:
            try:
                _afplay_proc.kill()
            except Exception:
                pass
        _afplay_proc = None


def _start_afplay(samples: array.array) -> None:
    """
    Write *samples* to a temp WAV file and launch afplay.
    Caller must hold _lock.
    """
    global _afplay_proc, _pending, _play_start_time

    if not samples:
        _pending = array.array("h")
        _afplay_proc = None
        return

    try:
        fd, wav_path = tempfile.mkstemp(suffix=".wav", dir=_tmp_dir)
        os.close(fd)
        _write_wav(samples, wav_path)
        proc = subprocess.Popen(
            ["/usr/bin/afplay", wav_path],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        _afplay_proc = proc
        _pending = samples
        _play_start_time = time.monotonic()

        # Background thread to clean up temp file and reset state after playback.
        def _reap(p=proc, path=wav_path):
            p.wait()
            try:
                os.unlink(path)
            except Exception:
                pass
            with _lock:
                if _afplay_proc is p:
                    _afplay_proc = None
                    del _pending[:]

        threading.Thread(target=_reap, daemon=True).start()
    except Exception:
        _afplay_proc = None
        _pending = array.array("h")


def _enqueue_sound(path: str, volume: float) -> None:
    """
    Mix *path* (at *volume*) into the current playback stream.
    Uses "interrupt and remix": compute remaining samples of current playback,
    mix in new sound, restart afplay with the combined audio.
    """
    new_samples = _read_wav_samples(path, volume)
    if not new_samples:
        return

    with _lock:
        if _afplay_proc is not None and _afplay_proc.poll() is None:
            # Estimate how many samples have been consumed already.
            elapsed = max(0.0, time.monotonic() - _play_start_time)
            consumed = int(elapsed * _SAMPLE_RATE)
            remaining_start = consumed  # index into _pending
            if remaining_start < len(_pending):
                remaining = _pending[remaining_start:]
            else:
                remaining = array.array("h")
            mixed = _mix_samples(remaining, new_samples)
            _kill_afplay()
            _start_afplay(mixed)
        else:
            # Nothing playing — start fresh.
            _kill_afplay()
            _start_afplay(new_samples)


# ---------------------------------------------------------------------------
# Socket listener
# ---------------------------------------------------------------------------

def _handle_connection(conn: socket.socket) -> None:
    """Read one JSON request from *conn* and enqueue the sound."""
    try:
        data = b""
        while b"\n" not in data:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        line = data.split(b"\n")[0].strip()
        if not line:
            return
        req = json.loads(line)
        path   = req.get("path", "")
        volume = float(req.get("volume", 1.0))
        if path and os.path.isfile(path):
            _enqueue_sound(path, volume)
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _serve(sock: socket.socket) -> None:
    """Accept connections until _shutdown is set."""
    sock.settimeout(1.0)
    while not _shutdown.is_set():
        try:
            conn, _ = sock.accept()
        except socket.timeout:
            continue
        except OSError:
            # Socket closed — shutting down.
            break
        t = threading.Thread(target=_handle_connection, args=(conn,), daemon=True)
        t.start()


# ---------------------------------------------------------------------------
# Cleanup / signal handling
# ---------------------------------------------------------------------------

def _cleanup(sock: socket.socket | None = None) -> None:
    """Remove socket and PID files; kill any running afplay."""
    _shutdown.set()
    with _lock:
        _kill_afplay()
    if sock is not None:
        try:
            sock.close()
        except Exception:
            pass
    for path in (_SOCK_PATH, _PID_PATH):
        try:
            os.unlink(path)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Daemonize (double-fork)
# ---------------------------------------------------------------------------

def _daemonize() -> None:
    """
    Detach from the calling process using the classic Unix double-fork.
    After this call, the process is a session leader's child, has no
    controlling terminal, and is fully detached from the calling shell.
    """
    # First fork.
    pid = os.fork()
    if pid > 0:
        # Parent exits immediately so the shell prompt returns.
        os._exit(0)

    # Child 1: become session leader.
    os.setsid()

    # Detach from any mounted filesystem.
    os.chdir('/')

    # Second fork: ensure we can never re-acquire a controlling terminal.
    pid = os.fork()
    if pid > 0:
        os._exit(0)

    # Grandchild (daemon process) continues here.
    # Redirect standard file descriptors to /dev/null.
    devnull = os.open(os.devnull, os.O_RDWR)
    os.dup2(devnull, 0)
    os.dup2(devnull, 1)
    os.dup2(devnull, 2)
    if devnull > 2:
        os.close(devnull)

    os.umask(0o022)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _is_process_alive(pid: int) -> bool:
    """Return True if a process with *pid* exists and is reachable."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False
    except Exception:
        return False


def main() -> None:
    global _tmp_dir

    # --- Guard: already running? ---
    if os.path.exists(_PID_PATH):
        try:
            with open(_PID_PATH) as f:
                existing_pid = int(f.read().strip())
            if _is_process_alive(existing_pid):
                # Daemon already running — silent no-op.
                sys.exit(0)
        except Exception:
            pass
        # Stale PID file — remove it and continue.
        try:
            os.unlink(_PID_PATH)
        except Exception:
            pass

    # --- Daemonize ---
    _daemonize()

    # === Daemon process from here ===

    # Probe-connect: if another daemon won the race, exit quietly.
    _probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        _probe.connect(_SOCK_PATH)
        _probe.close()
        sys.exit(0)  # Live daemon exists — this instance exits.
    except (FileNotFoundError, ConnectionRefusedError):
        pass  # No live daemon — proceed with unlink + bind.
    except OSError:
        pass  # Socket path doesn't exist or other error — safe to proceed.
    finally:
        try:
            _probe.close()
        except Exception:
            pass

    # Set up temp directory for WAV chunks.
    _tmp_dir = tempfile.mkdtemp(prefix="beepboop-")

    # Write PID file.
    try:
        with open(_PID_PATH, "w") as f:
            f.write(str(os.getpid()) + "\n")
    except Exception:
        pass

    # Bind Unix domain socket.
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        # Remove stale socket file if present.
        try:
            os.unlink(_SOCK_PATH)
        except FileNotFoundError:
            pass
        sock.bind(_SOCK_PATH)
        os.chmod(_SOCK_PATH, 0o600)
        sock.listen(64)
    except Exception:
        # Cannot bind — exit silently.
        try:
            sock.close()
        except Exception:
            pass
        try:
            os.unlink(_PID_PATH)
        except Exception:
            pass
        sys.exit(0)

    # SIGTERM handler.
    def _on_sigterm(signum, frame):
        _cleanup(sock)
        # Clean up temp directory.
        try:
            import shutil
            shutil.rmtree(_tmp_dir, ignore_errors=True)
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, _on_sigterm)
    signal.signal(signal.SIGINT,  _on_sigterm)

    # Serve.
    try:
        _serve(sock)
    finally:
        _cleanup(sock)
        try:
            import shutil
            shutil.rmtree(_tmp_dir, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
