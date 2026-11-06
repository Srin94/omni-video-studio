"""Live Idea Radar — zero-cost trending-topic aggregator (spec View 1).

Scrapes, with NO API keys:
  * Google Trends Daily RSS (one feed per configured geo)
  * Reddit "top of day" JSON for a few high-signal subreddits

Each raw item becomes a `TrendCard` with a heuristic **Hook Score** (0-100) that
rewards curiosity-gap phrasing, concrete numbers and raw popularity, plus a
best-guess genre so the UI can filter by pill. Results are cached in-process for
`TRENDS_CACHE_SECONDS` so repeated dashboard loads don't re-scrape.

Everything degrades gracefully: a dead feed is skipped, never fatal.
"""

from __future__ import annotations

import html
import re
import time
from dataclasses import dataclass, asdict, field
from typing import List, Optional

import httpx

try:
    from . import config
except ImportError:  # pragma: no cover
    import config  # type: ignore


@dataclass
class TrendCard:
    title: str
    source: str            # "Google Trends · IN", "Reddit · r/todayilearned"
    url: str
    genre: str             # best-guess Genre enum value
    hook_score: int        # 0-100
    blurb: str = ""
    traffic: str = ""      # e.g. "50K+ searches" when the feed provides it

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Genre guessing (keyword buckets -> Genre enum value)
# ---------------------------------------------------------------------------
_GENRE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "SCIENCE_PHYSICS": (
        "physics", "quantum", "space", "nasa", "star", "galaxy", "energy",
        "chemistry", "biology", "dna", "brain", "science", "particle", "gravity",
        "light", "neutrino", "fusion", "telescope", "climate",
    ),
    "MONEY_BUSINESS": (
        "stock", "market", "economy", "inflation", "bank", "startup", "ipo",
        "crypto", "bitcoin", "money", "price", "tax", "trade", "ceo", "billion",
        "company", "business", "fund", "invest", "profit",
    ),
    "CRIME_MYSTERY": (
        "murder", "crime", "killer", "police", "fbi", "heist", "fraud", "theft",
        "missing", "cold case", "forensic", "trial", "verdict", "scam", "arrest",
        "mystery", "disappear",
    ),
    "EVERYDAY_TECH": (
        "iphone", "android", "app", "ai", "chatgpt", "google", "wifi", "chip",
        "battery", "usb", "software", "gadget", "device", "how does", "works",
        "internet", "5g", "robot", "code",
    ),
    "HISTORY_CULTURE": (
        "history", "ancient", "empire", "war", "king", "queen", "dynasty",
        "artifact", "museum", "century", "medieval", "roman", "egypt", "culture",
        "tradition", "archaeolog", "ruins", "1944", "revolution",
    ),
    "PARADOX_LOGIC": (
        "paradox", "puzzle", "logic", "probability", "game theory", "riddle",
        "illusion", "math", "infinity", "statistic", "fallacy", "dilemma",
        "counterintuitive", "theorem",
    ),
}


def guess_genre(text: str) -> str:
    low = text.lower()
    best = "EVERYDAY_TECH"
    best_hits = 0
    for genre, words in _GENRE_KEYWORDS.items():
        hits = sum(1 for w in words if w in low)
        if hits > best_hits:
            best, best_hits = genre, hits
    return best


# ---------------------------------------------------------------------------
# Hook Score heuristic (0-100)
# ---------------------------------------------------------------------------
_CURIOSITY_MARKERS = (
    "why", "how", "secret", "hidden", "surprising", "actually", "really",
    "truth", "never", "finally", "shocking", "weird", "strange", "nobody",
    "everyone", "mistake", "wrong", "myth", "?", "vs", "more than", "less than",
)


def hook_score(title: str, popularity: float, blurb: str = "") -> int:
    text = f"{title} {blurb}".lower()
    score = 42.0
    # Curiosity-gap phrasing.
    score += 6.0 * sum(1 for m in _CURIOSITY_MARKERS if m in text)
    # Concrete numbers read as "this has a payload".
    if re.search(r"\d", title):
        score += 8.0
    # A punchy, tweetable length wins over a wall of words.
    n = len(title.split())
    if 4 <= n <= 11:
        score += 10.0
    elif n > 16:
        score -= 8.0
    # Raw popularity (already normalised to ~0..1 by the caller).
    score += 24.0 * max(0.0, min(1.0, popularity))
    return int(max(1, min(100, round(score))))


# ---------------------------------------------------------------------------
# Google Trends daily RSS
# ---------------------------------------------------------------------------
_TRAFFIC_RE = re.compile(r"([\d,]+)\+?")


def _parse_traffic(raw: str) -> float:
    """Map a '50,000+' approx-traffic string to a 0..1 popularity scalar."""
    if not raw:
        return 0.4
    m = _TRAFFIC_RE.search(raw.replace(",", ""))
    if not m:
        return 0.4
    try:
        n = int(m.group(1))
    except ValueError:
        return 0.4
    # 2M+ searches -> ~1.0 on a log scale.
    import math

    return max(0.0, min(1.0, math.log10(max(n, 10)) / math.log10(2_000_000)))


def _fetch_google_trends(client: httpx.Client, geo: str) -> List[TrendCard]:
    import feedparser  # lazy: keeps import cost off the hot path

    url = config.GOOGLE_TRENDS_RSS.format(geo=geo)
    try:
        resp = client.get(url, headers={"User-Agent": config.USER_AGENT})
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"[trends] Google Trends {geo} failed: {exc}")
        return []

    feed = feedparser.parse(resp.text)
    cards: List[TrendCard] = []
    for entry in feed.entries[:20]:
        title = html.unescape((entry.get("title") or "").strip())
        if not title:
            continue
        traffic = str(entry.get("ht_approx_traffic", "") or entry.get("approx_traffic", ""))
        # News snippet, if the feed carries one.
        blurb = ""
        news = entry.get("ht_news_item_title") or entry.get("summary") or ""
        if news:
            blurb = re.sub(r"<[^>]+>", "", html.unescape(str(news)))[:160]
        pop = _parse_traffic(traffic)
        cards.append(
            TrendCard(
                title=title,
                source=f"Google Trends · {geo}",
                url=entry.get("link") or f"https://www.google.com/search?q={title}",
                genre=guess_genre(f"{title} {blurb}"),
                hook_score=hook_score(title, pop, blurb),
                blurb=blurb,
                traffic=f"{traffic} searches" if traffic else "",
            )
        )
    return cards


# ---------------------------------------------------------------------------
# Reddit top-of-day JSON
# ---------------------------------------------------------------------------
def _fetch_reddit(client: httpx.Client, sub: str, limit: int = 8) -> List[TrendCard]:
    url = config.REDDIT_TOP_JSON.format(sub=sub, limit=limit)
    try:
        resp = client.get(url, headers={"User-Agent": config.USER_AGENT})
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        print(f"[trends] Reddit r/{sub} failed: {exc}")
        return []

    children = (data.get("data") or {}).get("children") or []
    # Normalise score within this sub so one viral post doesn't swamp the rest.
    scores = [max(1, (c.get("data") or {}).get("score", 1)) for c in children] or [1]
    top = max(scores)

    cards: List[TrendCard] = []
    for child in children:
        d = child.get("data") or {}
        title = html.unescape((d.get("title") or "").strip())
        if not title or d.get("stickied"):
            continue
        # Strip the "TIL that ..." lead-in for a cleaner topic.
        clean = re.sub(r"^(TIL|ELI5)[:\s-]*", "", title, flags=re.IGNORECASE).strip()
        pop = max(1, d.get("score", 1)) / top
        permalink = d.get("permalink") or ""
        cards.append(
            TrendCard(
                title=clean[:140],
                source=f"Reddit · r/{sub}",
                url=f"https://www.reddit.com{permalink}" if permalink else (d.get("url") or ""),
                genre=guess_genre(clean),
                hook_score=hook_score(clean, pop),
                blurb=f"{d.get('score', 0):,} upvotes · {d.get('num_comments', 0):,} comments",
                traffic=f"{d.get('score', 0):,} upvotes",
            )
        )
    return cards


# ---------------------------------------------------------------------------
# Aggregation + cache
# ---------------------------------------------------------------------------
_CACHE: dict[str, object] = {"at": 0.0, "cards": []}


def _aggregate() -> List[TrendCard]:
    cards: List[TrendCard] = []
    with httpx.Client(timeout=config.HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
        for geo in config.GOOGLE_TRENDS_GEOS:
            cards.extend(_fetch_google_trends(client, geo))
        for sub in config.REDDIT_SUBS:
            cards.extend(_fetch_reddit(client, sub))

    # De-dupe by lowercased title, keep the higher hook score.
    best: dict[str, TrendCard] = {}
    for c in cards:
        key = c.title.lower()
        if key not in best or c.hook_score > best[key].hook_score:
            best[key] = c
    out = sorted(best.values(), key=lambda c: c.hook_score, reverse=True)
    return out


def get_trends(force: bool = False, genre: Optional[str] = None) -> List[dict]:
    """Return ranked trend cards (optionally filtered to one genre)."""
    now = time.time()
    cached: List[TrendCard] = _CACHE["cards"]  # type: ignore[assignment]
    if force or not cached or (now - float(_CACHE["at"])) > config.TRENDS_CACHE_SECONDS:
        try:
            cached = _aggregate()
            _CACHE["cards"] = cached
            _CACHE["at"] = now
        except Exception as exc:  # noqa: BLE001
            print(f"[trends] aggregate failed ({exc}); serving stale cache.")
            cached = _CACHE["cards"]  # type: ignore[assignment]

    items = cached
    if genre and genre.upper() != "ALL":
        items = [c for c in items if c.genre == genre.upper()]
    return [c.to_dict() for c in items]


if __name__ == "__main__":
    for card in get_trends(force=True)[:15]:
        print(f"[{card['hook_score']:3d}] {card['genre']:16s} {card['title']}  <-- {card['source']}")
