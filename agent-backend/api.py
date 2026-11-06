"""FastAPI backend for the Omni Video Studio web app (spec section 6).

Endpoints
    GET  /api/health             liveness + feature flags
    GET  /api/trends             zero-cost trending radar (optional ?genre=)
    POST /api/prepare-prompt     scrape grounding + assemble the Master Prompt
    POST /api/validate-json      validate pasted model output vs OmniRenderPayload
    POST /api/start-render       launch the render + pipeline, returns job_id
    GET  /api/status/{job_id}    poll the live pipeline stepper

Run:  uvicorn api:app --reload --port 8000   (from agent-backend/)
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

import json  # noqa: E402

import config  # type: ignore  # noqa: E402
import trends as trends_mod  # type: ignore  # noqa: E402
import reference_gatherer  # type: ignore  # noqa: E402
import prompt_assembler  # type: ignore  # noqa: E402
import payload_ops  # type: ignore  # noqa: E402
import pipeline  # type: ignore  # noqa: E402
import github_dispatch  # type: ignore  # noqa: E402
from schema import Genre, VideoFormat  # type: ignore  # noqa: E402

app = FastAPI(title="Omni Video Studio API", version="1.0.0")

# The Vite studio runs on :3000 / :5173 locally. When the studio is deployed
# (e.g. Cloudflare Pages / GitHub Pages), add its origin(s) via the CORS_ORIGINS
# env var — a comma-separated list, e.g.
#   CORS_ORIGINS=https://my-studio.pages.dev,https://studio.example.com
_cors_origins = [
    "http://localhost:3000", "http://127.0.0.1:3000",
    "http://localhost:5173", "http://127.0.0.1:5173",
]
_cors_origins += [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class PreparePromptBody(BaseModel):
    topic: str = Field(min_length=2)
    genre: Genre
    format: VideoFormat = "landscape"


class ValidateBody(BaseModel):
    json_text: str
    format: VideoFormat = "landscape"
    sources: List[str] = Field(default_factory=list)


class StartRenderBody(BaseModel):
    json_text: str
    format: VideoFormat = "landscape"
    sources: List[str] = Field(default_factory=list)
    dry_run: bool = False
    skip_approval: bool = False
    skip_video: bool = False


class DispatchRenderBody(BaseModel):
    json_text: str
    format: VideoFormat = "landscape"
    sources: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "channel": config.CHANNEL_NAME,
        "telegram_configured": config.has_telegram(),
        "youtube_configured": config.has_youtube_credentials(),
        "github_configured": config.has_github(),
        "trends_geos": config.GOOGLE_TRENDS_GEOS,
    }


@app.get("/api/trends")
def get_trends(genre: Optional[str] = None, force: bool = False) -> dict:
    cards = trends_mod.get_trends(force=force, genre=genre)
    return {"count": len(cards), "genre": genre or "ALL", "trends": cards}


@app.post("/api/prepare-prompt")
def prepare_prompt(body: PreparePromptBody) -> dict:
    ref = reference_gatherer.gather(body.topic)
    assembled = prompt_assembler.assemble(
        topic=body.topic,
        genre=body.genre,
        video_format=body.format,
        reference_markdown=ref.markdown,
        sources=ref.sources,
    )
    assembled["reference_method"] = ref.method
    assembled["reference_preview"] = ref.markdown[:1200]
    return assembled


@app.post("/api/validate-json")
def validate_json(body: ValidateBody) -> dict:
    report = payload_ops.validate(body.json_text, video_format=body.format, sources=body.sources)
    return {
        "ok": report.ok,
        "errors": report.errors,
        "warnings": report.warnings,
        "summary": report.summary,
    }


@app.post("/api/start-render")
def start_render(body: StartRenderBody) -> dict:
    report = payload_ops.validate(body.json_text, video_format=body.format, sources=body.sources)
    if not report.ok or report.payload is None:
        raise HTTPException(status_code=422, detail={"errors": report.errors})
    job_id = pipeline.start_job(
        report.payload,
        dry_run=body.dry_run,
        skip_approval=body.skip_approval,
        skip_video=body.skip_video,
    )
    return {"job_id": job_id, "summary": report.summary, "warnings": report.warnings}


@app.post("/api/dispatch-render")
def dispatch_render(body: DispatchRenderBody) -> dict:
    """Validate the payload and commit it to render-jobs/ on GitHub, which fires
    the Actions render workflow. This is the hosted/mobile path — rendering runs
    on a GitHub runner, not on this server."""
    report = payload_ops.validate(body.json_text, video_format=body.format, sources=body.sources)
    if not report.ok or report.payload is None:
        raise HTTPException(status_code=422, detail={"errors": report.errors})
    if not github_dispatch.configured():
        raise HTTPException(
            status_code=503,
            detail=("GitHub dispatch is not configured. Set GITHUB_TOKEN (a fine-grained "
                    "PAT with Contents: write on the repo) in the backend environment."),
        )
    # Commit the validated+stamped payload so CI renders exactly what was shown.
    payload_json = json.dumps(report.payload.model_dump(), ensure_ascii=False, indent=2)
    title = report.payload.youtube_title or "Omni video"
    try:
        result = github_dispatch.commit_payload(payload_json, title)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"ok": True, "title": title, "summary": report.summary, **result}


@app.get("/api/status/{job_id}")
def status(job_id: str) -> dict:
    job = pipeline.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="unknown job_id")
    return job
