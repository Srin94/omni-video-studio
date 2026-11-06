# omni-video-studio

A genre-agnostic Web Studio + autonomous video rendering pipeline. Unlike the
single-domain sibling agents (`swe-youtube-agent`, `study-youtube-agent`), this
platform handles **science, history, economics, pop culture, crime mysteries,
tech and philosophy** — and uses a **Hybrid Human-in-the-Loop (HITL) prompt-relay
architecture**: instead of burning an LLM API quota on script generation, the
backend scrapes reference material, compiles a master prompt with a strict JSON
schema, and hands you a one-click copyable prompt for Gemini Advanced / Claude Pro
in your browser. Paste the JSON back and the backend synthesizes voiceover, mixes
mood-matched BGM, renders animated Remotion scenes, and dispatches to Telegram and
YouTube.

```
web-studio/      React + Vite + Tailwind dashboard (3 views, mobile-first)
agent-backend/   FastAPI pipeline (trends, prompt relay, audio, thumbnail, publish)
video-engine/    Remotion v4 adaptive multi-archetype renderer
```

## The flow

1. **Topic & Radar** — type a topic, or pick one from the zero-cost Live Idea Radar
   (Google Trends RSS + Reddit, each scored with a *Hook Score*). Choose 16:9
   (3-5 min) or 9:16 (60s).
2. **Prompt Relay** — the backend Jina-reads Wikipedia + DuckDuckGo for factual
   grounding and assembles a Master Synthesis Prompt embedding the exact
   `OmniRenderPayload` JSON schema. Copy it → paste into Gemini/Claude → copy the
   JSON it returns. The prompt asks the model to give each scene a concrete
   `broll_query` (the visual subject to show).
3. **Ingest & Render** — paste the JSON, hit *Validate Schema*, then *Launch Render
   & Pipeline* and watch the live stepper: voiceover → music → **B-roll** →
   Remotion → Telegram approval → YouTube.

### What makes the video feel like a video (not a slideshow)

- **Topic-matched B-roll.** For every scene the backend resolves `broll_query`
  to a real, freely-licensed photo/diagram from **Openverse** and floats it
  behind the narration with a slow Ken-Burns move. So when the script says
  "neuron", you see a neuron. Images are **relevance-gated** (a hit must match
  the subject's words) — a scene with no confident match cleanly falls back to
  its archetype canvas instead of showing something wrong. Credit is required by
  CC and is rendered on-screen + appended to the description automatically.
- **Voice that isn't robotic.** Each scene is synthesized as one whole take
  (natural sentence prosody), paced slightly slower, with a per-genre pitch.
- **Captions that lock to the voice.** Word timings come straight from the TTS
  engine's sentence boundaries — frame-accurate karaoke with **no ML model
  required** (works on Python 3.13/3.14).
- **BGM that's actually different per video.** The procedural engine has a
  distinct profile per mood (register, tempo, and a motif — swell / pulse /
  arpeggio / pluck / two-note), reseeded every render.

The one contract that ties it all together is `OmniRenderPayload`, defined once in
[`agent-backend/src/schema.py`](agent-backend/src/schema.py) and mirrored in
[`video-engine/src/types/schema.ts`](video-engine/src/types/schema.ts). Keep them
in lock-step.

## Quick start

### 1. Backend (FastAPI, port 8000)

```bash
cd agent-backend
python -m venv .venv && . .venv/Scripts/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt                        # core — installs everywhere
playwright install chromium                             # for thumbnails
cp ../.env.example ../.env                              # optional: Telegram / YouTube
uvicorn api:app --reload --port 8000
```

No LLM API key is required — script generation is the browser prompt relay.
Telegram and YouTube creds are optional and only gate the publish step.

Caption sync and B-roll need **no** heavy ML — they work on the core install
alone. **Optional local-ML extras** (nicer Kokoro voice + `faster-whisper`
re-alignment) live in `requirements-ml.txt`:

```bash
pip install -r requirements-ml.txt
```

These pull in `onnxruntime` / `ctranslate2`, which only ship wheels for released
Python versions — so on Python 3.13/3.14 this may fail with *"No matching
distribution for onnxruntime"*. That's expected and harmless: **skip this file**
(or use a Python 3.12 venv for it) and the audio engine falls back to `edge-tts`
voice + proportional word timing, so the full pipeline still runs.

### 2. Web studio (Vite, port 3000)

```bash
cd web-studio
npm install
npm run dev        # http://localhost:3000  (proxies /api -> :8000)
```

### 3. Video engine (Remotion)

```bash
cd video-engine
npm install
npm start          # Remotion Studio preview (uses the bundled sample payload)
```

The backend invokes `remotion render` for you during a job; you only run the engine
directly to preview or debug scenes.

## CLI (no web UI)

Script generation stays human-in-the-loop, so the CLI prints the master prompt and
waits for you to paste the model's JSON back:

```bash
cd agent-backend
python main.py --topic "How Shazam works" --genre EVERYDAY_TECH \
  --manual-prompt --dry-run --skip-approval
```

Or run straight from an already-saved payload:

```bash
python main.py --payload output/render_payload.json --dry-run --skip-approval
```

> **Safety:** pair `--dry-run` with `--skip-approval` for local tests so nothing is
> ever published to YouTube or sent to the Telegram gate.

## API

| Method | Path                   | Purpose                                            |
| ------ | ---------------------- | -------------------------------------------------- |
| GET    | `/api/health`          | liveness + which integrations are configured       |
| GET    | `/api/trends`          | zero-cost trending radar (`?genre=`, `?force=`)    |
| POST   | `/api/prepare-prompt`  | scrape grounding + assemble the Master Prompt      |
| POST   | `/api/validate-json`   | validate pasted model output vs `OmniRenderPayload`|
| POST   | `/api/start-render`    | launch the render + pipeline, returns `job_id`     |
| GET    | `/api/status/{job_id}` | poll the live pipeline stepper                     |

## Visual archetypes

Each scene picks one of four canvases (the Adaptive Layout Director mounts the
matching component):

- **DOCUMENTARY_ARCHIVE** — warm paper, grain, ink stamps, typewriter titles.
- **KINETIC_MINIMALIST** — stark high-contrast, giant kinetic numbers.
- **NEON_TECHNICAL_HUD** — oscilloscope console, telemetry, flow nodes.
- **NARRATIVE_STORYBOARD** — cinematic letterbox + timeline breadcrumbs.

Shared on top of every archetype: word-level **karaoke subtitles**, floating
**HUD telemetry** cards, and a continuous **camera drift** per `camera_movement`.

## Notes & graceful degradation

- **Audio** uses `edge-tts` (whole-scene takes for natural prosody, per-genre
  voice + pitch), or local Kokoro-82M if its model files are cached. Word timings
  come from the TTS engine's own **sentence boundaries** (exact, no ML model);
  `faster-whisper`, if installed, can re-align, and there is a proportional
  safety net.
- **B-roll** resolves each scene's `broll_query` to a freely-licensed image via
  **Openverse**, relevance-gated and always attributed. Knobs (env):
  `BROLL_ENABLED`, `BROLL_LICENSE_TYPE` (`commercial` default), `BROLL_MIN_SCORE`
  (relevance gate, 0.65), `BROLL_ALLOW_NONCOMMERCIAL`. A scene with no confident
  match falls back to its archetype canvas. *Note:* Wikimedia Commons blocks
  automated access, so named historical figures with no CC photo elsewhere will
  usually fall back to the canvas — for guaranteed portraits you'd add a licensed
  source or AI image generation.
- **Music** prefers drop-in tracks in `assets/music/<mood>/`, falls back to a
  fresh procedural bed with a distinct per-mood profile + motif (see
  `assets/music/README.md`).
- The in-process job registry in `pipeline.py` fits a single-worker uvicorn; a
  multi-worker deploy would swap it for Redis.
