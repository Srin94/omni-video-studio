"""Defensive illustration inference — a safety net, not the main path.

The browser LLM is asked to fill `scene.illustration` directly (see
prompt_assembler). This module only *backfills* it when the LLM left it empty,
and ONLY from unambiguous signals, so it can never manufacture a wrong visual
(a wrong picture is worse than none — the scene just keeps its archetype/B-roll):

  1. a `node_network` visual_element  -> a concept_flow (it IS a flow already)
  2. a "<number> <countable-noun>" adjacency in the narration
     (e.g. "86 billion neurons", "4,000 drivers") -> a glyph_world crowd

Everything is deterministic and offline (no network, no model)."""

from __future__ import annotations

import re
from typing import List, Optional

try:
    from .schema import (
        OmniRenderPayload, SceneSpec, SceneIllustration,
        GlyphWorldSpec, ConceptFlowSpec, FlowNode, FlowEdge,
    )
except ImportError:  # pragma: no cover
    from schema import (  # type: ignore
        OmniRenderPayload, SceneSpec, SceneIllustration,
        GlyphWorldSpec, ConceptFlowSpec, FlowNode, FlowEdge,
    )


# noun (as it may appear in narration) -> glyph name understood by the renderer
_UNIT_GLYPH = {
    "neuron": "neuron", "neurons": "neuron", "synapse": "neuron", "synapses": "neuron",
    "cell": "neuron", "cells": "neuron",
    "driver": "car", "drivers": "car", "car": "car", "cars": "car", "vehicle": "car",
    "vehicles": "car",
    "person": "person", "people": "person", "human": "person", "humans": "person",
    "voter": "person", "voters": "person", "user": "person", "users": "person",
    "worker": "person", "workers": "person", "citizen": "person", "citizens": "person",
    "customer": "person", "customers": "person", "soldier": "person", "soldiers": "person",
    "dollar": "coin", "dollars": "coin", "coin": "coin", "coins": "coin",
    "atom": "atom", "atoms": "atom", "electron": "atom", "electrons": "atom",
    "molecule": "atom", "molecules": "atom", "particle": "atom", "particles": "atom",
    "gene": "dna", "genes": "dna",
    "star": "star", "stars": "star", "galaxy": "star", "galaxies": "star",
    "planet": "planet", "planets": "planet",
    "file": "file", "files": "file", "record": "file", "records": "file",
    "row": "file", "rows": "file", "document": "file", "documents": "file",
    "server": "server", "servers": "server", "computer": "server", "computers": "server",
    "request": "request", "requests": "request", "packet": "request", "packets": "request",
    "message": "request", "messages": "request",
    "building": "building", "buildings": "building", "city": "building", "cities": "building",
    "house": "building", "houses": "building", "factory": "building", "factories": "building",
    "idea": "bulb", "ideas": "bulb", "book": "book", "books": "book",
    "box": "box", "boxes": "box", "package": "box", "packages": "box",
    "tree": "tree", "trees": "tree", "patient": "heart", "patients": "heart",
    # science / space
    "photon": "wave", "photons": "wave", "signal": "wave", "signals": "wave",
    "wave": "wave", "waves": "wave", "ray": "wave", "rays": "wave",
    "galaxy": "star", "galaxies": "star", "comet": "star", "comets": "star",
    "satellite": "satellite", "satellites": "satellite", "probe": "satellite", "probes": "satellite",
    # biology / health
    "virus": "virus", "viruses": "virus", "microbe": "virus", "microbes": "virus",
    "bacteria": "virus", "bacterium": "virus", "pathogen": "virus", "pathogens": "virus",
    "pill": "pill", "pills": "pill", "dose": "pill", "doses": "pill", "vaccine": "pill",
    "vaccines": "pill", "fish": "fish", "bird": "bird", "birds": "bird",
    "leaf": "leaf", "leaves": "leaf",
    # tech / physics / energy
    "transistor": "chip", "transistors": "chip", "chip": "chip", "chips": "chip",
    "fire": "flame", "fires": "flame", "flame": "flame", "flames": "flame",
}

# formation keyword scoring against the narration (verb/shape of the sentence)
_FORM_WORDS = {
    "jam": ["jam", "bottleneck", "congest", "gridlock", "stuck", "crush", "clog", "overload", "pile up", "traffic"],
    "rush": ["rush", "flood", "surge", "pour", "stream", "flock", "race ", "arrive", "commute", "storm in"],
    "queue": ["queue", "in line", "wait", "backlog", "one by one", "rate limit", "throttle", "sequence"],
    "scatter": ["scatter", "spread", "broadcast", "fan out", "disperse", "emerge", "explode"],
    "orbit": ["orbit", "revolve", "circle", "network", "loop", "cycle", "around the", "rotate"],
    "field": ["each", "every", "all of", "population", "percent", "fraction", "share", "most", "half", "billions", "millions", "fire", "light up"],
}

_MAG = {"trillion": 1_000_000_000_000, "billion": 1_000_000_000, "million": 1_000_000,
        "thousand": 1_000, "k": 1_000, "m": 1_000_000, "b": 1_000_000_000}

# lucide icon guesses for flow-node labels
_NODE_ICON = {
    "brain": "brain", "model": "brain", "neural": "brain", "mind": "brain",
    "server": "server", "backend": "server", "api": "cpu", "service": "cpu",
    "cpu": "cpu", "processor": "cpu", "compute": "cpu",
    "database": "database", "db": "database", "store": "database", "storage": "database",
    "data": "database", "table": "table",
    "cache": "zap", "redis": "zap", "queue": "list", "buffer": "list",
    "user": "user", "client": "user", "person": "user", "customer": "user", "driver": "car",
    "cloud": "cloud", "network": "network", "internet": "globe", "web": "globe",
    "input": "log-in", "source": "log-in", "start": "play", "begin": "play",
    "output": "log-out", "result": "flag", "end": "flag", "goal": "flag",
    "bridge": "git-merge", "router": "git-merge", "road": "route", "route": "route",
    "town": "building-2", "city": "building-2", "node": "circle-dot", "shortcut": "zap",
    "sensor": "radio", "signal": "radio", "money": "banknote", "bank": "landmark",
    # science / space
    "telescope": "telescope", "scope": "telescope", "mirror": "aperture", "lens": "aperture",
    "optic": "aperture", "detector": "camera", "camera": "camera", "ccd": "camera",
    "image": "image", "light": "sparkles", "photon": "sparkles", "star": "star",
    "orbit": "orbit", "planet": "orbit", "satellite": "satellite", "rocket": "rocket",
    "sun": "sun", "solar": "sun", "moon": "moon", "atom": "atom", "electron": "atom",
    "nucleus": "atom", "wave": "radio", "gene": "dna", "dna": "dna", "cell": "microscope",
    "virus": "bug", "lab": "flask-conical", "fire": "flame", "energy": "zap",
}


def _num(text: str, mag: Optional[str]) -> int:
    base = float(re.sub(r"[,\s]", "", text))
    if mag:
        base *= _MAG.get(mag.lower(), 1)
    return int(round(base))


def _unit_pattern() -> re.Pattern:
    nouns = sorted(_UNIT_GLYPH.keys(), key=len, reverse=True)
    noun_alt = "|".join(re.escape(n) for n in nouns)
    mag_alt = "|".join(sorted(_MAG.keys(), key=len, reverse=True))
    # NUMBER [magnitude] NOUN  — the number is tied to the noun, so a stray year
    # or duration ("90 minutes", "in 1958") can't become a population.
    return re.compile(
        rf"(\d[\d,\.]*)\s*({mag_alt})?\s+({noun_alt})\b",
        re.IGNORECASE,
    )


_UNIT_RE = _unit_pattern()
_PCT_RE = re.compile(r"(\d[\d\.]*)\s*(?:%|percent)")


def _pick_formation(text: str) -> str:
    low = text.lower()
    best, score = "field", 0
    for form, words in _FORM_WORDS.items():
        s = sum(1 for w in words if w in low)
        if s > score:
            best, score = form, s
    return best


def _status(text: str, hud_text: str) -> str:
    low = (text + " " + hud_text).lower()
    if any(w in low for w in ("critical", "collapse", "crash", "fail", "worse", "overload", "disaster", "gridlock")):
        return "critical"
    if any(w in low for w in ("warning", "strain", "slow", "bottleneck", "stuck", "jam", "risk", "pressure")):
        return "warning"
    return "normal"


def _node_icon(label: str) -> str:
    low = label.lower()
    for key, icon in _NODE_ICON.items():
        if key in low:
            return icon
    return "circle-dot"


def _flow_from_node_network(scene: SceneSpec) -> Optional[ConceptFlowSpec]:
    for el in scene.visual_elements:
        if el.element_type != "node_network":
            continue
        parts = [p.strip() for p in re.split(r"\s*(?:->|→|=>|,|then)\s*", el.subtext) if p.strip()]
        if len(parts) < 2:
            continue
        nodes: List[FlowNode] = []
        edges: List[FlowEdge] = []
        colors = ["cyan", "emerald", "amber", "violet"]
        for i, label in enumerate(parts[:6]):
            nid = f"n{i}"
            nodes.append(FlowNode(id=nid, label=label[:28], icon=_node_icon(label), tier=i + 1,
                                   highlight=(i == len(parts) - 1)))
            if i > 0:
                edges.append(FlowEdge(source=f"n{i-1}", target=nid, color=colors[(i - 1) % len(colors)], animate=True))
        return ConceptFlowSpec(title=(el.headline or scene.chapter_title)[:40], nodes=nodes, edges=edges,
                               caption=el.subtext[:90])
    return None


def _world_from_text(scene: SceneSpec) -> Optional[GlyphWorldSpec]:
    m = _UNIT_RE.search(scene.narration_text)
    if not m:
        return None
    population = _num(m.group(1), m.group(2))
    if population < 8:  # too small to read as a crowd
        return None
    noun = m.group(3).lower()
    glyph = _UNIT_GLYPH[noun]
    hud_text = " ".join(f"{h.label} {h.value} {h.delta or ''}" for h in scene.hud_metrics)
    formation = _pick_formation(scene.narration_text)
    status = _status(scene.narration_text, hud_text)
    pct = _PCT_RE.search(scene.narration_text)
    if pct:
        active = min(1.0, float(pct.group(1)) / 100.0)
    else:
        active = {"jam": 0.78, "rush": 0.6, "queue": 0.45, "field": 0.5, "scatter": 0.5, "orbit": 0.7}[formation]
    unit_label = noun if noun.endswith("s") else noun + "s"
    return GlyphWorldSpec(
        unit_icon=glyph,
        formation=formation,  # type: ignore[arg-type]
        population=population,
        active_fraction=round(active, 2),
        section_label=scene.chapter_title[:22],
        headline=f"{m.group(1)}{(' ' + m.group(2)) if m.group(2) else ''} {unit_label}".strip(),
        unit_label=unit_label,
        active_label="active" if status == "normal" else ("stuck" if formation in ("jam", "rush") else "affected"),
        # No caption: the narration already plays as the subtitle, so an inferred
        # caption would just echo it. Author-supplied worlds set a distinct beat.
        caption="",
        status=status,  # type: ignore[arg-type]
    )


def infer_scene(scene: SceneSpec) -> None:
    if scene.illustration is not None:
        return  # the LLM already specified one — never override it
    flow = _flow_from_node_network(scene)
    if flow is not None:
        scene.illustration = SceneIllustration(kind="concept_flow", flow=flow)
        return
    world = _world_from_text(scene)
    if world is not None:
        scene.illustration = SceneIllustration(kind="glyph_world", world=world)


def infer_payload(payload: OmniRenderPayload) -> int:
    """Backfill illustrations across the payload. Returns how many were added."""
    added = 0
    for scene in payload.scenes:
        before = scene.illustration is not None
        try:
            infer_scene(scene)
        except Exception as exc:  # noqa: BLE001 — never fatal
            print(f"[illustration] infer failed for scene {scene.scene_id}: {exc}")
        if not before and scene.illustration is not None:
            added += 1
    if added:
        print(f"[illustration] backfilled {added} scene(s).")
    return added
