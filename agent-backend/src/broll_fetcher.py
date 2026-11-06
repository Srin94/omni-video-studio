"""Topic-matched B-roll imagery — the thing that turns slides into a *video*.

For every scene the model gives a concrete, image-searchable subject
(`scene.broll_query`, e.g. "a single biological neuron", "the Rosetta Stone").
We resolve each one to a real, freely-licensed photo/diagram and download it into
the Remotion engine's public assets, where the renderer floats it behind the
scene with a slow Ken-Burns move.

Source: **Openverse** (https://api.openverse.org) — no API key, aggregates
Wikimedia Commons + Flickr CC + museums, and (unlike the Commons API, which
403s automated clients) it serves us reliably. We default to
commercially-usable licences (BY / CC0 / PDM) so the output is safe for a real
channel, and we ALWAYS capture attribution (creator + licence), which Creative
Commons requires — it is rendered small on-screen and appended to the YouTube
description.

Everything degrades gracefully: a scene with no usable image simply renders on
its archetype canvas as before, so B-roll can never fail a render.
"""

from __future__ import annotations

import io
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import httpx

try:
    from . import config
    from .schema import OmniRenderPayload, SceneSpec
except ImportError:  # pragma: no cover
    import config  # type: ignore
    from schema import OmniRenderPayload, SceneSpec  # type: ignore


OPENVERSE_IMAGES = "https://api.openverse.org/v1/images/"
_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)
# A short, polite client string for the JSON API (no personal data).
_API_UA = "omni-video-studio/1.0 (educational video tooling)"


_STOPWORDS = {
    "the", "a", "an", "of", "and", "in", "on", "to", "for", "with", "at", "by",
    "diagram", "illustration", "photo", "photograph", "image", "picture", "view",
    "closeup", "close", "up",
}


def _terms(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2 and w not in _STOPWORDS]


@dataclass
class BrollHit:
    url: str
    thumbnail: str
    creator: str
    license: str
    license_version: str
    source_page: str
    width: int
    height: int
    title: str = ""
    tags: str = ""
    source: str = ""

    def relevance(self, query: str) -> float:
        """How much of the query's *specific* meaning this hit matches. Terms are
        weighted by length so a rare/long word ("rosenblatt", "perceptron")
        counts far more than a common short one ("frank"), which stops a stray
        match on a generic word from passing the gate."""
        terms = _terms(query)
        if not terms:
            return 0.0
        hay = f"{self.title} {self.tags}".lower()
        den = sum(len(t) for t in terms)
        num = sum(len(t) for t in terms if t in hay)
        return num / den if den else 0.0

    def attribution(self) -> str:
        who = (self.creator or "Unknown").strip()
        lic = self.license.upper()
        ver = f" {self.license_version}" if self.license_version else ""
        if lic in ("CC0", "PDM"):
            return f"{who} · Public Domain"
        return f"{who} · CC {lic}{ver}"


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
def _search(client: httpx.Client, query: str, portrait: bool, license_type: str) -> List[BrollHit]:
    params = {
        "q": query,
        "page_size": str(config.BROLL_SEARCH_LIMIT),
        "license_type": license_type,
        "mature": "false",
        "aspect_ratio": "tall" if portrait else "wide",
    }
    try:
        r = client.get(OPENVERSE_IMAGES, params=params, timeout=config.BROLL_TIMEOUT)
        r.raise_for_status()
        results = r.json().get("results", []) or []
    except Exception as exc:  # noqa: BLE001
        print(f"[broll] search failed for {query!r} ({exc}).")
        return []

    hits: List[BrollHit] = []
    for h in results:
        url = h.get("url") or ""
        if not url:
            continue
        tags = " ".join(t.get("name", "") for t in (h.get("tags") or []) if isinstance(t, dict))
        hits.append(
            BrollHit(
                url=url,
                thumbnail=h.get("thumbnail") or "",
                creator=h.get("creator") or "",
                license=h.get("license") or "",
                license_version=h.get("license_version") or "",
                source_page=h.get("foreign_landing_url") or h.get("source") or "",
                width=int(h.get("width") or 0),
                height=int(h.get("height") or 0),
                title=h.get("title") or "",
                tags=tags,
                source=h.get("source") or "",
            )
        )
    return hits


# ---------------------------------------------------------------------------
# Download + normalise
# ---------------------------------------------------------------------------
def _download_image(client: httpx.Client, url: str) -> Optional["ImageType"]:  # noqa: F821
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        print("[broll] Pillow not installed; skipping B-roll (pip install pillow).")
        return None
    try:
        r = client.get(url, headers={"User-Agent": _BROWSER_UA},
                       timeout=config.BROLL_TIMEOUT, follow_redirects=True)
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content))
        im.load()  # force decode (first frame for GIFs)
        return im
    except Exception:  # noqa: BLE001
        return None


def _save_cover(im, dest: Path, target_w: int, target_h: int) -> bool:
    """Center-crop to the target aspect and save a clean JPEG a bit larger than
    the frame so the renderer's Ken-Burns zoom never shows an edge."""
    try:
        from PIL import Image, ImageOps  # type: ignore
    except ImportError:
        return False
    try:
        im = ImageOps.exif_transpose(im).convert("RGB")
        # Oversize so a 1.12x zoom stays inside the image.
        tw, th = int(target_w * 1.15), int(target_h * 1.15)
        fitted = ImageOps.fit(im, (tw, th), method=Image.LANCZOS, centering=(0.5, 0.42))
        dest.parent.mkdir(parents=True, exist_ok=True)
        fitted.save(dest, "JPEG", quality=88, optimize=True)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[broll] save failed ({exc}).")
        return False


def _attempts(query: str) -> List[Tuple[str, str]]:
    """A cascade of (query, license_type) tries, widening only as needed so the
    first, commercial-safe result wins when there is one."""
    base = config.BROLL_LICENSE_TYPE
    out: List[Tuple[str, str]] = [(query, base)]
    if config.BROLL_ALLOW_NONCOMMERCIAL and base != "all":
        out.append((query, "all"))
    simple = " ".join(query.split()[:2]).strip()
    if simple and simple.lower() != query.lower():
        out.append((simple, "all" if config.BROLL_ALLOW_NONCOMMERCIAL else base))
    return out


def _resolve_scene(
    client: httpx.Client, scene: SceneSpec, query: str, portrait: bool,
    target_w: int, target_h: int, out_dir: Path, rel_prefix: str,
) -> None:
    for q, lic in _attempts(query):
        hits = _search(client, q, portrait, lic)
        # Score every hit against the ORIGINAL subject (not the widened query) so
        # a simplified search can't drag in something off-topic, then try the
        # most relevant first.
        scored = sorted(
            ((h.relevance(query), h) for h in hits),
            key=lambda sh: sh[0], reverse=True,
        )
        for score, hit in scored:
            if score < config.BROLL_MIN_SCORE:
                break  # the rest are only less relevant
            if hit.width and hit.height and hit.width < config.BROLL_MIN_DIM and hit.height < config.BROLL_MIN_DIM:
                continue
            im = _download_image(client, hit.url)
            if im is None and hit.thumbnail:
                im = _download_image(client, hit.thumbnail)  # Openverse-proxied fallback
            if im is None:
                continue
            rel = f"{rel_prefix}/scene_{scene.scene_id:02d}.jpg"
            dest = out_dir / f"scene_{scene.scene_id:02d}.jpg"
            if _save_cover(im, dest, target_w, target_h):
                scene.broll_asset = rel
                scene.broll_attribution = hit.attribution()
                scene.broll_source_url = hit.source_page
                print(f"[broll] scene {scene.scene_id:02d}: {q!r} [{lic}] score={score:.2f} -> {hit.attribution()}")
                return
    print(f"[broll] scene {scene.scene_id:02d}: no relevant image for {query!r} (archetype canvas instead).")


def _query_for(scene: SceneSpec, topic: str) -> str:
    q = (scene.broll_query or "").strip()
    if q:
        return q
    # Fallbacks when the model didn't supply one: callout keywords, else the
    # chapter title, always anchored to the topic so results stay on-subject.
    if scene.callout_keywords:
        return f"{' '.join(scene.callout_keywords[:3])} {topic}".strip()
    return f"{scene.chapter_title} {topic}".strip()


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------
def fetch_broll(payload: OmniRenderPayload, topic: str = "") -> int:
    """Resolve + download a B-roll image for every scene. Returns the count."""
    if not config.BROLL_ENABLED:
        return 0
    portrait = payload.video_format == "portrait"
    target_w, target_h = config.video_dimensions(payload.video_format)
    out_dir = config.VIDEO_ASSETS_DIR / "broll"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Clear stale images from a previous render so nothing bleeds across videos.
    for old in out_dir.glob("scene_*.jpg"):
        old.unlink(missing_ok=True)

    topic = topic or payload.youtube_title
    headers = {"User-Agent": _API_UA, "Accept": "application/json"}
    # Scenes that carry an animated illustration use it as their main visual, so
    # they don't need (and won't show) a fetched photo — skip them.
    broll_scenes = [s for s in payload.scenes if s.illustration is None]
    with httpx.Client(headers=headers, follow_redirects=True) as client:
        with ThreadPoolExecutor(max_workers=config.BROLL_WORKERS) as pool:
            futs = [
                pool.submit(
                    _resolve_scene, client, scene, _query_for(scene, topic),
                    portrait, target_w, target_h, out_dir, "assets/broll",
                )
                for scene in broll_scenes
            ]
            for f in as_completed(futs):
                f.result()

    got = sum(1 for s in payload.scenes if s.broll_asset)
    print(f"[broll] resolved {got}/{len(payload.scenes)} scenes.")
    return got


def attribution_block(payload: OmniRenderPayload) -> str:
    """A credits block for the YouTube description (CC attribution)."""
    lines = []
    seen = set()
    for s in payload.scenes:
        if s.broll_attribution and s.broll_attribution not in seen:
            seen.add(s.broll_attribution)
            src = f" ({s.broll_source_url})" if s.broll_source_url else ""
            lines.append(f"• {s.broll_attribution}{src}")
    if not lines:
        return ""
    return "Imagery via Openverse (Creative Commons):\n" + "\n".join(lines)
