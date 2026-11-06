// TypeScript mirror of the Python Pydantic OmniRenderPayload contract in
// agent-backend/src/schema.py. These two MUST stay in lock-step.
//
// Universal, genre-agnostic contract: each scene picks ONE of four
// `visual_archetype` canvases and carries dynamic HUD metrics + visual elements.

export interface WordTimestamp {
  word: string;
  start_sec: number;
  end_sec: number;
}

export type HighlightColor = "emerald" | "cyan" | "crimson" | "amber" | "violet";

export interface DynamicHUDMetric {
  label: string; // "Velocity", "Net Worth", "Probability", "Year"
  value: string; // "28,000 km/h", "$4.2 Billion", "0.0014%"
  delta?: string | null; // "+14%", "CRITICAL", "FALLING"
}

export type ElementType =
  | "stat_card"
  | "quote_callout"
  | "comparison_split"
  | "node_network"
  | "map_pin"
  | "timeline_milestone";

export interface VisualElement {
  element_type: ElementType;
  headline: string;
  subtext: string;
  badge?: string | null;
  highlight_color: HighlightColor;
}

// ---------------------------------------------------------------------------
// Animated illustration — the engagement layer. A scene may carry ONE of two
// data-driven, animated illustrations that draw the MEANING of the narration:
//   glyph_world  — the countable noun as a crowd of glowing glyphs in a formation
//   concept_flow — a tier-laid-out node/edge diagram with packets flowing along it
// Both are optional; a scene without one falls back to B-roll / the archetype.
// ---------------------------------------------------------------------------
export type GlyphFormation = "rush" | "jam" | "queue" | "field" | "scatter" | "orbit";
export type IllustrationStatus = "normal" | "warning" | "critical";

export interface GlyphWorldSpec {
  unit_icon: string; // glyph name: person|car|coin|neuron|atom|file|building|... (aliased)
  formation: GlyphFormation; // the VERB: rush|jam|queue|field|scatter|orbit
  population: number; // the real count being visualized (e.g. 86_000_000_000)
  active_fraction: number; // 0..1 share lit / admitted / active
  gate_label?: string | null;
  section_label?: string; // small kicker, e.g. "THE BRAIN"
  headline?: string; // big line, e.g. "86 billion neurons"
  unit_label?: string; // what one glyph is, for the count pill (e.g. "neurons")
  active_label?: string; // what "active" means (e.g. "firing")
  caption?: string; // one-line story beat
  status?: IllustrationStatus;
}

export interface FlowNode {
  id: string;
  label: string;
  sublabel?: string;
  icon?: string; // lucide-react icon name, e.g. "brain", "cpu", "database"
  tier: number; // 1..N — the column (left→right reading order)
  highlight?: boolean;
}

export interface FlowEdge {
  source: string; // node id
  target: string; // node id
  label?: string;
  color?: string; // highlight name (emerald|cyan|...) or a hex
  animate?: boolean; // stream packets along it (default true)
}

export interface ConceptFlowSpec {
  title?: string;
  nodes: FlowNode[];
  edges: FlowEdge[];
  focus_node_id?: string | null;
  caption?: string;
}

export type IllustrationKind = "glyph_world" | "concept_flow";

export interface SceneIllustration {
  kind: IllustrationKind;
  world?: GlyphWorldSpec | null;
  flow?: ConceptFlowSpec | null;
}

export type VisualArchetype =
  | "DOCUMENTARY_ARCHIVE"
  | "KINETIC_MINIMALIST"
  | "NEON_TECHNICAL_HUD"
  | "NARRATIVE_STORYBOARD";

export type CameraMovement =
  | "pan_right"
  | "slow_zoom_in"
  | "slow_zoom_out"
  | "static_focus";

export interface SceneSpec {
  scene_id: number;
  chapter_title: string; // 2-4 words
  narration_text: string;
  visual_archetype: VisualArchetype;
  camera_movement: CameraMovement;
  hud_metrics: DynamicHUDMetric[];
  visual_elements: VisualElement[];
  callout_keywords: string[];
  illustration?: SceneIllustration | null; // animated glyph-world / concept-flow
  broll_query?: string; // concrete visual subject for topic-matched imagery
  start_sec: number;
  duration_sec: number;
  // Stamped by the backend B-roll fetcher (may be null when nothing was found).
  broll_asset?: string | null; // e.g. "assets/broll/scene_01.jpg"
  broll_attribution?: string | null; // "Creator · CC BY 2.0"
  broll_source_url?: string | null;
}

export type Genre =
  | "SCIENCE_PHYSICS"
  | "MONEY_BUSINESS"
  | "CRIME_MYSTERY"
  | "EVERYDAY_TECH"
  | "HISTORY_CULTURE"
  | "PARADOX_LOGIC";

export type BgmMood =
  | "dark_ambient_synth"
  | "cinematic_investigative"
  | "upbeat_curious_tech"
  | "acoustic_thoughtful"
  | "minimal_tension";

export type VideoFormat = "landscape" | "portrait";

export interface OmniRenderPayload {
  genre: Genre;
  suggested_bgm_mood: BgmMood;
  youtube_title: string;
  youtube_description: string;
  youtube_tags: string[];
  pinned_comment: string;
  thumbnail_headline: string;
  thumbnail_sub_badge: string;
  scenes: SceneSpec[];
  words: WordTimestamp[];
  total_duration_sec: number;
  video_format: VideoFormat;
  source_urls: string[];
}
