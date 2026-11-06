"""End-to-end render + publish orchestrator with live job status (spec View 3).

A job runs on a background thread and advances a stepper the web UI polls:

    [1] Grounding & Script Ingested
    [2] Generating Natural Voiceover & Word Timestamps
    [3] Mixing Topic-Matched Background Music
    [4] Rendering Remotion Frames (1080p60)
    [5] Dispatching Telegram HITL Preview
    [6] Uploading to YouTube

Each stage carries a status (pending|running|done|skipped|error). Jobs live in an
in-process registry keyed by job_id. Safe for a single-worker uvicorn; a
multi-worker deploy would swap this for Redis.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

try:
    from . import config
    from . import audio_engine
    from . import broll_fetcher
    from . import thumbnail_generator
    from . import telegram_gate
    from . import youtube_publisher
    from . import payload_ops
    from .schema import OmniRenderPayload
except ImportError:  # pragma: no cover
    import config  # type: ignore
    import audio_engine  # type: ignore
    import broll_fetcher  # type: ignore
    import thumbnail_generator  # type: ignore
    import telegram_gate  # type: ignore
    import youtube_publisher  # type: ignore
    import payload_ops  # type: ignore
    from schema import OmniRenderPayload  # type: ignore


STAGE_KEYS = [
    ("ingest", "Grounding & Script Ingested"),
    ("voice", "Generating Natural Voiceover & Word Timestamps"),
    ("music", "Mixing Topic-Matched Background Music"),
    ("broll", "Fetching Topic-Matched B-roll Imagery"),
    ("render", "Rendering Remotion Frames (1080p60)"),
    ("telegram", "Dispatching Telegram HITL Preview"),
    ("upload", "Uploading to YouTube"),
]


@dataclass
class Stage:
    key: str
    label: str
    status: str = "pending"  # pending|running|done|skipped|error
    detail: str = ""


@dataclass
class Job:
    job_id: str
    stages: List[Stage]
    status: str = "queued"  # queued|running|done|error
    title: str = ""
    created_at: float = field(default_factory=time.time)
    video_id: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["elapsed_sec"] = round(time.time() - self.created_at, 1)
        return d


_JOBS: Dict[str, Job] = {}
_LOCK = threading.Lock()


def _new_job(title: str) -> Job:
    job = Job(
        job_id=uuid.uuid4().hex[:12],
        stages=[Stage(k, label) for k, label in STAGE_KEYS],
        title=title,
    )
    with _LOCK:
        _JOBS[job.job_id] = job
    return job


def get_job(job_id: str) -> Optional[dict]:
    with _LOCK:
        job = _JOBS.get(job_id)
        return job.to_dict() if job else None


def _stage(job: Job, key: str) -> Stage:
    return next(s for s in job.stages if s.key == key)


def _set(job: Job, key: str, status: str, detail: str = "") -> None:
    st = _stage(job, key)
    st.status = status
    if detail:
        st.detail = detail


# ---------------------------------------------------------------------------
# Remotion render
# ---------------------------------------------------------------------------
def render_video(payload: OmniRenderPayload) -> bool:
    """Compile the MP4 via the Remotion CLI at the payload's format dimensions."""
    config.VIDEO_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    if config.NARRATION_PATH.exists():
        shutil.copy(config.NARRATION_PATH, config.VIDEO_ASSETS_DIR / "narration.wav")
    payload_ops.save_payload(payload, config.VIDEO_ASSETS_DIR / "render_payload.json")
    payload_ops.save_payload(payload, config.RENDER_PAYLOAD_PATH)

    # Dimensions are derived from payload.video_format inside the composition's
    # calculateMetadata (see video-engine/src/Root.tsx), so no size flags here.
    npx = shutil.which("npx") or "npx"
    cmd = [
        npx, "remotion", "render", "src/index.ts",
        config.REMOTION_COMPOSITION_ID,
        str(config.FINAL_VIDEO_PATH),
        "--codec=h264",
    ]
    print(f"[pipeline] Rendering: {' '.join(cmd)} (cwd={config.VIDEO_ENGINE_DIR})")
    try:
        subprocess.run(cmd, cwd=str(config.VIDEO_ENGINE_DIR), check=True, shell=(os.name == "nt"))
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"[pipeline] Remotion render failed: {exc}")
        return False
    ok = config.FINAL_VIDEO_PATH.exists()
    print(f"[pipeline] Video rendered: {ok} -> {config.FINAL_VIDEO_PATH}")
    return ok


# ---------------------------------------------------------------------------
# The worker
# ---------------------------------------------------------------------------
def _run(job: Job, payload: OmniRenderPayload, dry_run: bool, skip_approval: bool, skip_video: bool) -> None:
    job.status = "running"
    try:
        # [1] Ingest (already validated/stamped by the caller).
        _set(job, "ingest", "running")
        payload_ops.save_payload(payload)
        _set(job, "ingest", "done", f"{len(payload.scenes)} scenes · {payload.genre}")

        # [2] Voiceover + word timestamps.
        _set(job, "voice", "running")
        master = audio_engine.synthesize_narration(payload)
        audio_engine.align_words(payload)
        _set(job, "voice", "done", f"{payload.total_duration_sec:.0f}s · {len(payload.words)} words")

        # [3] Background music bed.
        _set(job, "music", "running")
        master = audio_engine.apply_music_bed(master, payload.suggested_bgm_mood)
        master.export(str(config.NARRATION_PATH), format="wav")
        payload_ops.save_payload(payload)
        _set(job, "music", "done", payload.suggested_bgm_mood)

        # [3.5] Topic-matched B-roll imagery (never fatal — scenes without an
        # image just render on their archetype canvas).
        _set(job, "broll", "running")
        try:
            got = broll_fetcher.fetch_broll(payload)
            credits = broll_fetcher.attribution_block(payload)
            if credits and credits not in payload.youtube_description:
                payload.youtube_description = payload.youtube_description.rstrip() + "\n\n" + credits
            payload_ops.save_payload(payload)
            _set(job, "broll", "done" if got else "skipped", f"{got}/{len(payload.scenes)} scenes")
        except Exception as exc:  # noqa: BLE001
            print(f"[pipeline] B-roll fetch failed (continuing): {exc}")
            _set(job, "broll", "skipped", str(exc)[:80])

        # Thumbnail (best-effort; not a stepper stage, surfaced in render detail).
        try:
            thumbnail_generator.render_thumbnail(payload)
        except Exception as exc:  # noqa: BLE001
            print(f"[pipeline] Thumbnail render failed (continuing): {exc}")

        # [4] Remotion render.
        if skip_video:
            _set(job, "render", "skipped", "--skip-video")
        else:
            _set(job, "render", "running")
            ok = render_video(payload)
            _set(job, "render", "done" if ok else "error", "" if ok else "render failed")

        # [5] Telegram HITL approval.
        approved = True
        if skip_approval:
            _set(job, "telegram", "skipped", "--skip-approval")
        else:
            _set(job, "telegram", "running")
            decision = telegram_gate.request_approval(payload)
            approved = decision.approved
            _set(job, "telegram", "done", decision.reason)

        # [6] YouTube upload.
        if not approved:
            _set(job, "upload", "skipped", "not approved")
        elif dry_run:
            _set(job, "upload", "skipped", "--dry-run")
        else:
            _set(job, "upload", "running")
            video_id = youtube_publisher.publish(payload)
            job.video_id = video_id
            _set(job, "upload", "done", f"https://youtu.be/{video_id}" if video_id else "no credentials / skipped")

        job.status = "done"
    except Exception as exc:  # noqa: BLE001
        job.status = "error"
        job.error = str(exc)
        for st in job.stages:
            if st.status == "running":
                st.status = "error"
                st.detail = str(exc)
        print(f"[pipeline] Job {job.job_id} failed: {exc}")


def start_job(
    payload: OmniRenderPayload,
    dry_run: bool = False,
    skip_approval: bool = False,
    skip_video: bool = False,
) -> str:
    """Kick off a render+publish job on a background thread; return its id."""
    job = _new_job(payload.youtube_title or "Untitled")
    thread = threading.Thread(
        target=_run, args=(job, payload, dry_run, skip_approval, skip_video), daemon=True
    )
    thread.start()
    return job.job_id
