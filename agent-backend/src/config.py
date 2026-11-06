"""Central configuration: env variables, paths and pipeline constants.

Everything that tunes the pipeline lives here so the individual modules stay
declarative. Environment variables are loaded once via python-dotenv.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# agent-backend/src/config.py -> agent-backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent

DATA_DIR = BACKEND_DIR / "data"
OUTPUT_DIR = BACKEND_DIR / "output"
TEMPLATES_DIR = BACKEND_DIR / "templates"

VIDEO_ENGINE_DIR = REPO_ROOT / "video-engine"
VIDEO_ASSETS_DIR = VIDEO_ENGINE_DIR / "public" / "assets"

RENDER_PAYLOAD_PATH = OUTPUT_DIR / "render_payload.json"
NARRATION_PATH = OUTPUT_DIR / "narration.wav"
THUMBNAIL_PATH = OUTPUT_DIR / "thumbnail.png"
FINAL_VIDEO_PATH = OUTPUT_DIR / "final_video.mp4"
THUMBNAIL_TEMPLATE_PATH = TEMPLATES_DIR / "thumbnail_template.html"

for _d in (DATA_DIR, OUTPUT_DIR, VIDEO_ASSETS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

load_dotenv(REPO_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")

# ---------------------------------------------------------------------------
# Secrets / credentials
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

APPROVAL_WINDOW_MINUTES = int(os.getenv("APPROVAL_WINDOW_MINUTES", "120") or "120")
# Fail-closed by default: no explicit "Approve" within the window => do NOT publish.
APPROVE_ON_TIMEOUT = os.getenv("APPROVE_ON_TIMEOUT", "false").lower() in ("1", "true", "yes")

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "").strip()
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "").strip()
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip()

DRY_RUN_SKIP_UPLOAD = os.getenv("DRY_RUN_SKIP_UPLOAD", "false").lower() in ("1", "true", "yes")

# On-screen channel brand (wordmark + outro CTA + thumbnail).
CHANNEL_NAME = os.getenv("CHANNEL_NAME", "Omni Studio")

# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
# A browser-like UA so Wikipedia / Jina / Reddit / Trends don't 429 us.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36 omni-video-studio/1.0"
)
HTTP_TIMEOUT_SECONDS = 20

# ---------------------------------------------------------------------------
# Trend radar (zero-cost, no API keys) — View 1
# ---------------------------------------------------------------------------
GOOGLE_TRENDS_RSS = "https://trends.google.com/trending/rss?geo={geo}"
GOOGLE_TRENDS_GEOS = [g.strip() for g in os.getenv("TRENDS_GEOS", "IN,US").split(",") if g.strip()]
REDDIT_SUBS = [
    "todayilearned",
    "explainlikeimfive",
    "damnthatsinteresting",
]
REDDIT_TOP_JSON = "https://www.reddit.com/r/{sub}/top.json?t=day&limit={limit}"
TRENDS_CACHE_SECONDS = int(os.getenv("TRENDS_CACHE_SECONDS", "900"))

# ---------------------------------------------------------------------------
# Reference gathering (Jina Reader over DuckDuckGo / Wikipedia) — View 2
# ---------------------------------------------------------------------------
JINA_READER_PREFIX = "https://r.jina.ai/"
JINA_TIMEOUT_SECONDS = 25
DUCKDUCKGO_HTML = "https://html.duckduckgo.com/html/?q={query}"
WIKIPEDIA_SEARCH = (
    "https://en.wikipedia.org/w/api.php?action=opensearch&format=json&limit=1&search={query}"
)
MIN_REFERENCE_CHARS = 400
MAX_REFERENCE_CHARS = 16_000

# ---------------------------------------------------------------------------
# Audio / TTS — genre-matched voice personas (spec 4.1)
# ---------------------------------------------------------------------------
# edge-tts persona per genre (primary cloud-free voice). Kokoro voices used when
# the local ONNX model is present.
GENRE_EDGE_VOICE: dict[str, str] = {
    "SCIENCE_PHYSICS": "en-US-ChristopherNeural",   # deep, measured, thoughtful
    "PARADOX_LOGIC": "en-US-ChristopherNeural",
    "CRIME_MYSTERY": "en-US-EricNeural",            # gripping, lower-pitch
    "HISTORY_CULTURE": "en-US-EricNeural",
    "EVERYDAY_TECH": "en-US-BrianNeural",           # energetic, crisp
    "MONEY_BUSINESS": "en-US-BrianNeural",
}
GENRE_KOKORO_VOICE: dict[str, str] = {
    "SCIENCE_PHYSICS": "am_adam",
    "PARADOX_LOGIC": "am_adam",
    "CRIME_MYSTERY": "am_michael",
    "HISTORY_CULTURE": "am_michael",
    "EVERYDAY_TECH": "af_bella",
    "MONEY_BUSINESS": "af_bella",
}
DEFAULT_EDGE_VOICE = "en-US-ChristopherNeural"
EDGE_TTS_FALLBACK_VOICES = ["en-US-GuyNeural", "en-US-AndrewNeural"]
# Pacing: the old default (-2%) sounded rushed. Slow the delivery and drop the
# pitch a touch for a calmer, more authoritative read. Per-genre pitch below.
EDGE_TTS_RATE = os.getenv("EDGE_TTS_RATE", "-8%")
EDGE_TTS_VOLUME = os.getenv("EDGE_TTS_VOLUME", "+0%")
EDGE_TTS_PITCH = os.getenv("EDGE_TTS_PITCH", "-3Hz")
# Slight per-genre pitch shaping (Hz), layered on top of EDGE_TTS_PITCH's feel.
GENRE_EDGE_PITCH: dict[str, str] = {
    "SCIENCE_PHYSICS": "-2Hz",
    "PARADOX_LOGIC": "-2Hz",
    "CRIME_MYSTERY": "-6Hz",    # lower, graver
    "HISTORY_CULTURE": "-5Hz",
    "EVERYDAY_TECH": "+0Hz",    # brighter, energetic
    "MONEY_BUSINESS": "-2Hz",
}
KOKORO_SPEED = float(os.getenv("KOKORO_SPEED", "0.95"))

# Gap of real silence inserted BETWEEN scenes (does not affect intra-scene word
# timing, which now comes verbatim from the TTS engine's word boundaries).
SCENE_GAP_MS = 420
# Extra breath held after a scene that ends a sentence hard ('.', '!', '?').
SENTENCE_TAIL_MS = 180

AUDIO_SAMPLE_RATE = 24_000
WHISPER_MODEL = "base.en"
WHISPER_COMPUTE_TYPE = "int8"

# ---------------------------------------------------------------------------
# Background music (mood-tagged catalog + procedural fallback) — spec 4.3
# ---------------------------------------------------------------------------
BACKGROUND_MUSIC_ENABLED = os.getenv("BACKGROUND_MUSIC_ENABLED", "true").lower() in ("1", "true", "yes")
MUSIC_DIR = BACKEND_DIR / "assets" / "music"
# Ducked well under narration; narration sits near -16..-20 dBFS.
MUSIC_LEVEL_DBFS = float(os.getenv("MUSIC_LEVEL_DBFS", "-28"))
MUSIC_FADE_MS = int(os.getenv("MUSIC_FADE_MS", "2500"))
# Mood -> subfolder inside assets/music/ (spec 4.3).
MOOD_FOLDERS: dict[str, str] = {
    "dark_ambient_synth": "dark_ambient_synth",
    "cinematic_investigative": "cinematic_investigative",
    "upbeat_curious_tech": "upbeat_curious_tech",
    "acoustic_thoughtful": "acoustic_thoughtful",
    "minimal_tension": "cinematic_investigative",
}

# ---------------------------------------------------------------------------
# B-roll imagery (Openverse — topic-matched, freely licensed) — the thing that
# turns slides into a video. No API key required.
# ---------------------------------------------------------------------------
BROLL_ENABLED = os.getenv("BROLL_ENABLED", "true").lower() in ("1", "true", "yes")
# "commercial" (BY / CC0 / PDM) is safe for a monetised channel; "all" widens
# the pool but may include non-commercial images — always attributed either way.
BROLL_LICENSE_TYPE = os.getenv("BROLL_LICENSE_TYPE", "commercial")
# If a scene finds no commercial-safe image, allow a last-resort pass over ALL
# Creative-Commons licences (still fully attributed on-screen + in the
# description). Set to "false" for a strictly monetisation-safe pool.
BROLL_ALLOW_NONCOMMERCIAL = os.getenv("BROLL_ALLOW_NONCOMMERCIAL", "true").lower() in ("1", "true", "yes")
BROLL_SEARCH_LIMIT = int(os.getenv("BROLL_SEARCH_LIMIT", "12"))
# Reject images that don't actually match the subject: a hit must share at least
# this fraction of the query's meaningful words with its title/tags. Prevents the
# "it said neuron but showed a tree" failure — a wrong image is worse than none
# (the scene just falls back to its archetype canvas).
BROLL_MIN_SCORE = float(os.getenv("BROLL_MIN_SCORE", "0.65"))
BROLL_MIN_DIM = int(os.getenv("BROLL_MIN_DIM", "500"))
BROLL_WORKERS = int(os.getenv("BROLL_WORKERS", "6"))
BROLL_TIMEOUT = int(os.getenv("BROLL_TIMEOUT", "25"))

# ---------------------------------------------------------------------------
# Thumbnail (Playwright 1280x720) — spec 1 / 5
# ---------------------------------------------------------------------------
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720

# ---------------------------------------------------------------------------
# Video — format-selectable (landscape 1920x1080 / portrait 1080x1920), 60fps
# ---------------------------------------------------------------------------
VIDEO_FPS = 60
VIDEO_DIMENSIONS: dict[str, tuple[int, int]] = {
    "landscape": (1920, 1080),
    "portrait": (1080, 1920),
}
REMOTION_COMPOSITION_ID = "OmniMasterVideo"

# ---------------------------------------------------------------------------
# YouTube
# ---------------------------------------------------------------------------
YOUTUBE_CATEGORY_ID = "27"  # Education
YOUTUBE_UPLOAD_SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]


def has_telegram() -> bool:
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


def has_youtube_credentials() -> bool:
    return bool(YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET and YOUTUBE_REFRESH_TOKEN)


def video_dimensions(video_format: str) -> tuple[int, int]:
    return VIDEO_DIMENSIONS.get(video_format, VIDEO_DIMENSIONS["landscape"])
