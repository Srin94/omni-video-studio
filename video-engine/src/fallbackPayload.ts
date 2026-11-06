import type { OmniRenderPayload } from "./types/schema";

// Bundled sample so Remotion Studio / a render always has something valid to draw
// even before the Python pipeline writes public/assets/render_payload.json. It
// exercises all four archetypes.

export const FALLBACK_PAYLOAD: OmniRenderPayload = {
  genre: "PARADOX_LOGIC",
  suggested_bgm_mood: "minimal_tension",
  youtube_title: "The Road That Made Traffic WORSE",
  youtube_description:
    "Braess's paradox: adding a road can slow everyone down. A toy network, the math, and the real cities that tore roads out.",
  youtube_tags: ["game theory", "braess paradox", "traffic", "networks", "nash equilibrium"],
  pinned_comment:
    "If every driver is selfish, can a city ever reach the FASTEST outcome on its own? Drop your take 👇",
  thumbnail_headline: "ADD ROAD, LOSE TIME",
  thumbnail_sub_badge: "GAME THEORY",
  video_format: "landscape",
  source_urls: ["https://en.wikipedia.org/wiki/Braess%27s_paradox"],
  words: [],
  total_duration_sec: 24,
  scenes: [
    {
      scene_id: 1,
      chapter_title: "THE WRONG ROAD",
      narration_text:
        "In 1990, New York closed 42nd Street... and traffic got faster. Adding roads can make everyone slower. It sounds impossible.",
      visual_archetype: "KINETIC_MINIMALIST",
      camera_movement: "slow_zoom_in",
      hud_metrics: [
        { label: "Year", value: "1990", delta: null },
        { label: "Travel Time", value: "-7 min", delta: "FALLING" },
      ],
      visual_elements: [
        { element_type: "stat_card", headline: "42nd ST", subtext: "Closed — and the jam eased", badge: "NEW YORK", highlight_color: "amber" },
      ],
      callout_keywords: ["faster", "slower"],
      start_sec: 0,
      duration_sec: 6,
    },
    {
      scene_id: 2,
      chapter_title: "THE TOY NETWORK",
      narration_text:
        "Picture 4,000 drivers, two routes, each a mix of a fixed bridge and a crowd-sensitive road. At balance, everyone takes 90 minutes.",
      visual_archetype: "NEON_TECHNICAL_HUD",
      camera_movement: "pan_right",
      hud_metrics: [
        { label: "Drivers", value: "4,000", delta: null },
        { label: "Routes", value: "2", delta: null },
        { label: "Time", value: "90 min", delta: "STABLE" },
      ],
      visual_elements: [
        { element_type: "node_network", headline: "The Commute", subtext: "START -> Bridge -> Town -> END", badge: "MODEL", highlight_color: "cyan" },
      ],
      callout_keywords: ["4,000", "90"],
      start_sec: 6,
      duration_sec: 6,
    },
    {
      scene_id: 3,
      chapter_title: "THE SHORTCUT TRAP",
      narration_text:
        "Now add a super-fast shortcut linking the two. Every selfish driver grabs it... and the new equilibrium is 105 minutes. Worse for all.",
      visual_archetype: "NARRATIVE_STORYBOARD",
      camera_movement: "static_focus",
      hud_metrics: [
        { label: "Time", value: "105 min", delta: "+15 min" },
        { label: "Winners", value: "0", delta: "CRITICAL" },
      ],
      visual_elements: [
        { element_type: "comparison_split", headline: "90 min vs 105 min", subtext: "The shortcut made everyone slower", badge: "EQUILIBRIUM", highlight_color: "crimson" },
      ],
      callout_keywords: ["shortcut", "105"],
      start_sec: 12,
      duration_sec: 6,
    },
    {
      scene_id: 4,
      chapter_title: "TORN OUT",
      narration_text:
        "Seoul ripped out a highway in 2003 and traffic improved. The fix for a selfish network... can be a road removed. Would you vote for that?",
      visual_archetype: "DOCUMENTARY_ARCHIVE",
      camera_movement: "slow_zoom_out",
      hud_metrics: [
        { label: "City", value: "Seoul", delta: null },
        { label: "Year", value: "2003", delta: null },
      ],
      visual_elements: [
        { element_type: "timeline_milestone", headline: "2003", subtext: "Cheonggyecheon highway demolished — flow improved", badge: "CASE FILE", highlight_color: "emerald" },
      ],
      callout_keywords: ["Seoul", "removed"],
      start_sec: 18,
      duration_sec: 6,
    },
  ],
};
