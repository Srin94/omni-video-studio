"""Validate, stamp and lightly repair an `OmniRenderPayload` (spec View 3).

The browser LLM's pasted JSON is validated against the strict contract; this
module turns raw text into a clean, renderable payload with friendly error
messages for the studio's "Validate Schema" badges, plus deterministic safety
nets so no scene renders empty and provisional timings exist before TTS.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import List, Optional

from pydantic import ValidationError

try:
    from . import config
    from . import illustration_infer
    from .schema import (
        OmniRenderPayload,
        SceneSpec,
        VisualElement,
        GENRE_DEFAULT_MOOD,
        GENRE_DEFAULT_ARCHETYPE,
    )
except ImportError:  # pragma: no cover
    import config  # type: ignore
    import illustration_infer  # type: ignore
    from schema import (  # type: ignore
        OmniRenderPayload, SceneSpec, VisualElement,
        GENRE_DEFAULT_MOOD, GENRE_DEFAULT_ARCHETYPE,
    )

_FENCE = re.compile(r"^\s*```[a-zA-Z0-9]*\s*|\s*```\s*$")


@dataclass
class ValidationReport:
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    payload: Optional[OmniRenderPayload] = None
    # Light summary for the UI "summary card".
    summary: dict = field(default_factory=dict)


def _strip_fences(text: str) -> str:
    t = text.strip()
    # Drop a leading ```json / trailing ``` if the model added them anyway.
    t = re.sub(r"^\s*```[a-zA-Z0-9]*\s*", "", t)
    t = re.sub(r"\s*```\s*$", "", t)
    return t.strip()


def _extract_json(text: str) -> str:
    """Best-effort: pull the outermost {...} object out of pasted text."""
    t = _strip_fences(text)
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        return t[start : end + 1]
    return t


def _friendly_errors(exc: ValidationError) -> List[str]:
    out: List[str] = []
    for err in exc.errors()[:25]:
        loc = ".".join(str(p) for p in err.get("loc", ()))
        out.append(f"{loc or '(root)'}: {err.get('msg', 'invalid')}")
    return out


def validate(raw: str, video_format: str = "landscape", sources: Optional[List[str]] = None) -> ValidationReport:
    """Validate pasted model output into a clean, stamped payload."""
    if not raw or not raw.strip():
        return ValidationReport(ok=False, errors=["No JSON pasted."])

    try:
        data = json.loads(_extract_json(raw))
    except json.JSONDecodeError as exc:
        return ValidationReport(ok=False, errors=[f"Not valid JSON: {exc.msg} (line {exc.lineno}, col {exc.colno})."])

    try:
        payload = OmniRenderPayload.model_validate(data)
    except ValidationError as exc:
        return ValidationReport(ok=False, errors=_friendly_errors(exc))

    warnings: List[str] = []
    _stamp(payload, video_format, sources or [])
    _repair(payload, warnings)
    renumber_scenes(payload)
    seed_provisional_timings(payload)
    # Backfill animated illustrations the model didn't specify (safe, offline).
    illustration_infer.infer_payload(payload)

    return ValidationReport(
        ok=True,
        warnings=warnings,
        payload=payload,
        summary=summarize(payload),
    )


def _stamp(payload: OmniRenderPayload, video_format: str, sources: List[str]) -> None:
    payload.video_format = video_format if video_format in config.VIDEO_DIMENSIONS else "landscape"
    if sources and not payload.source_urls:
        payload.source_urls = sources
    # Backfill a sensible mood if the model left it off-genre or blank-ish.
    if not payload.suggested_bgm_mood:
        payload.suggested_bgm_mood = GENRE_DEFAULT_MOOD.get(payload.genre, "minimal_tension")  # type: ignore[assignment]


def _default_archetype_for(payload: OmniRenderPayload) -> str:
    return GENRE_DEFAULT_ARCHETYPE.get(payload.genre, "NEON_TECHNICAL_HUD")


def _repair(payload: OmniRenderPayload, warnings: List[str]) -> None:
    """Guarantee every scene has narration + at least one visual element."""
    for sc in payload.scenes:
        if not sc.narration_text.strip():
            sc.narration_text = sc.chapter_title or "..."
            warnings.append(f"Scene {sc.scene_id}: empty narration backfilled.")
        if not sc.visual_elements:
            sc.visual_elements = [
                VisualElement(
                    element_type="stat_card",
                    headline=sc.chapter_title or "Key point",
                    subtext=(sc.callout_keywords[0] if sc.callout_keywords else sc.narration_text[:60]),
                    highlight_color="cyan",
                )
            ]
            warnings.append(f"Scene {sc.scene_id}: no visual_elements; added a stat_card.")
        # Trim to the schema caps so a generous model can't overflow a canvas.
        sc.visual_elements = sc.visual_elements[:3]
        sc.hud_metrics = sc.hud_metrics[:4]
    if not payload.scenes:
        warnings.append("Payload has zero scenes.")


def renumber_scenes(payload: OmniRenderPayload) -> None:
    for i, sc in enumerate(payload.scenes, start=1):
        sc.scene_id = i


def seed_provisional_timings(payload: OmniRenderPayload) -> None:
    """Rough timing estimate (~2.6 words/sec) before real TTS alignment."""
    cursor = 0.0
    for sc in payload.scenes:
        words = max(1, len(sc.narration_text.split()))
        dur = round(words / 2.6, 2)
        sc.start_sec = round(cursor, 2)
        sc.duration_sec = dur
        cursor += dur + config.SCENE_GAP_MS / 1000.0
    if payload.total_duration_sec <= 0:
        payload.total_duration_sec = round(cursor, 2)


def summarize(payload: OmniRenderPayload) -> dict:
    archetypes = sorted({s.visual_archetype for s in payload.scenes})
    return {
        "youtube_title": payload.youtube_title,
        "genre": payload.genre,
        "video_format": payload.video_format,
        "bgm_mood": payload.suggested_bgm_mood,
        "scene_count": len(payload.scenes),
        "estimated_duration_sec": payload.total_duration_sec,
        "archetypes_used": archetypes,
        "tag_count": len(payload.youtube_tags),
    }


def save_payload(payload: OmniRenderPayload, path=None) -> None:
    path = path or config.RENDER_PAYLOAD_PATH
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload.model_dump(), fh, indent=2, ensure_ascii=False)
    print(f"[payload] Wrote render payload -> {path}")
