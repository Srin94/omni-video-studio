// Visual-archetype design tokens. Each of the four archetypes is a distinct
// canvas "look"; the Adaptive Layout Director (MasterComposition) mounts the
// matching scene component and themes the shared HUD + subtitles from here.
//
// Palettes mirror agent-backend/src/thumbnail_generator.py so a video and its
// thumbnail read as the same world.

import type React from "react";
import type { VisualArchetype, HighlightColor } from "../types/schema";

export interface ArchetypeTheme {
  mode: "light" | "dark";
  canvasBg: string;
  canvasBg2: string;
  grid: string;
  textPrimary: string;
  textMuted: string;
  accent: string;
  accent2: string;
  onAccent: string;
  card: string;
  cardBorder: string;
  fontHeading: string;
  fontMono: string;
  fontDisplay: string;
}

const MONO = "'IBM Plex Mono', 'JetBrains Mono', 'Consolas', monospace";
const SANS = "'Space Grotesk', 'Segoe UI', system-ui, sans-serif";

export const ARCHETYPES: Record<VisualArchetype, ArchetypeTheme> = {
  DOCUMENTARY_ARCHIVE: {
    mode: "light",
    canvasBg: "#F3EFE4",
    canvasBg2: "#E7E0CE",
    grid: "#D8CFBB",
    textPrimary: "#201B12",
    textMuted: "#6E6450",
    accent: "#C2410C",
    accent2: "#0369A1",
    onAccent: "#FBF6EC",
    card: "#FBF8F0",
    cardBorder: "#CDC2A9",
    fontHeading: SANS,
    fontMono: MONO,
    fontDisplay: "'Playfair Display', Georgia, serif",
  },
  KINETIC_MINIMALIST: {
    mode: "dark",
    canvasBg: "#0A0A0A",
    canvasBg2: "#141414",
    grid: "#262626",
    textPrimary: "#FAFAFA",
    textMuted: "#8A8A8A",
    accent: "#FACC15",
    accent2: "#F472B6",
    onAccent: "#111111",
    card: "#161616",
    cardBorder: "#2E2E2E",
    fontHeading: SANS,
    fontMono: MONO,
    fontDisplay: SANS,
  },
  NEON_TECHNICAL_HUD: {
    mode: "dark",
    canvasBg: "#080C14",
    canvasBg2: "#0C1424",
    grid: "#17304A",
    textPrimary: "#E8F1FB",
    textMuted: "#6B8099",
    accent: "#38BDF8",
    accent2: "#34D399",
    onAccent: "#06121F",
    card: "#0E1A2C",
    cardBorder: "#1E3A57",
    fontHeading: SANS,
    fontMono: MONO,
    fontDisplay: MONO,
  },
  NARRATIVE_STORYBOARD: {
    mode: "dark",
    canvasBg: "#12131A",
    canvasBg2: "#1A1C26",
    grid: "#2A2D3A",
    textPrimary: "#ECEAF2",
    textMuted: "#7B7E90",
    accent: "#F43F5E",
    accent2: "#A78BFA",
    onAccent: "#140A0D",
    card: "#1C1E2A",
    cardBorder: "#30323F",
    fontHeading: SANS,
    fontMono: MONO,
    fontDisplay: "'Playfair Display', Georgia, serif",
  },
};

export const getArchetype = (a: VisualArchetype): ArchetypeTheme =>
  ARCHETYPES[a] ?? ARCHETYPES.NEON_TECHNICAL_HUD;

export const HIGHLIGHT: Record<HighlightColor, string> = {
  emerald: "#34D399",
  cyan: "#38BDF8",
  crimson: "#F43F5E",
  amber: "#FBBF24",
  violet: "#A78BFA",
};

export const gridBackground = (t: ArchetypeTheme): React.CSSProperties => ({
  backgroundImage: `linear-gradient(${t.grid} 1px, transparent 1px), linear-gradient(90deg, ${t.grid} 1px, transparent 1px)`,
  backgroundSize: "64px 64px",
});
