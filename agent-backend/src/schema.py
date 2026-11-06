"""Universal multi-genre data contract — the single source of truth.

`OmniRenderPayload` is the strict JSON contract shared VERBATIM (field for field)
with the Remotion engine's `video-engine/src/types/schema.ts`. The Human-in-the-
Loop prompt relay forces Gemini Advanced / Claude Pro (in the browser) to emit a
JSON object that validates against this model; the backend then renders it.

Unlike the single-domain sibling agents, this schema is genre-agnostic: a scene
picks ONE of four `visual_archetype` canvases and carries dynamic HUD metrics +
visual elements that each archetype knows how to draw.

Keep the Pydantic models and the TypeScript interfaces in lock-step.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Controlled vocabularies (shared with the frontend genre pills + TS unions)
# ---------------------------------------------------------------------------
Genre = Literal[
    "SCIENCE_PHYSICS",
    "MONEY_BUSINESS",
    "CRIME_MYSTERY",
    "EVERYDAY_TECH",
    "HISTORY_CULTURE",
    "PARADOX_LOGIC",
]

BgmMood = Literal[
    "dark_ambient_synth",
    "cinematic_investigative",
    "upbeat_curious_tech",
    "acoustic_thoughtful",
    "minimal_tension",
]

VisualArchetype = Literal[
    "DOCUMENTARY_ARCHIVE",
    "KINETIC_MINIMALIST",
    "NEON_TECHNICAL_HUD",
    "NARRATIVE_STORYBOARD",
]

CameraMovement = Literal[
    "pan_right",
    "slow_zoom_in",
    "slow_zoom_out",
    "static_focus",
]

ElementType = Literal[
    "stat_card",
    "quote_callout",
    "comparison_split",
    "node_network",
    "map_pin",
    "timeline_milestone",
]

HighlightColor = Literal["emerald", "cyan", "crimson", "amber", "violet"]

VideoFormat = Literal["landscape", "portrait"]

# Animated-illustration vocabularies (mirrored in the TS schema).
GlyphFormation = Literal["rush", "jam", "queue", "field", "scatter", "orbit"]
IllustrationStatus = Literal["normal", "warning", "critical"]
IllustrationKind = Literal["glyph_world", "concept_flow"]


# ---------------------------------------------------------------------------
# Leaf models
# ---------------------------------------------------------------------------
class WordTimestamp(BaseModel):
    word: str
    start_sec: float
    end_sec: float


class DynamicHUDMetric(BaseModel):
    label: str = Field(
        description="e.g. 'Velocity', 'Net Worth', 'Probability', 'Decibels', 'Year'"
    )
    value: str = Field(
        description="e.g. '28,000 km/h', '$4.2 Billion', '0.0014%', '-18 dB', '1944 AD'"
    )
    delta: Optional[str] = Field(
        default=None, description="e.g. '+14%', 'CRITICAL', 'FALLING'"
    )


class VisualElement(BaseModel):
    element_type: ElementType
    headline: str
    subtext: str
    badge: Optional[str] = None
    highlight_color: HighlightColor = "cyan"


class GlyphWorldSpec(BaseModel):
    """A crowd of glyphs that draws the countable noun of the narration."""

    unit_icon: str = Field(
        description="The glyph to draw for each unit — a concrete countable noun: "
        "person | car | coin | neuron | atom | dna | file | building | server | "
        "database | box | star | planet | gear | bulb | book | flask | bolt | "
        "droplet | heart | tree | clock | request. Aliases (people, drivers, money, "
        "cells, records, cities...) are accepted."
    )
    formation: GlyphFormation = Field(
        default="field",
        description="The VERB / motion: field (a population, a share lit up), rush "
        "(units stream toward a gate), jam (a bottleneck / overload crush), queue "
        "(an orderly line draining), scatter (fan out from a hub), orbit (circle a "
        "nucleus — systems, atoms, networks).",
    )
    population: int = Field(
        default=0,
        description="The REAL count being visualized, e.g. 86000000000 neurons, 4000 "
        "drivers, 10000000 rows. The on-screen counter ticks up to this.",
    )
    active_fraction: float = Field(
        default=0.0,
        description="0..1 — the share that is lit / admitted / active / affected.",
    )
    gate_label: Optional[str] = None
    section_label: str = Field(default="", description="Short kicker, e.g. 'THE BRAIN'")
    headline: str = Field(default="", description="Big line, e.g. '86 billion neurons'")
    unit_label: str = Field(default="", description="What one glyph is, e.g. 'neurons'")
    active_label: str = Field(default="", description="What active means, e.g. 'firing'")
    caption: str = Field(default="", description="One-line story beat under the crowd")
    status: IllustrationStatus = "normal"


class FlowNode(BaseModel):
    id: str
    label: str
    sublabel: str = ""
    icon: str = Field(
        default="",
        description="A lucide-react icon name (lowercase-hyphenated), e.g. brain, "
        "cpu, database, server, network, zap, git-branch, globe, cloud, shield.",
    )
    tier: int = Field(default=1, description="1..N — the column; flow reads left→right")
    highlight: bool = False


class FlowEdge(BaseModel):
    source: str = Field(description="source node id")
    target: str = Field(description="target node id")
    label: str = ""
    color: str = Field(default="", description="emerald|cyan|crimson|amber|violet or #hex")
    animate: bool = True


class ConceptFlowSpec(BaseModel):
    """A node/edge diagram with packets flowing along the edges."""

    title: str = ""
    nodes: List[FlowNode] = Field(default_factory=list)
    edges: List[FlowEdge] = Field(default_factory=list)
    focus_node_id: Optional[str] = None
    caption: str = Field(default="", description="One-line story beat under the diagram")


class SceneIllustration(BaseModel):
    kind: IllustrationKind
    world: Optional[GlyphWorldSpec] = None
    flow: Optional[ConceptFlowSpec] = None


class SceneSpec(BaseModel):
    scene_id: int
    chapter_title: str = Field(
        description="2-4 words, e.g. 'THE CONCRETE DISASTER', 'THE HIDDEN FORMULA'"
    )
    narration_text: str = Field(
        description="Spoken text. Use ellipsis (...) or commas for natural pauses. "
        "20-35 words per scene."
    )
    visual_archetype: VisualArchetype
    camera_movement: CameraMovement = "slow_zoom_in"
    hud_metrics: List[DynamicHUDMetric] = Field(default_factory=list, max_length=4)
    visual_elements: List[VisualElement] = Field(default_factory=list, max_length=3)
    callout_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords to highlight in the karaoke subtitles",
    )
    illustration: Optional[SceneIllustration] = Field(
        default=None,
        description="OPTIONAL animated illustration that DRAWS the meaning of this "
        "scene — a glyph_world (crowd of the countable noun) or a concept_flow "
        "(node/edge diagram). When present it becomes the scene's main visual "
        "instead of a static photo. See the ILLUSTRATION guide.",
    )
    broll_query: str = Field(
        default="",
        description="A concrete, image-searchable VISUAL SUBJECT for this scene — "
        "the literal thing a viewer should SEE, e.g. 'a single biological neuron', "
        "'the Rosetta Stone', 'New York City subway map', 'Wall Street 1929 crash'. "
        "Prefer specific nouns/proper nouns over abstractions. The backend fetches a "
        "real, freely-licensed photo/diagram of it and floats it behind the scene.",
    )
    # Filled by the audio engine after TTS alignment (left at defaults by the LLM).
    start_sec: float = 0.0
    duration_sec: float = 0.0
    # Stamped by the backend's B-roll fetcher (relative asset path + CC credit).
    broll_asset: Optional[str] = None
    broll_attribution: Optional[str] = None
    broll_source_url: Optional[str] = None


class OmniRenderPayload(BaseModel):
    genre: Genre
    suggested_bgm_mood: BgmMood
    youtube_title: str = Field(description="High-CTR curiosity hook under 70 chars")
    youtube_description: str
    youtube_tags: List[str]
    pinned_comment: str = Field(
        description="A provocative debate or quiz question for the comments section"
    )
    thumbnail_headline: str = Field(
        description="3-4 high-impact words for the thumbnail graphic"
    )
    thumbnail_sub_badge: str
    scenes: List[SceneSpec]
    words: List[WordTimestamp] = Field(default_factory=list)
    total_duration_sec: float = 0.0
    # Not emitted by the model — stamped by the backend so the renderer and the
    # studio always know the frame. Defaults keep older payloads valid.
    video_format: VideoFormat = "landscape"
    source_urls: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Genre -> sensible defaults (used when stamping / repairing a payload)
# ---------------------------------------------------------------------------
GENRE_DEFAULT_MOOD: dict[str, str] = {
    "SCIENCE_PHYSICS": "upbeat_curious_tech",
    "MONEY_BUSINESS": "cinematic_investigative",
    "CRIME_MYSTERY": "dark_ambient_synth",
    "EVERYDAY_TECH": "upbeat_curious_tech",
    "HISTORY_CULTURE": "cinematic_investigative",
    "PARADOX_LOGIC": "minimal_tension",
}

GENRE_DEFAULT_ARCHETYPE: dict[str, str] = {
    "SCIENCE_PHYSICS": "NEON_TECHNICAL_HUD",
    "MONEY_BUSINESS": "KINETIC_MINIMALIST",
    "CRIME_MYSTERY": "NARRATIVE_STORYBOARD",
    "EVERYDAY_TECH": "NEON_TECHNICAL_HUD",
    "HISTORY_CULTURE": "DOCUMENTARY_ARCHIVE",
    "PARADOX_LOGIC": "KINETIC_MINIMALIST",
}


if __name__ == "__main__":
    import json

    print(json.dumps(OmniRenderPayload.model_json_schema(), indent=2)[:1800])
