"""High-CTR 1280x720 thumbnail renderer (Playwright headless Chromium) — spec 1/5.

Renders a bold headline + genre badge card. Colors are keyed off the video's
genre so a thumbnail reads like its archetype (dark neon for tech/science, warm
paper for history, kinetic high-contrast for money/paradox, charcoal for crime).
"""

from __future__ import annotations

from typing import Dict

try:
    from . import config
    from .schema import OmniRenderPayload
except ImportError:  # pragma: no cover
    import config  # type: ignore
    from schema import OmniRenderPayload  # type: ignore


_GENRE_LABEL = {
    "SCIENCE_PHYSICS": "Science & Physics",
    "MONEY_BUSINESS": "Business & Money",
    "CRIME_MYSTERY": "True Crime & Mystery",
    "EVERYDAY_TECH": "Everyday Tech",
    "HISTORY_CULTURE": "History & Culture",
    "PARADOX_LOGIC": "Game Theory & Paradoxes",
}

# Palettes mirror video-engine/src/styles/archetypes.ts.
_DARK = {
    "canvas_bg": "#080C14", "canvas_bg2": "#0C1424", "grid": "#17304A",
    "text_primary": "#E8F1FB", "text_muted": "#6B8099", "accent": "#38BDF8",
    "accent_2": "#34D399", "on_accent": "#06121F",
    "text_shadow": "0 6px 30px rgba(0,0,0,0.6)",
}
_PAPER = {
    "canvas_bg": "#F3EFE4", "canvas_bg2": "#E7E0CE", "grid": "#D8CFBB",
    "text_primary": "#201B12", "text_muted": "#6E6450", "accent": "#C2410C",
    "accent_2": "#0369A1", "on_accent": "#FBF6EC",
    "text_shadow": "2px 3px 0 rgba(32,27,18,0.14)",
}
_KINETIC = {
    "canvas_bg": "#0A0A0A", "canvas_bg2": "#141414", "grid": "#262626",
    "text_primary": "#FAFAFA", "text_muted": "#8A8A8A", "accent": "#FACC15",
    "accent_2": "#F472B6", "on_accent": "#111111",
    "text_shadow": "0 6px 30px rgba(0,0,0,0.7)",
}
_CHARCOAL = {
    "canvas_bg": "#12131A", "canvas_bg2": "#1A1C26", "grid": "#2A2D3A",
    "text_primary": "#ECEAF2", "text_muted": "#7B7E90", "accent": "#F43F5E",
    "accent_2": "#A78BFA", "on_accent": "#140A0D",
    "text_shadow": "0 6px 30px rgba(0,0,0,0.6)",
}

_GENRE_THEME: Dict[str, Dict[str, str]] = {
    "SCIENCE_PHYSICS": _DARK,
    "EVERYDAY_TECH": _DARK,
    "HISTORY_CULTURE": _PAPER,
    "MONEY_BUSINESS": _KINETIC,
    "PARADOX_LOGIC": _KINETIC,
    "CRIME_MYSTERY": _CHARCOAL,
}


def _headline_html(text: str) -> str:
    words = text.strip().split()
    if not words:
        return ""
    if len(words) > 1:
        head = " ".join(words[:-1])
        return f'{head} <span class="hl">{words[-1]}</span>'
    return f'<span class="hl">{text}</span>'


def _fill_template(payload: OmniRenderPayload) -> str:
    theme = _GENRE_THEME.get(payload.genre, _DARK)
    with open(config.THUMBNAIL_TEMPLATE_PATH, encoding="utf-8") as fh:
        html = fh.read()

    replacements = {
        "__CANVAS_BG__": theme["canvas_bg"],
        "__CANVAS_BG2__": theme["canvas_bg2"],
        "__GRID__": theme["grid"],
        "__TEXT_PRIMARY__": theme["text_primary"],
        "__TEXT_MUTED__": theme["text_muted"],
        "__ACCENT__": theme["accent"],
        "__ACCENT_2__": theme["accent_2"],
        "__ON_ACCENT__": theme["on_accent"],
        "__TEXT_SHADOW__": theme["text_shadow"],
        "__CHANNEL_NAME__": config.CHANNEL_NAME.upper(),
        "__BADGE_TEXT__": payload.thumbnail_sub_badge.upper(),
        "__HEADLINE_HTML__": _headline_html(payload.thumbnail_headline),
        "__GENRE_LABEL__": _GENRE_LABEL.get(payload.genre, payload.genre),
    }
    for token, value in replacements.items():
        html = html.replace(token, value)
    return html


def render_thumbnail(payload: OmniRenderPayload) -> str:
    """Render the thumbnail PNG; return its path. Requires Playwright chromium."""
    html = _fill_template(payload)
    filled_path = config.OUTPUT_DIR / "thumbnail_filled.html"
    filled_path.write_text(html, encoding="utf-8")

    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "playwright not installed. `pip install playwright && playwright install chromium`."
        ) from exc

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(
            viewport={"width": config.THUMBNAIL_WIDTH, "height": config.THUMBNAIL_HEIGHT},
            device_scale_factor=1,
        )
        page.goto(filled_path.as_uri())
        page.wait_for_timeout(400)
        page.screenshot(
            path=str(config.THUMBNAIL_PATH),
            clip={"x": 0, "y": 0, "width": config.THUMBNAIL_WIDTH, "height": config.THUMBNAIL_HEIGHT},
        )
        browser.close()

    print(f"[thumbnail] Rendered -> {config.THUMBNAIL_PATH}")
    return str(config.THUMBNAIL_PATH)


if __name__ == "__main__":
    import json

    with open(config.RENDER_PAYLOAD_PATH, encoding="utf-8") as fh:
        p = OmniRenderPayload.model_validate(json.load(fh))
    render_thumbnail(p)
