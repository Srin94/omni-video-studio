"""Grounding Scout — fetch factual Markdown for a topic (spec View 2).

Given a topic string, assemble clean factual grounding so the web-LLM is anchored
in real numbers, dates, mechanics and names (not hallucination).

Strategy, best-effort and in order:
  1. Wikipedia: resolve the topic via the opensearch API, then Jina-read the
     resolved article (`https://r.jina.ai/https://en.wikipedia.org/wiki/...`).
  2. DuckDuckGo HTML results Jina-read into Markdown for broader coverage.
  3. Direct BeautifulSoup fallback if Jina is unavailable.

Output is truncated to the browser-LLM's comfortable context budget and returned
with the list of sources actually used (surfaced in the UI).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
from urllib.parse import quote_plus, urlparse

import httpx
from bs4 import BeautifulSoup

try:
    from . import config
except ImportError:  # pragma: no cover
    import config  # type: ignore


@dataclass
class Reference:
    markdown: str
    sources: List[str] = field(default_factory=list)
    method: str = "empty"  # "jina-wiki" | "jina-ddg" | "soup" | "empty"

    @property
    def ok(self) -> bool:
        return len(self.markdown) >= config.MIN_REFERENCE_CHARS


def _truncate(text: str) -> str:
    text = text.strip()
    if len(text) <= config.MAX_REFERENCE_CHARS:
        return text
    cut = text.rfind("\n", 0, config.MAX_REFERENCE_CHARS)
    if cut < config.MAX_REFERENCE_CHARS * 0.6:
        cut = config.MAX_REFERENCE_CHARS
    return text[:cut].strip() + "\n\n...[truncated]"


def _fetch_jina(client: httpx.Client, url: str) -> str:
    jina_url = config.JINA_READER_PREFIX + url
    resp = client.get(
        jina_url,
        headers={"X-Return-Format": "markdown", "User-Agent": config.USER_AGENT},
        timeout=config.JINA_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return resp.text or ""


def _fetch_soup(client: httpx.Client, url: str) -> str:
    resp = client.get(url, headers={"User-Agent": config.USER_AGENT})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    parts: List[str] = []
    title = soup.find("h1") or soup.find("title")
    if title:
        parts.append(f"# {title.get_text(strip=True)}")
    root = soup.find("article") or soup.find("main") or soup.body or soup
    for el in root.find_all(["h2", "h3", "p", "li"]):
        if el.name in ("h2", "h3"):
            parts.append(f"\n## {el.get_text(strip=True)}")
        elif el.name == "li":
            text = el.get_text(" ", strip=True)
            if text:
                parts.append(f"- {text}")
        else:
            text = el.get_text(" ", strip=True)
            if len(text) > 30:
                parts.append(text)
    return "\n\n".join(parts)


def _resolve_wikipedia(client: httpx.Client, topic: str) -> str | None:
    url = config.WIKIPEDIA_SEARCH.format(query=quote_plus(topic))
    try:
        resp = client.get(url, headers={"User-Agent": config.USER_AGENT})
        resp.raise_for_status()
        data = resp.json()
        links = data[3] if len(data) > 3 else []
        return links[0] if links else None
    except Exception as exc:  # noqa: BLE001
        print(f"[reference] Wikipedia resolve failed: {exc}")
        return None


def _duckduckgo_links(client: httpx.Client, topic: str, limit: int = 3) -> List[str]:
    url = config.DUCKDUCKGO_HTML.format(query=quote_plus(topic))
    try:
        resp = client.post(url, headers={"User-Agent": config.USER_AGENT})
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"[reference] DuckDuckGo failed: {exc}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    links: List[str] = []
    for a in soup.select("a.result__a"):
        href = a.get("href") or ""
        if href.startswith("http") and "duckduckgo.com" not in href:
            links.append(href)
        if len(links) >= limit:
            break
    return links


def gather(topic: str) -> Reference:
    """Return grounded Markdown + the sources used for ``topic``."""
    chunks: List[str] = []
    sources: List[str] = []
    method = "empty"

    with httpx.Client(timeout=config.HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
        # 1. Wikipedia (resolved + Jina).
        wiki = _resolve_wikipedia(client, topic)
        if wiki:
            try:
                md = _fetch_jina(client, wiki)
                if len(md.strip()) >= config.MIN_REFERENCE_CHARS:
                    chunks.append(md)
                    sources.append(wiki)
                    method = "jina-wiki"
            except Exception as exc:  # noqa: BLE001
                print(f"[reference] Jina Wikipedia failed: {exc}")
                try:
                    md = _fetch_soup(client, wiki)
                    if len(md.strip()) >= config.MIN_REFERENCE_CHARS:
                        chunks.append(md)
                        sources.append(wiki)
                        method = "soup"
                except Exception as exc2:  # noqa: BLE001
                    print(f"[reference] soup Wikipedia failed: {exc2}")

        # 2. DuckDuckGo breadth (fill up to the budget).
        budget_left = config.MAX_REFERENCE_CHARS - sum(len(c) for c in chunks)
        if budget_left > 1500:
            for link in _duckduckgo_links(client, topic):
                if link in sources:
                    continue
                try:
                    md = _fetch_jina(client, link)
                except Exception:  # noqa: BLE001
                    continue
                if len(md.strip()) < 300:
                    continue
                host = urlparse(link).netloc
                chunks.append(f"\n\n### Source: {host}\n{md}")
                sources.append(link)
                if method == "empty":
                    method = "jina-ddg"
                if sum(len(c) for c in chunks) >= config.MAX_REFERENCE_CHARS:
                    break

    if not chunks:
        print("[reference] no substantial reference; grounding on the title only.")
        return Reference(markdown=topic, sources=[], method="empty")

    combined = _truncate("\n\n".join(chunks))
    print(f"[reference] method={method} chars={len(combined)} sources={len(sources)}")
    return Reference(markdown=combined, sources=sources, method=method)


if __name__ == "__main__":
    import sys

    t = sys.argv[1] if len(sys.argv) > 1 else "Braess's paradox"
    ref = gather(t)
    print(f"method={ref.method} ok={ref.ok} chars={len(ref.markdown)} sources={ref.sources}")
    print(ref.markdown[:600])
