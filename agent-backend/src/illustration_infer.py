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
    # motion / forces / mechanical
    "battery": "battery-charging", "motor": "cog", "engine": "cog", "gear": "cog",
    "rotor": "fan", "fan": "fan", "blade": "fan", "propeller": "fan", "turbine": "fan",
    "propulsion": "rocket", "thrust": "move-up", "lift": "move-up", "rise": "move-up",
    "upward": "arrow-up", "up ": "arrow-up", "downward": "arrow-down", "down": "arrow-down",
    "gravity": "arrow-down-to-line", "weight": "anvil", "mass": "anvil", "heavy": "anvil",
    "load": "package", "payload": "package", "cargo": "package",
    "air": "wind", "wind": "wind", "flow": "wind", "aerodynam": "wind",
    "flight": "plane", "aircraft": "plane", "plane": "plane", "fly": "plane", "aviation": "plane",
    "vehicle": "car", "car": "car", "drone": "send",
    # control / systems / measurement
    "control": "sliders-horizontal", "adjust": "sliders-horizontal", "tune": "sliders-horizontal",
    "balance": "scale", "stability": "scale", "stable": "scale", "law": "scale", "force": "scale",
    "computer": "cpu", "chip": "cpu", "electron": "cpu",
    "power": "zap", "electric": "zap", "voltage": "zap", "current": "zap", "charge": "zap",
    "range": "gauge", "distance": "gauge", "speed": "gauge", "velocity": "gauge", "rate": "gauge",
    "consumption": "gauge", "endurance": "gauge",
    # logic / verdicts / abstractions (common in explainer scenes)
    "fact": "badge-check", "verified": "badge-check", "established": "badge-check",
    "real": "badge-check", "true": "badge-check", "proven": "badge-check",
    "fiction": "circle-help", "speculation": "circle-help", "unverified": "circle-help",
    "myth": "circle-help", "false": "circle-x", "question": "circle-help", "unknown": "circle-help",
    "future": "sparkles", "concept": "lightbulb", "idea": "lightbulb", "theory": "lightbulb",
    "challenge": "triangle-alert", "problem": "triangle-alert", "limit": "triangle-alert",
    "risk": "triangle-alert", "trade-off": "git-compare", "tradeoff": "git-compare",
    "versus": "git-compare", "compare": "git-compare", "difference": "git-compare",
    "cost": "banknote", "price": "banknote", "profit": "trending-up", "growth": "trending-up",
    "reaction": "repeat", "cycle": "repeat-2", "loop": "repeat-2", "step": "footprints",
    "time": "clock", "year": "calendar", "history": "scroll", "process": "workflow",
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
    # Longest matching key wins, so a specific term beats a substring of it
    # (e.g. "unverified" is not mis-read as "verified", "database" not "data").
    low = label.lower()
    best_key = ""
    best_icon = "circle-dot"
    for key, icon in _NODE_ICON.items():
        k = key.strip()
        if k and k in low and len(k) > len(best_key):
            best_key, best_icon = k, icon
    return best_icon


# A flow is built from the scene's own STRUCTURED fields (visual-element
# headlines, HUD metric values, callout keywords) — which the model fills
# reliably — rather than by chopping a narration sentence on its commas (that
# produced nonsense like "Monitor movement -> orientation -> and stability").
_EDGE_COLORS = ["cyan", "emerald", "amber", "violet"]
_VS_RE = re.compile(r"\s+(?:vs\.?|versus|or)\s+", re.IGNORECASE)
_LABEL_STRIP = re.compile(r"^[\"'“”\s]+|[\"'“”\s]+$")


def _clean_label(text: str, max_len: int = 26) -> str:
    s = re.sub(r"\s+", " ", (text or "")).strip()
    s = _LABEL_STRIP.sub("", s).strip(" .")
    if len(s) > max_len:
        s = s[:max_len].rstrip() + "…"
    return s


def _dedupe(labels: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for lab in labels:
        key = lab.lower()
        if lab and len(lab) >= 2 and key not in seen:
            seen.add(key)
            out.append(lab)
    return out


def _comparison_branch(scene: SceneSpec) -> Optional[ConceptFlowSpec]:
    """A comparison_split whose headline reads 'A vs B' becomes a branch:
    topic -> {A, B}. The clearest possible 'these two are weighed' visual."""
    for el in scene.visual_elements:
        if el.element_type != "comparison_split":
            continue
        parts = _VS_RE.split(el.headline or "")
        if len(parts) != 2:
            continue
        a, b = _clean_label(parts[0]), _clean_label(parts[1])
        if not a or not b:
            continue
        root = _clean_label(scene.chapter_title, 30) or "Compare"
        nodes = [
            FlowNode(id="n0", label=root, icon=_node_icon(root), tier=1),
            FlowNode(id="nA", label=a, icon=_node_icon(a), tier=2, highlight=True),
            FlowNode(id="nB", label=b, icon=_node_icon(b), tier=2, highlight=True),
        ]
        edges = [
            FlowEdge(source="n0", target="nA", color="emerald", animate=True),
            FlowEdge(source="n0", target="nB", color="amber", animate=True),
        ]
        return ConceptFlowSpec(title=root, nodes=nodes, edges=edges, caption=_clean_label(el.subtext, 90))
    return None


def _linear_flow(scene: SceneSpec) -> Optional[ConceptFlowSpec]:
    """Chain the scene's concrete labels into a 2-5 node flow. Concept headlines
    lead, then HUD values (the concrete nouns), then callout keywords as filler."""
    candidates: List[str] = []
    for el in scene.visual_elements:
        candidates.append(_clean_label(el.headline))
    for m in scene.hud_metrics:
        candidates.append(_clean_label(m.value))
    for kw in scene.callout_keywords:
        candidates.append(_clean_label(kw))

    labels = _dedupe([c for c in candidates if c])[:4]
    if len(labels) < 2:
        return None

    nodes: List[FlowNode] = []
    edges: List[FlowEdge] = []
    for i, lab in enumerate(labels):
        nid = f"n{i}"
        nodes.append(FlowNode(id=nid, label=lab, icon=_node_icon(lab), tier=i + 1,
                              highlight=(i == len(labels) - 1)))
        if i > 0:
            edges.append(FlowEdge(source=f"n{i-1}", target=nid,
                                  color=_EDGE_COLORS[(i - 1) % len(_EDGE_COLORS)], animate=True))
    return ConceptFlowSpec(title=_clean_label(scene.chapter_title, 40), nodes=nodes, edges=edges, caption="")


def _flow_from_structure(scene: SceneSpec) -> Optional[ConceptFlowSpec]:
    """Every scene gets an animated diagram (a branch for a comparison, else a
    flow), so no scene is ever a bare card-wall with an empty half."""
    return _comparison_branch(scene) or _linear_flow(scene)


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
    # A specific countable-noun crowd is the strongest visual when it applies;
    # otherwise build an animated flow from the scene's own structure so EVERY
    # scene shows a real diagram instead of a static card-wall.
    world = _world_from_text(scene)
    if world is not None:
        scene.illustration = SceneIllustration(kind="glyph_world", world=world)
        return
    flow = _flow_from_structure(scene)
    if flow is not None:
        scene.illustration = SceneIllustration(kind="concept_flow", flow=flow)


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
