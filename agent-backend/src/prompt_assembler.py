"""Master Synthesis Prompt generator (spec section 3).

Packages the scraped factual grounding, the narrative constraints and the EXACT
`OmniRenderPayload` JSON schema into one comprehensive prompt. The operator copies
it with one click, pastes it into Gemini Advanced / Claude Pro in the browser, and
pastes the raw JSON back for validation + render. This replaces an LLM API call,
so the pipeline never hits a rate limit for script generation.
"""

from __future__ import annotations

import json
from typing import List

try:
    from . import config
    from .schema import OmniRenderPayload
except ImportError:  # pragma: no cover
    import config  # type: ignore
    from schema import OmniRenderPayload  # type: ignore


# Human-readable genre labels for the prompt header.
_GENRE_LABEL = {
    "SCIENCE_PHYSICS": "Science & Physics",
    "MONEY_BUSINESS": "Business & Money",
    "CRIME_MYSTERY": "True Crime & Mystery",
    "EVERYDAY_TECH": "Everyday Tech",
    "HISTORY_CULTURE": "History & Culture",
    "PARADOX_LOGIC": "Game Theory & Paradoxes",
}

# Per-genre tonal + archetype steer.
_GENRE_STEER = {
    "SCIENCE_PHYSICS": "Precise and wondrous. Favour NEON_TECHNICAL_HUD telemetry "
    "and stat_card / node_network elements. BGM: upbeat_curious_tech.",
    "MONEY_BUSINESS": "Sharp and consequential. Favour KINETIC_MINIMALIST giant "
    "numbers and comparison_split / stat_card. BGM: cinematic_investigative.",
    "CRIME_MYSTERY": "Tense, restrained, factual. Favour NARRATIVE_STORYBOARD with "
    "timeline_milestone / map_pin / quote_callout. BGM: dark_ambient_synth.",
    "EVERYDAY_TECH": "Energetic and clarifying. Favour NEON_TECHNICAL_HUD and "
    "node_network / stat_card to show how the thing works. BGM: upbeat_curious_tech.",
    "HISTORY_CULTURE": "Evocative and grounded. Favour DOCUMENTARY_ARCHIVE with "
    "timeline_milestone / quote_callout / map_pin. BGM: cinematic_investigative.",
    "PARADOX_LOGIC": "Playful but rigorous. Favour KINETIC_MINIMALIST and "
    "comparison_split / stat_card to stage the counter-intuitive turn. "
    "BGM: minimal_tension.",
}


def _format_targets(video_format: str) -> dict:
    """Runtime, scene-count and per-scene word targets for each format."""
    if video_format == "portrait":
        return {
            "runtime": "a punchy 55-70 second vertical Short",
            "scenes": "6 to 8 scenes",
            "words": "18-26 spoken words per scene",
            "frame": "9:16 vertical (1080x1920)",
        }
    return {
        "runtime": "a 3 to 5 minute landscape video (aim for 190-300 seconds)",
        "scenes": "16 to 22 scenes",
        "words": "24-34 spoken words per scene",
        "frame": "16:9 landscape (1920x1080)",
    }


_ARCHETYPE_GUIDE = """FOUR VISUAL ARCHETYPES — set `visual_archetype` per scene and \
VARY them beat to beat so the video never feels static:
- DOCUMENTARY_ARCHIVE: warm vintage paper, typewriter titles, archival stamps, \
photo-frame feel. Best for history, origins, human stories, dossiers.
- KINETIC_MINIMALIST: stark high-contrast canvas, massive kinetic typography, \
giant numbers, bold split cards. Best for a single shocking statistic or a sharp \
either/or contrast.
- NEON_TECHNICAL_HUD: dark oscilloscope console, glowing grid, telemetry counters, \
flow nodes. Best for mechanisms, systems, "how it works", data.
- NARRATIVE_STORYBOARD: cinematic charcoal, letterbox accents, floating timeline \
breadcrumbs. Best for chronology, investigations, cause-and-effect.

ELEMENTS — fill `visual_elements` (max 3 per scene) with the right kind for the beat:
- stat_card (headline=the number, subtext=what it means), quote_callout \
(headline=the quote, subtext=attribution), comparison_split (headline=A vs B, \
subtext=the verdict), node_network (headline=the system, subtext=the flow), \
map_pin (headline=the place, subtext=what happened there), timeline_milestone \
(headline=the date/event, subtext=the significance). Set highlight_color to one of \
emerald | cyan | crimson | amber | violet to signal tone (crimson=danger/loss, \
emerald=gain/success, amber=caution, cyan=neutral/tech, violet=mystery).

HUD METRICS — fill `hud_metrics` (max 4) with live readouts that EVOLVE across \
scenes: label (e.g. 'Probability', 'Year', 'Net Worth'), value (the concrete \
figure), and optional delta ('+14%', 'CRITICAL', 'FALLING'). Keep labels stable \
across scenes and change the values so the viewer watches the story move."""


_ILLUSTRATION_GUIDE = """ANIMATED ILLUSTRATION (`illustration`) — THE top engagement \
lever. For scenes about a COUNT, a MECHANISM, a SYSTEM or a FLOW, don't just show a \
photo — DRAW the idea so it animates while the narrator talks. Set `illustration` on \
roughly half to two-thirds of scenes (the conceptual ones). Pick ONE kind:

1) "glyph_world" — draw the countable noun of the sentence as a CROWD of little \
glowing icons that move to match the verb. Use it whenever the scene has a number of \
things (86 billion neurons, 4,000 drivers, 10 million rows, 70% of users). Fill \
`world`:
   - unit_icon: the thing each icon is — person, car, coin, neuron, atom, dna, file, \
building, server, database, box, star, planet, gear, bulb, book, flask, bolt, \
droplet, heart, tree, request. (Plain nouns like "people", "drivers", "cells" also work.)
   - formation = the VERB/shape: field (a population; a % lights up) · rush (they \
stream toward a gate) · jam (a bottleneck/overload crush) · queue (an orderly line) · \
scatter (fan out from a hub) · orbit (circle a nucleus — atoms, networks, systems).
   - population = the REAL integer (86000000000). active_fraction = 0..1 lit/active share.
   - headline ("86 billion neurons"), unit_label ("neurons"), active_label ("firing"), \
section_label (2-3 word kicker), caption (one plain sentence = the beat), \
status (normal|warning|critical — use warning/critical for overload/jam/failure beats).
   - ONLY use glyph_world for a count of discrete THINGS (stars, people, cells, cars, \
rows). NEVER for a span of time, a distance, money or a measurement — "175 million \
YEARS" is a duration, not 175M objects, so use a stat_card or concept_flow instead. \
unit_icon, unit_label and active_label must all describe the SAME thing.

2) "concept_flow" — a left-to-right DIAGRAM of a process or architecture with packets \
flowing along the arrows. Use it for "how X works", pipelines, cause→effect chains. \
Fill `flow`:
   - nodes: [{ id, label, icon, tier, highlight }]. tier = the column (1,2,3…) so the \
flow reads left→right. icon = a lucide-react name (brain, cpu, database, server, \
network, zap, cloud, globe, user, git-merge, route…). highlight=true for the key node.
   - edges: [{ source, target, label?, color?, animate }] using node ids. color = \
emerald|cyan|crimson|amber|violet. Keep animate=true so data visibly flows.
   - title (2-4 words), caption (one sentence), focus_node_id (optional node to spotlight).

Rule of thumb: a NUMBER of things → glyph_world; a PROCESS/SYSTEM → concept_flow; a \
real photographable object/place/person/artifact → leave illustration null and use \
broll_query instead. Never set both for one scene. Leave illustration null for a scene \
that is purely a quote, a single date, or a place to show as a photo."""


_BROLL_GUIDE = """B-ROLL — for scenes you did NOT give an `illustration`, this is the \
single most important field for making the scene feel like a real video and NOT a \
slideshow. For every such scene set `broll_query` to the \
concrete, searchable VISUAL SUBJECT the viewer should literally SEE behind the \
narration — a real photo or diagram the backend will fetch from a free image \
library and float behind the scene with a slow camera move.
- Name the LITERAL thing, with specific/proper nouns: "a single biological \
neuron", "the Rosetta Stone", "New York City subway map", "Wall Street during the \
1929 crash", "a Formula 1 car's rear wing", "the Antikythera mechanism".
- When the narration says "neuron", the broll_query is "biological neuron"; when \
it says "neural network", it is "artificial neural network diagram". Match the \
image to what is being SAID in that exact scene.
- Avoid abstractions ("innovation", "the economy", "complexity") — they return \
junk. Pick a photographable object, place, person, artifact, chart or diagram.
- 2-5 words, no sentences. One subject per scene."""


_ARC_GUIDE = """THE 4-ACT CURIOSITY ARC (structure every video this way):
- ACT 1 — THE HOOK (first ~15%): open on the single most counter-intuitive fact \
or highest-stakes moment, backed by a HARD NUMBER. State the provocative promise \
immediately. Never 'Welcome back' / 'In today's video' / 'Hey guys'.
- ACT 2 — THE BUILD (the heart, ~55%): walk the mechanism / story / case forward \
ONE concrete step per scene. Use real figures, dates, names, units from the \
reference. Each scene must add a genuinely new fact or move the story to a new \
state — never restate or pad.
- ACT 3 — THE PAYOFF / SCALE (~20%): reveal the underlying formula, the twist, or \
scale the idea up to the real world with concrete numbers (billions, physical \
limits, the verdict).
- ACT 4 — THE BRAIN-TEASER (final scene + pinned_comment): pose a twist that \
invites a prediction or debate in the comments."""


def build_master_prompt(
    topic: str,
    genre: str,
    video_format: str,
    reference_markdown: str,
    sources: List[str] | None = None,
) -> str:
    """Assemble the full copy-paste Master Synthesis Prompt for the browser LLM."""
    targets = _format_targets(video_format)
    schema_json = json.dumps(OmniRenderPayload.model_json_schema(), indent=2)
    genre_label = _GENRE_LABEL.get(genre, genre)
    steer = _GENRE_STEER.get(genre, "")
    sources_block = ""
    if sources:
        sources_block = "\nSOURCES USED:\n" + "\n".join(f"- {s}" for s in sources) + "\n"

    return f"""You are the showrunner AND principal writer for a premium, \
high-retention explainer YouTube channel ("{config.CHANNEL_NAME}") in the lineage \
of Vox, Johnny Harris, Wendover, 3Blue1Brown and Primer. You turn a factual \
reference into a tightly-paced, intensely visual script as a STRICT JSON object.

TASK
Genre: {genre_label}  (genre enum: {genre})
Topic: "{topic}"
Target: {targets['runtime']} — {targets['scenes']}, {targets['words']}.
Frame: {targets['frame']} (video_format = "{video_format}").
Tone & visual steer: {steer}

Every claim MUST be grounded in the FACTUAL REFERENCE below — real equations, \
units, dates, names, dollar figures, step-by-step mechanics. Depth over filler: \
a longer runtime means MORE distinct, specific facts, never repetition.

{_ARC_GUIDE}

{_ILLUSTRATION_GUIDE}

{_BROLL_GUIDE}

{_ARCHETYPE_GUIDE}

OUTPUT META
- genre: use "{genre}" EXACTLY.
- suggested_bgm_mood: one of dark_ambient_synth | cinematic_investigative | \
upbeat_curious_tech | acoustic_thoughtful | minimal_tension (match the tone steer).
- youtube_title: curiosity-gap hook under 70 characters.
- youtube_description: 2-3 sentences + chapter timestamps.
- youtube_tags: 8-12 relevant tags.
- pinned_comment: the Act-4 brain-teaser / debate question.
- thumbnail_headline: 3-4 BOLD high-impact words. thumbnail_sub_badge: a short \
genre/angle badge (e.g. "GAME THEORY", "SOLVED", "HOW IT WORKS").
- scenes: each with scene_id (1..N in order), chapter_title (2-4 words), \
narration_text ({targets['words']}, use "..." and commas for natural pauses), \
visual_archetype, camera_movement (pan_right | slow_zoom_in | slow_zoom_out | \
static_focus), EITHER illustration (see ANIMATED ILLUSTRATION above — for count / \
mechanism / flow scenes) OR broll_query (the concrete visual subject — for \
photographable scenes), hud_metrics, visual_elements, callout_keywords (2-3 words \
that appear VERBATIM in that scene's narration_text to highlight in subtitles).
- Leave words and total_duration_sec empty / 0, start_sec / duration_sec at 0, and \
broll_asset / broll_attribution / broll_source_url null — the backend fills exact \
timings and fetches the imagery after voiceover. Set illustration to null on scenes \
that use a photo.

CRITICAL OUTPUT FORMAT
Respond with ONLY one raw JSON object — NO markdown code fences, NO prose before \
or after — that strictly conforms to this JSON Schema:

{schema_json}
{sources_block}
FACTUAL REFERENCE (Markdown, may be truncated):
---
{reference_markdown}
---
Return ONLY the JSON object now."""


def assemble(
    topic: str,
    genre: str,
    video_format: str,
    reference_markdown: str,
    sources: List[str] | None = None,
) -> dict:
    """Return the prompt plus light metadata for the studio UI."""
    prompt = build_master_prompt(topic, genre, video_format, reference_markdown, sources)
    return {
        "topic": topic,
        "genre": genre,
        "video_format": video_format,
        "sources": sources or [],
        "reference_chars": len(reference_markdown),
        "master_prompt": prompt,
    }


if __name__ == "__main__":
    out = assemble(
        "Braess's paradox",
        "PARADOX_LOGIC",
        "landscape",
        "Braess's paradox: adding a road to a congested network can slow everyone "
        "down. In 1990 New York closed 42nd Street on Earth Day and traffic improved.",
        ["https://en.wikipedia.org/wiki/Braess%27s_paradox"],
    )
    print(out["master_prompt"][:2000])
