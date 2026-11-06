"""Mood-matched background-music bed for each video (spec 4.3).

Two sources, in priority order:

  1. Drop-in tracks — any audio file placed in the mood's subfolder under
     ``agent-backend/assets/music/<mood>/`` (``.mp3`` / ``.wav`` / ``.ogg`` /
     ``.flac`` / ``.m4a`` / ``.aac``). One is chosen per render, deliberately not
     repeating the previous video's pick, then looped / trimmed to length. The
     mood comes from ``payload.suggested_bgm_mood``; if that folder is empty we
     fall back to the flat ``assets/music/`` folder, then to the generator.

  2. Procedural ambient (default, zero assets) — a warm, slowly-evolving pad is
     synthesized from scratch with a fresh random key, chord progression and
     tempo on every run, with per-mood tonal shaping (darker/tenser moods pick
     lower, more minor voicings). Nothing has to be downloaded or licensed.

The returned bed is already looped to length, leveled well under the narration,
and faded in/out. Everything degrades to silence on any error: background music
must never be the reason a render fails.
"""

from __future__ import annotations

import os
import random
from pathlib import Path
from typing import List, Optional

from pydub import AudioSegment

try:
    from . import config
except ImportError:  # pragma: no cover
    import config  # type: ignore

_AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"}
_STATE_FILE = config.OUTPUT_DIR / ".last_music"


# ---------------------------------------------------------------------------
# "Don't repeat the last one" state
# ---------------------------------------------------------------------------
def _read_last() -> str:
    try:
        return _STATE_FILE.read_text(encoding="utf-8").strip()
    except Exception:  # noqa: BLE001
        return ""


def _write_last(tag: str) -> None:
    try:
        _STATE_FILE.write_text(tag, encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def _loop_to(seg: AudioSegment, duration_ms: int) -> Optional[AudioSegment]:
    if seg is None or len(seg) == 0 or duration_ms <= 0:
        return None
    out = seg
    while len(out) < duration_ms:
        out = out + seg
    return out[:duration_ms]


# ---------------------------------------------------------------------------
# Source 1: mood-tagged drop-in folders
# ---------------------------------------------------------------------------
def _candidate_folders(mood: str) -> List[Path]:
    sub = config.MOOD_FOLDERS.get(mood, "")
    folders: List[Path] = []
    if sub:
        folders.append(config.MUSIC_DIR / sub)
    folders.append(config.MUSIC_DIR)  # flat fallback
    return folders


def _pick_from_folder(mood: str, duration_ms: int) -> Optional[AudioSegment]:
    tracks: List[Path] = []
    for folder in _candidate_folders(mood):
        if folder.exists():
            tracks = sorted(
                p for p in folder.iterdir()
                if p.suffix.lower() in _AUDIO_EXTS and p.is_file()
            )
            if tracks:
                break
    if not tracks:
        return None

    last = _read_last()
    pool = [t for t in tracks if t.name != last] or tracks
    pick = random.choice(pool)
    _write_last(pick.name)

    try:
        seg = AudioSegment.from_file(pick)
    except Exception as exc:  # noqa: BLE001
        print(f"[music] could not decode '{pick.name}' ({exc}); using generator.")
        return None

    seg = seg.set_channels(1).set_frame_rate(config.AUDIO_SAMPLE_RATE)
    print(f"[music] background track ({mood}): {pick.name}")
    return _loop_to(seg, duration_ms)


# ---------------------------------------------------------------------------
# Source 2: procedural ambient pad (the zero-asset default)
# ---------------------------------------------------------------------------
_CHORDS = {
    "maj7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10],
    "add9": [0, 4, 7, 14],
    "min9": [0, 3, 7, 14],
    "sus2": [0, 2, 7, 12],
    "sus4": [0, 5, 7, 12],
    "maj6": [0, 4, 7, 9],
    "min_add9": [0, 3, 7, 14],
}
_PROG_WARM = [
    ["maj7", "min9", "add9", "sus2"],
    ["add9", "sus2", "maj7", "min7"],
    ["maj7", "maj6", "min7", "add9"],
]
_PROG_DARK = [
    ["min9", "min7", "sus2", "min9"],
    ["min7", "min9", "add9", "min7"],
    ["sus2", "min7", "min9", "min7"],
]
_PROG_SUS = [
    ["sus2", "sus4", "sus2", "min7"],
    ["sus4", "add9", "sus2", "sus4"],
]
_ROOT_WALKS = [
    [0, -3, -5, 2],
    [0, 2, -3, -5],
    [0, -5, -3, 0],
    [0, 3, 5, 2],
]

# Per-mood sonic identity — this is what makes each video (and each sibling
# project) sound DIFFERENT instead of one generic drone. Each profile picks its
# own register, chord colour, tempo, filter brightness and a rhythmic "motif".
#   motif: "swell"  slow noise/pad swells, no notes   (ambient, spacious)
#          "pulse"  soft low heartbeat on the root     (investigative tension)
#          "two"    two high notes trading slowly      (minimal suspense)
#          "arp"    bright pentatonic arpeggio pattern (curious / tech)
#          "pluck"  sparse warm decaying plucks        (thoughtful / acoustic)
_PROFILES = {
    "dark_ambient_synth": dict(
        tonics=[73.42, 65.41, 61.74, 55.00], progs=_PROG_DARK, bar=(6.5, 8.5),
        lp=0.07, trem=(0.03, 0.07), sub=0.55, motif="swell", bright=0.10,
    ),
    "cinematic_investigative": dict(
        tonics=[110.00, 98.00, 103.83, 87.31], progs=_PROG_DARK, bar=(4.5, 5.5),
        lp=0.10, trem=(0.05, 0.10), sub=0.40, motif="pulse", bright=0.22,
    ),
    "minimal_tension": dict(
        tonics=[130.81, 123.47, 110.00, 116.54], progs=_PROG_SUS, bar=(6.0, 7.5),
        lp=0.11, trem=(0.04, 0.08), sub=0.30, motif="two", bright=0.28,
    ),
    "upbeat_curious_tech": dict(
        tonics=[196.00, 220.00, 174.61, 164.81], progs=_PROG_WARM, bar=(3.2, 4.2),
        lp=0.20, trem=(0.08, 0.15), sub=0.25, motif="arp", bright=0.85,
    ),
    "acoustic_thoughtful": dict(
        tonics=[164.81, 146.83, 196.00, 130.81], progs=_PROG_WARM, bar=(4.0, 5.0),
        lp=0.16, trem=(0.05, 0.10), sub=0.30, motif="pluck", bright=0.60,
    ),
}
_DEFAULT_PROFILE = _PROFILES["minimal_tension"]


def _procedural_bed(mood: str, duration_ms: int, seed: Optional[int] = None) -> Optional[AudioSegment]:
    try:
        import numpy as np
    except Exception as exc:  # noqa: BLE001
        print(f"[music] numpy unavailable ({exc}); no generated music.")
        return None

    sr = config.AUDIO_SAMPLE_RATE
    total = int(sr * duration_ms / 1000)
    if total <= 0:
        return None

    if seed is None:
        seed = int.from_bytes(os.urandom(8), "big")
    rng = random.Random(seed)
    prof = _PROFILES.get(mood, _DEFAULT_PROFILE)

    tonic = rng.choice(prof["tonics"])
    quality = rng.choice(prof["progs"])
    walk = rng.choice(_ROOT_WALKS)
    bar_sec = rng.uniform(*prof["bar"])
    trem_hz = rng.uniform(*prof["trem"])
    motif = prof["motif"]
    bright = prof["bright"]

    bar_n = int(sr * bar_sec)
    fade = np.hanning(bar_n * 2)
    env = np.ones(bar_n)
    half = bar_n // 2
    env[:half] = fade[:half]
    env[-half:] = fade[-half:]

    def semis(freq: float, s: float) -> float:
        return freq * (2.0 ** (s / 12.0))

    def voice(freq: float, n: int) -> "np.ndarray":
        t = np.arange(n) / sr
        base = np.sin(2 * np.pi * freq * t)
        octv = (0.30 + 0.25 * bright) * np.sin(2 * np.pi * freq * 2 * t)
        det = 0.5 * (np.sin(2 * np.pi * freq * 1.003 * t) + np.sin(2 * np.pi * freq * 0.997 * t))
        fifth = 0.2 * np.sin(2 * np.pi * semis(freq, 7) * t)
        return base + octv + det + fifth

    def pluck(freq: float, n: int, decay: float, amp: float) -> "np.ndarray":
        m = min(n, int(sr * 1.6))
        tb = np.arange(m) / sr
        tone = np.sin(2 * np.pi * freq * tb) + 0.5 * np.sin(2 * np.pi * freq * 2 * tb)
        out = np.zeros(n, dtype=np.float32)
        out[:m] = (amp * tone * np.exp(-tb * decay)).astype(np.float32)
        return out

    out = np.zeros(total + bar_n, dtype=np.float32)
    pent = [0, 2, 4, 7, 9, 12]

    cursor = 0
    bar_idx = 0
    while cursor < total:
        q = quality[bar_idx % len(quality)]
        root = semis(tonic, walk[bar_idx % len(walk)])
        chord = _CHORDS[q]

        bar = np.zeros(bar_n, dtype=np.float32)
        for st in chord:
            bar += voice(semis(root, st), bar_n)
        bar += prof["sub"] * voice(root / 2.0, bar_n)
        bar *= env

        # --- the per-mood rhythmic motif ----------------------------------
        if motif == "pulse":
            step = int(sr * bar_sec / 4)  # four soft pulses per bar
            for k in range(4):
                at = k * step
                p = pluck(root, bar_n - at, decay=6.0, amp=0.5)
                bar[at:at + len(p)] += p[: bar_n - at]
        elif motif == "two":
            for k, deg in ((0, 7), (1, 12)):  # two high notes trading, half-bar apart
                at = int(k * bar_n / 2)
                note = semis(root * 2, deg)
                p = pluck(note, bar_n - at, decay=1.6, amp=0.18)
                bar[at:at + len(p)] += p[: bar_n - at]
        elif motif == "arp":
            steps = 8
            step = bar_n // steps
            for k in range(steps):
                at = k * step
                note = semis(root * 2, pent[(bar_idx + k) % len(pent)])
                p = pluck(note, bar_n - at, decay=5.5, amp=0.22)
                bar[at:at + len(p)] += p[: bar_n - at]
        elif motif == "pluck":
            for _ in range(rng.randint(2, 3)):
                at = rng.randint(0, max(1, bar_n - sr))
                note = semis(root * 2, rng.choice(pent))
                p = pluck(note, bar_n - at, decay=3.2, amp=0.20)
                bar[at:at + len(p)] += p[: bar_n - at]
        elif motif == "swell" and rng.random() < 0.7:
            # a slow filtered-noise swell for air/space
            at = rng.randint(0, max(1, bar_n // 2))
            m = min(bar_n - at, int(sr * bar_sec * 0.6))
            noise = rng.random()  # seed-stable amplitude
            wash = (0.05 * noise) * np.random.default_rng(seed + bar_idx).standard_normal(m).astype(np.float32)
            win = np.hanning(m)
            bar[at:at + m] += wash * win

        out[cursor:cursor + bar_n] += bar
        cursor += bar_n
        bar_idx += 1

    sig = out[:total]

    t = np.arange(total) / sr
    sig = sig * (0.88 + 0.12 * np.sin(2 * np.pi * trem_hz * t))

    # One-pole low-pass; brighter moods keep more top end.
    a = prof["lp"]
    lp = np.empty_like(sig)
    acc = 0.0
    for i in range(total):
        acc += a * (sig[i] - acc)
        lp[i] = acc
    sig = (1.0 - 0.25 * bright) * lp + (0.22 + 0.25 * bright) * sig

    for delay_ms, gain in ((180, 0.22), (320, 0.14)):
        d = int(sr * delay_ms / 1000)
        if d < total:
            sig[d:] += gain * sig[:-d]

    peak = float(np.max(np.abs(sig))) or 1.0
    sig = (sig / peak) * 0.72
    pcm = (sig * 32767.0).astype("<i2")

    bed = AudioSegment(pcm.tobytes(), frame_rate=sr, sample_width=2, channels=1)
    _write_last(f"gen:{mood}:{seed}")
    print(
        f"[music] generated '{mood}' bed (motif={motif}, tonic {tonic:.1f}Hz, "
        f"{'-'.join(quality)}, {bar_sec:.1f}s/bar)."
    )
    return bed


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------
def build_music_bed(duration_ms: int, mood: str = "minimal_tension") -> Optional[AudioSegment]:
    """Return a leveled, faded, mood-matched background bed, or None."""
    if not config.BACKGROUND_MUSIC_ENABLED or duration_ms <= 0:
        return None
    try:
        bed = _pick_from_folder(mood, duration_ms)
        if bed is None:
            bed = _procedural_bed(mood, duration_ms)
        if bed is None:
            return None
        bed = _loop_to(bed, duration_ms) or bed

        if bed.dBFS != float("-inf"):
            bed = bed.apply_gain(config.MUSIC_LEVEL_DBFS - bed.dBFS)
        fade = min(config.MUSIC_FADE_MS, len(bed) // 2)
        if fade > 0:
            bed = bed.fade_in(fade).fade_out(fade)
        return bed
    except Exception as exc:  # noqa: BLE001
        print(f"[music] bed build failed ({exc}); rendering without music.")
        return None
