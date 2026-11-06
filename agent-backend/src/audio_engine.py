"""Natural voiceover synthesis + EXACT word-level timing (spec 4.1/4.2).

The old engine chopped every sentence into comma-separated fragments and
synthesized each one as its own TTS call — which is exactly why it sounded flat
and robotic (the voice restarted with dead intonation on every fragment) and why
the captions drifted (word timings were *guessed* by spreading words evenly
across a scene, pauses included).

This version fixes both at the source:

  * **Whole-scene synthesis** — each scene's narration is spoken in ONE call so
    the engine's natural sentence melody, emphasis and breathing are preserved.
  * **Exact timings, no ML model** — edge-tts emits a `WordBoundary` event for
    every word as it synthesizes. We capture those, so `payload.words` carries
    frame-accurate start/end times straight from the TTS engine. This works on
    any Python (no onnxruntime), so karaoke subtitles finally lock to the voice.
  * **Calmer pacing** — a slower rate and a slight per-genre pitch drop.

Order of preference per scene: edge-tts streaming (gives word boundaries) →
Kokoro-82M if its model files are cached (higher fidelity, but no boundaries, so
those scenes fall back to proportional timing). Everything degrades gracefully.
"""

from __future__ import annotations

import asyncio
import io
import re
from pathlib import Path
from typing import List, Tuple

from pydub import AudioSegment

try:
    from . import config
    from .schema import OmniRenderPayload, SceneSpec, WordTimestamp
except ImportError:  # pragma: no cover
    import config  # type: ignore
    from schema import OmniRenderPayload, SceneSpec, WordTimestamp  # type: ignore

TARGET_SR = config.AUDIO_SAMPLE_RATE

# A span is (text, start_sec_within_scene, end_sec_within_scene). edge-tts emits
# these from the TTS engine itself — word-level if the service provides it, else
# sentence-level (the current behaviour), which we sub-divide into words.
Span = Tuple[str, float, float]
_WORD_RE = re.compile(r"[^\w'%$.\-]")


# ---------------------------------------------------------------------------
# Voice persona selection
# ---------------------------------------------------------------------------
def _edge_voices(genre: str) -> List[str]:
    primary = config.GENRE_EDGE_VOICE.get(genre, config.DEFAULT_EDGE_VOICE)
    return [primary, *config.EDGE_TTS_FALLBACK_VOICES]


def _edge_pitch(genre: str) -> str:
    return config.GENRE_EDGE_PITCH.get(genre, config.EDGE_TTS_PITCH)


def _kokoro_voice(genre: str) -> str:
    return config.GENRE_KOKORO_VOICE.get(genre, "am_adam")


# ---------------------------------------------------------------------------
# edge-tts streaming synth WITH word boundaries (primary)
# ---------------------------------------------------------------------------
async def _edge_stream(text: str, voice: str, pitch: str) -> Tuple[bytes, List[Span], str]:
    """Return (mp3_bytes, spans, level). `level` is 'word' | 'sentence' | 'none'.
    offset / duration arrive in 100-nanosecond ticks (1e7 per second)."""
    import edge_tts  # type: ignore

    comm = edge_tts.Communicate(
        text,
        voice=voice,
        rate=config.EDGE_TTS_RATE,
        volume=config.EDGE_TTS_VOLUME,
        pitch=pitch,
    )
    audio = bytearray()
    words: List[Span] = []
    sentences: List[Span] = []
    async for chunk in comm.stream():
        ctype = chunk.get("type")
        if ctype == "audio" and chunk.get("data"):
            audio.extend(chunk["data"])
        elif ctype in ("WordBoundary", "SentenceBoundary"):
            start = float(chunk.get("offset", 0)) / 1e7
            dur = float(chunk.get("duration", 0)) / 1e7
            txt = (chunk.get("text") or "").strip()
            if not txt:
                continue
            (words if ctype == "WordBoundary" else sentences).append((txt, start, start + dur))
    if words:
        return bytes(audio), words, "word"
    if sentences:
        return bytes(audio), sentences, "sentence"
    return bytes(audio), [], "none"


def _synth_scene_edge(text: str, genre: str) -> Tuple[AudioSegment, List[Span], str] | Tuple[None, list, str]:
    pitch = _edge_pitch(genre)
    for voice in _edge_voices(genre):
        try:
            audio_bytes, spans, level = asyncio.run(_edge_stream(text, voice, pitch))
            if not audio_bytes:
                raise RuntimeError("no audio returned")
            seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
            seg = seg.set_channels(1).set_frame_rate(TARGET_SR)
            return seg, spans, level
        except Exception as exc:  # noqa: BLE001
            print(f"[audio] edge-tts voice '{voice}' failed ({exc}); trying next.")
    return None, [], "none"


# ---------------------------------------------------------------------------
# Kokoro (optional higher-fidelity local voice; no word boundaries)
# ---------------------------------------------------------------------------
_KOKORO_MODEL = None


def _try_load_kokoro():
    global _KOKORO_MODEL
    if _KOKORO_MODEL is not None:
        return _KOKORO_MODEL
    try:
        from kokoro_onnx import Kokoro  # type: ignore
    except ImportError:
        return None

    search = [config.BACKEND_DIR / ".cache", config.BACKEND_DIR, Path.cwd()]
    model_path = voices_path = None
    for base in search:
        for mname, vname in (("kokoro-v0_19.onnx", "voices-v1.0.bin"), ("kokoro.onnx", "voices.bin")):
            m, v = base / mname, base / vname
            if m.exists() and v.exists():
                model_path, voices_path = m, v
                break
        if model_path:
            break
    if not model_path:
        return None
    try:
        _KOKORO_MODEL = Kokoro(str(model_path), str(voices_path))
        print(f"[audio] Loaded Kokoro from {model_path}")
        return _KOKORO_MODEL
    except Exception as exc:  # noqa: BLE001
        print(f"[audio] Kokoro load failed ({exc}); using edge-tts.")
        return None


def _synth_scene_kokoro(kokoro, text: str, genre: str) -> AudioSegment | None:
    try:
        import numpy as np  # noqa: F401
        import soundfile as sf  # type: ignore

        samples, sr = kokoro.create(text, voice=_kokoro_voice(genre), speed=config.KOKORO_SPEED, lang="en-us")
        buf = io.BytesIO()
        sf.write(buf, samples, sr, format="WAV")
        buf.seek(0)
        seg = AudioSegment.from_file(buf, format="wav").set_channels(1).set_frame_rate(TARGET_SR)
        return seg
    except Exception as exc:  # noqa: BLE001
        print(f"[audio] Kokoro synth failed ({exc}); using edge-tts.")
        return None


# ---------------------------------------------------------------------------
# Per-scene synthesis
# ---------------------------------------------------------------------------
def _synthesize_scene(kokoro, text: str, genre: str) -> Tuple[AudioSegment, List[Span], str]:
    """Return (audio, spans, level). Spans/level are empty/'none' when the voice
    path can't provide timing (Kokoro / total failure); the caller interpolates."""
    text = text.strip() or "…"
    # Prefer edge-tts because it yields timing spans from the engine itself.
    seg, spans, level = _synth_scene_edge(text, genre)
    if seg is not None:
        return seg, spans, level
    # Kokoro has no timing metadata but is still good audio.
    if kokoro is not None:
        kseg = _synth_scene_kokoro(kokoro, text, genre)
        if kseg is not None:
            return kseg, [], "none"
    # Last resort: silence sized to a plausible reading pace (no crash).
    dur = max(800, int(len(text.split()) / 2.4 * 1000))
    return AudioSegment.silent(duration=dur, frame_rate=TARGET_SR), [], "none"


def _distribute(words: List[str], start: float, end: float) -> List[Span]:
    """Spread words across [start, end], weighted by length so long words (which
    take longer to say) get proportionally more time than short ones."""
    words = [w for w in words if w]
    if not words:
        return []
    span = max(0.0, end - start)
    weights = [len(w) + 1.5 for w in words]  # +1.5 ≈ the gap/padding after a word
    total = sum(weights) or 1.0
    out: List[Span] = []
    t = start
    for w, wt in zip(words, weights):
        dt = span * wt / total
        out.append((w, t, t + dt))
        t += dt
    return out


def _scene_words(scene: SceneSpec, spans: List[Span], level: str, scene_start_ms: int) -> List[WordTimestamp]:
    base = scene_start_ms / 1000.0
    out: List[WordTimestamp] = []

    if level == "word" and spans:
        for word, s, e in spans:
            out.append(WordTimestamp(word=word, start_sec=round(base + s, 3), end_sec=round(base + e, 3)))
        return out

    if level == "sentence" and spans:
        # Exact per-sentence anchors from the engine; sub-divide each sentence
        # into its words so the karaoke cursor can never drift across a pause.
        for text, s, e in spans:
            toks = [_WORD_RE.sub("", t) for t in text.split()]
            for word, ws, we in _distribute(toks, s, e):
                out.append(WordTimestamp(word=word, start_sec=round(base + ws, 3), end_sec=round(base + we, 3)))
        return out

    # No engine timing at all (Kokoro / silence): spread across the whole scene.
    toks = [_WORD_RE.sub("", t) for t in scene.narration_text.split()]
    for word, ws, we in _distribute(toks, 0.0, scene.duration_sec):
        out.append(WordTimestamp(word=word, start_sec=round(base + ws, 3), end_sec=round(base + we, 3)))
    return out


def _ends_sentence(text: str) -> bool:
    return text.rstrip().endswith((".", "!", "?", "…"))


# ---------------------------------------------------------------------------
# Scene synthesis + stitching (now also produces exact word timings)
# ---------------------------------------------------------------------------
def synthesize_narration(payload: OmniRenderPayload) -> AudioSegment:
    kokoro = _try_load_kokoro()
    master = AudioSegment.silent(duration=0, frame_rate=TARGET_SR)
    all_words: List[WordTimestamp] = []

    cursor_ms = 0
    for i, scene in enumerate(payload.scenes):
        seg, spans, level = _synthesize_scene(kokoro, scene.narration_text, payload.genre)
        scene.start_sec = round(cursor_ms / 1000.0, 3)
        scene.duration_sec = round(len(seg) / 1000.0, 3)
        all_words.extend(_scene_words(scene, spans, level, cursor_ms))

        master += seg
        cursor_ms += len(seg)
        if i < len(payload.scenes) - 1:
            gap = config.SCENE_GAP_MS + (config.SENTENCE_TAIL_MS if _ends_sentence(scene.narration_text) else 0)
            master += AudioSegment.silent(duration=gap, frame_rate=TARGET_SR)
            cursor_ms += gap

    payload.words = all_words
    payload.total_duration_sec = round(len(master) / 1000.0, 3)
    master.export(config.NARRATION_PATH, format="wav")
    print(
        f"[audio] Stitched {len(payload.scenes)} scenes ({payload.genre}) · "
        f"{payload.total_duration_sec:.1f}s · {len(all_words)} words -> {config.NARRATION_PATH}"
    )
    return master


# ---------------------------------------------------------------------------
# Word-level alignment (now a no-op when synthesis already produced boundaries;
# kept so the pipeline stage structure and a whisper upgrade path still exist)
# ---------------------------------------------------------------------------
def _decode_for_whisper():
    import numpy as np
    import soundfile as sf  # type: ignore

    audio, sr = sf.read(str(config.NARRATION_PATH), dtype="float32")
    if getattr(audio, "ndim", 1) > 1:
        audio = audio.mean(axis=1)
    target = 16_000
    if sr != target:
        n = int(len(audio) * target / sr)
        audio = np.interp(
            np.linspace(0, len(audio), n, endpoint=False),
            np.arange(len(audio)),
            audio,
        ).astype("float32")
    return np.ascontiguousarray(audio, dtype="float32")


def _align_with_whisper(payload: OmniRenderPayload) -> bool:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError:
        return False
    try:
        model = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type=config.WHISPER_COMPUTE_TYPE)
        audio = _decode_for_whisper()
        segments, _ = model.transcribe(audio, word_timestamps=True, language="en")
        words: List[WordTimestamp] = []
        for seg in segments:
            for w in seg.words or []:
                words.append(
                    WordTimestamp(word=w.word.strip(), start_sec=round(float(w.start), 3), end_sec=round(float(w.end), 3))
                )
        if not words:
            return False
        payload.words = words
        print(f"[audio] faster-whisper re-aligned {len(words)} words.")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[audio] faster-whisper alignment failed ({exc}).")
        return False


def align_words(payload: OmniRenderPayload) -> None:
    """Keep the exact boundaries from synthesis. Only if none were produced do we
    try faster-whisper, then a flat proportional pass as the final safety net."""
    if payload.words:
        return
    if _align_with_whisper(payload):
        return
    words: List[WordTimestamp] = []
    for scene in payload.scenes:
        words.extend(_scene_words(scene, [], "none", int(scene.start_sec * 1000)))
    payload.words = words
    print(f"[audio] Proportional timing produced {len(words)} words.")


# ---------------------------------------------------------------------------
# Background music
# ---------------------------------------------------------------------------
def apply_music_bed(master: AudioSegment, mood: str) -> AudioSegment:
    return _mix_background_music(master, mood)


def _mix_background_music(master: AudioSegment, mood: str) -> AudioSegment:
    try:
        from . import music_engine
    except ImportError:  # pragma: no cover
        import music_engine  # type: ignore
    try:
        bed = music_engine.build_music_bed(len(master), mood=mood)
    except Exception as exc:  # noqa: BLE001
        print(f"[audio] background music skipped ({exc}).")
        return master
    if bed is None:
        return master
    print(f"[audio] mixed '{mood}' bed under {len(master) / 1000:.1f}s of narration.")
    return master.overlay(bed)


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------
def build_audio(payload: OmniRenderPayload, save: bool = True) -> OmniRenderPayload:
    master = synthesize_narration(payload)            # clean narration.wav + exact words
    align_words(payload)                              # no-op unless boundaries missing
    master = _mix_background_music(master, payload.suggested_bgm_mood)
    master.export(str(config.NARRATION_PATH), format="wav")
    if save:
        _save_payload(payload)
    return payload


def _save_payload(payload: OmniRenderPayload) -> None:
    import json

    with open(config.RENDER_PAYLOAD_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload.model_dump(), fh, indent=2, ensure_ascii=False)
    print(f"[audio] Wrote render payload -> {config.RENDER_PAYLOAD_PATH}")


if __name__ == "__main__":
    import json

    with open(config.RENDER_PAYLOAD_PATH, encoding="utf-8") as fh:
        p = OmniRenderPayload.model_validate(json.load(fh))
    build_audio(p)
