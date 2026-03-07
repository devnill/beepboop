"""
Beepboop sound definitions.

Imports synthesis primitives from the synth submodule.
Run generate.sh (or `synth generate`) to produce WAV files in plugin/sounds/.
"""

import numpy as np
from synth import sine, square, sweep, fm, adsr, seq, silence, SAMPLE_RATE
from synth.primitives import _t


def session_start() -> np.ndarray:
    """Warm startup chirp: low boop then rising sweep."""
    boop = adsr(sine(300, 0.12), 0.005, 0.08, 0.0, 0.03)
    rise = adsr(sweep(420, 780, 0.20), 0.005, 0.06, 0.4, 0.08)
    return seq(boop, silence(0.04), rise)


def user_prompt_submit() -> np.ndarray:
    """Short, clean acknowledgment boop."""
    return adsr(sine(520, 0.15), 0.005, 0.10, 0.0, 0.03)


def pre_tool_use() -> np.ndarray:
    """Quick click/tick — snappy and minimal."""
    return adsr(sine(900, 0.06), 0.002, 0.04, 0.0, 0.015)


def permission_request() -> np.ndarray:
    """FM alert with rising 2-note inflection (question feel)."""
    note1 = adsr(fm(480, 480, 3, 0.18), 0.005, 0.04, 0.6, 0.06)
    note2 = adsr(fm(576, 576, 3, 0.20), 0.005, 0.04, 0.6, 0.08)
    return seq(note1, silence(0.04), note2)


def post_tool_use() -> np.ndarray:
    """Soft confirmation bip — gentle, higher than submit."""
    return adsr(sine(660, 0.10), 0.003, 0.07, 0.0, 0.025)


def post_tool_use_failure() -> np.ndarray:
    """Detuned square buzz pulsed at 8 Hz — harsh but not overwhelming."""
    duration = 0.45
    t = _t(duration)
    wave = np.sign(np.sin(2 * np.pi * 160 * t)) + 0.5 * np.sign(np.sin(2 * np.pi * 170 * t))
    wave /= 1.5
    pulse = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 8 * t))
    env = adsr(np.ones(len(t)), 0.002, 0.02, 0.7, 0.05)
    return wave * pulse * env


def notification() -> np.ndarray:
    """Bright bell-like ping with long ring decay."""
    fundamental = sine(880, 0.35)
    harmonic = 0.3 * sine(1760, 0.35)
    return adsr(fundamental + harmonic, 0.003, 0.05, 0.3, 0.18)


def subagent_start() -> np.ndarray:
    """Fast rising chirp — a subagent spawning."""
    return adsr(sweep(400, 1000, 0.20), 0.005, 0.03, 0.0, 0.04)


def subagent_stop() -> np.ndarray:
    """Exponential falling chirp — a subagent winding down."""
    return adsr(sweep(1000, 350, 0.22, log=True), 0.005, 0.03, 0.5, 0.06)


def stop() -> np.ndarray:
    """Descending 2-note conclusion — satisfied, done."""
    note1 = adsr(sine(440, 0.16), 0.008, 0.06, 0.4, 0.06)
    note2 = adsr(sine(330, 0.22), 0.005, 0.08, 0.3, 0.10)
    return seq(note1, silence(0.03), note2)


def task_completed() -> np.ndarray:
    """Happy C5-E5-G5 major arpeggio — cheerful multi-boop."""
    freqs = [523.25, 659.25, 783.99]
    parts = []
    for i, freq in enumerate(freqs):
        parts.append(adsr(sine(freq, 0.12), 0.005, 0.04, 0.5, 0.04))
        if i < len(freqs) - 1:
            parts.append(silence(0.03))
    return seq(*parts)


def teammate_idle() -> np.ndarray:
    """Quiet idle blip — unobtrusive since it fires frequently."""
    return adsr(sine(420, 0.08), 0.003, 0.05, 0.0, 0.025) * 0.57  # ~40% final amplitude


def instructions_loaded() -> np.ndarray:
    """R2D2 data-reading: 4 rapid ascending tones like scanning."""
    freqs = [400, 520, 640, 800]
    parts = []
    for i, freq in enumerate(freqs):
        parts.append(adsr(sine(freq, 0.07), 0.003, 0.05, 0.0, 0.015))
        if i < len(freqs) - 1:
            parts.append(silence(0.015))
    return seq(*parts)


def config_change() -> np.ndarray:
    """Two-tone descending switch — crisp, mechanical settings click."""
    note1 = adsr(sine(440, 0.10), 0.003, 0.07, 0.0, 0.02)
    note2 = adsr(sine(370, 0.12), 0.003, 0.09, 0.0, 0.025)
    return seq(note1, silence(0.02), note2)


def worktree_create() -> np.ndarray:
    """Three ascending tones + bright ping — summoning a branch."""
    parts = []
    for freq in [330, 440, 550]:
        parts.append(adsr(sine(freq, 0.08), 0.003, 0.055, 0.0, 0.02))
        parts.append(silence(0.015))
    ping = adsr(sine(880, 0.15) + 0.2 * sine(1760, 0.15), 0.003, 0.04, 0.3, 0.08)
    parts.append(ping)
    return seq(*parts)


def worktree_remove() -> np.ndarray:
    """Warbly falling sweep — a branch dissolving."""
    duration = 0.30
    t = _t(duration)
    freqs = np.logspace(np.log10(700), np.log10(200), len(t))
    wobble = 12 * np.sin(2 * np.pi * 18 * t) * (1 - t / duration)
    phase = 2 * np.pi * np.cumsum(freqs + wobble) / SAMPLE_RATE
    return adsr(np.sin(phase), 0.005, 0.05, 0.5, 0.12)


def pre_compact() -> np.ndarray:
    """Rapid descending warble — R2D2 compressing memory."""
    duration = 0.35
    t = _t(duration)
    freqs = np.linspace(800, 300, len(t))
    wobble = 60 * np.sin(2 * np.pi * 25 * t)
    phase = 2 * np.pi * np.cumsum(freqs + wobble) / SAMPLE_RATE
    return adsr(np.sin(phase), 0.005, 0.06, 0.6, 0.10)


def session_end() -> np.ndarray:
    """Mirror of session_start — descending, softer goodbye."""
    fall = adsr(sweep(780, 420, 0.20, log=True), 0.005, 0.06, 0.4, 0.08)
    boop = adsr(sine(280, 0.14), 0.005, 0.10, 0.0, 0.05)
    return seq(fall, silence(0.04), boop) * 0.85


SOUNDS = {
    "SessionStart":         session_start,
    "UserPromptSubmit":     user_prompt_submit,
    "PreToolUse":           pre_tool_use,
    "PermissionRequest":    permission_request,
    "PostToolUse":          post_tool_use,
    "PostToolUseFailure":   post_tool_use_failure,
    "Notification":         notification,
    "SubagentStart":        subagent_start,
    "SubagentStop":         subagent_stop,
    "Stop":                 stop,
    "TaskCompleted":        task_completed,
    "TeammateIdle":         teammate_idle,
    "InstructionsLoaded":   instructions_loaded,
    "ConfigChange":         config_change,
    "WorktreeCreate":       worktree_create,
    "WorktreeRemove":       worktree_remove,
    "PreCompact":           pre_compact,
    "SessionEnd":           session_end,
}
