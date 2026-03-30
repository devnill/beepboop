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


def stop_failure() -> np.ndarray:
    """Glitchy descending minor sequence — alarmed, tense, clearly worse than stop."""
    duration = 0.28
    t = _t(duration)
    # Detuned buzz layer for glitch texture
    buzz = np.sign(np.sin(2 * np.pi * 180 * t)) + 0.4 * np.sign(np.sin(2 * np.pi * 187 * t))
    buzz /= 1.4
    # Rapid stutter pulse at 14 Hz
    pulse = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 14 * t))
    env = adsr(np.ones(len(t)), 0.002, 0.03, 0.65, 0.08)
    glitch = buzz * pulse * env
    # Minor descending notes after the glitch burst
    note1 = adsr(fm(370, 370, 4, 0.14), 0.005, 0.04, 0.5, 0.05)
    note2 = adsr(fm(220, 220, 4, 0.18), 0.005, 0.06, 0.4, 0.08)
    return seq(glitch, silence(0.02), note1, silence(0.025), note2)


def task_created() -> np.ndarray:
    """Short ascending two-note chirp — lighter and brighter than task_completed."""
    note1 = adsr(sine(480, 0.09), 0.004, 0.04, 0.3, 0.03)
    note2 = adsr(sine(720, 0.11), 0.004, 0.05, 0.2, 0.04)
    return seq(note1, silence(0.025), note2)


def post_compact() -> np.ndarray:
    """Resolution tone — bookend to pre_compact, rising settle after compression."""
    duration = 0.30
    t = _t(duration)
    freqs = np.linspace(300, 600, len(t))
    # Gentle wobble that fades out (settling, not frantic)
    wobble = 20 * np.sin(2 * np.pi * 10 * t) * np.exp(-t / 0.15)
    phase = 2 * np.pi * np.cumsum(freqs + wobble) / SAMPLE_RATE
    warble = adsr(np.sin(phase), 0.005, 0.06, 0.5, 0.12)
    # Bright confirming ping at the end
    ping = adsr(sine(660, 0.12) + 0.2 * sine(1320, 0.12), 0.003, 0.04, 0.3, 0.06)
    return seq(warble, silence(0.02), ping)


def cwd_changed() -> np.ndarray:
    """Very short directional blip — a quick step to a new place (≤150ms)."""
    # Two-tone upward flick: ~110ms total
    lo = adsr(sine(500, 0.05), 0.002, 0.03, 0.0, 0.015)
    hi = adsr(sine(750, 0.05), 0.002, 0.025, 0.0, 0.02)
    return seq(lo, silence(0.01), hi) * 0.65


def file_changed() -> np.ndarray:
    """Very short soft ping — watched file touched (≤150ms)."""
    # Single soft sine ping with quick decay: ~90ms
    return adsr(sine(1100, 0.09) + 0.15 * sine(2200, 0.09), 0.002, 0.025, 0.0, 0.06) * 0.55


def elicitation() -> np.ndarray:
    """Rising inquisitive FM tone — MCP awaiting input, held attentively."""
    note1 = adsr(fm(360, 360, 2.5, 0.16), 0.005, 0.05, 0.55, 0.06)
    # Rise to a higher, slightly brighter FM note held a moment
    note2 = adsr(fm(540, 540, 2.5, 0.24), 0.005, 0.06, 0.60, 0.10)
    return seq(note1, silence(0.03), note2)


def elicitation_result() -> np.ndarray:
    """Short affirmative two-tone resolution — answer received, carry on."""
    note1 = adsr(fm(540, 540, 2, 0.11), 0.004, 0.04, 0.4, 0.04)
    note2 = adsr(sine(660, 0.13), 0.004, 0.05, 0.3, 0.05)
    return seq(note1, silence(0.02), note2)


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
    "StopFailure":          stop_failure,
    "TaskCreated":          task_created,
    "PostCompact":          post_compact,
    "CwdChanged":           cwd_changed,
    "FileChanged":          file_changed,
    "Elicitation":          elicitation,
    "ElicitationResult":    elicitation_result,
}
