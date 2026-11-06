// The crowd MOTION engine. `computeCrowd` returns the exact screen placement of
// every glyph FOR A GIVEN FRAME, plus the live counts the chrome reads. The
// painter (GlyphWorld) only draws what this returns — all movement lives here, as
// a pure function of localFrame (deterministic, no Math.random).
//
// Five formations map a VERB to motion:
//   rush   — units stream in from the left and funnel through a gate
//   jam    — same gate, already crushed (bottleneck / overload)
//   queue  — orderly lanes that slowly drain
//   field  — a grid fills; a fraction lights up (share active / lit / infected)
//   scatter— units fan out from a central hub on a golden-angle spiral
//   orbit  — units circle a nucleus on nested rings (systems, atoms, networks)

import { hash01, smooth, type GlyphKind } from "./glyphs";

export type Formation = "rush" | "jam" | "queue" | "field" | "scatter" | "orbit";
export type CrowdStatus = "normal" | "warning" | "critical";

export interface CrowdColors {
  active: string;
  idle: string;
  warn: string;
  crit: string;
}

export interface CrowdInput {
  unit_icon: GlyphKind;
  formation: Formation;
  population: number;
  active_fraction: number; // 0..1
  status: CrowdStatus;
}

export interface PlacedGlyph {
  key: number;
  x: number;
  y: number;
  size: number;
  color: string;
  glow: number; // 0..1 -> drop-shadow blur strength
  opacity: number;
}

export interface CrowdResult {
  glyphs: PlacedGlyph[];
  shown: number;
  population: number;
  activeCount: number;
  stuckCount: number;
  gate: { x: number; y: number; h: number } | null;
  hub: { x: number; y: number } | null;
}

export interface Dims {
  W: number;
  H: number;
  top: number; // top of the drawable crowd band (px)
  bottom: number; // bottom of the band
  portrait: boolean;
}

const CAP: Record<Formation, number> = {
  field: 260,
  rush: 150,
  jam: 150,
  queue: 120,
  scatter: 96,
  orbit: 80,
};

const litColorFor = (status: CrowdStatus, c: CrowdColors): string =>
  status === "critical" ? c.crit : status === "warning" ? c.warn : c.active;

export function computeCrowd(
  input: CrowdInput,
  colors: CrowdColors,
  localFrame: number,
  dims: Dims,
): CrowdResult {
  const pop = Math.max(1, Math.round(input.population || 1));
  const shown = Math.max(1, Math.min(pop, CAP[input.formation] ?? 150));
  const frac = Math.min(1, Math.max(0, input.active_fraction ?? 0));
  const activeCount = Math.round(pop * frac);
  const litColor = litColorFor(input.status, colors);
  const { W, top, bottom, portrait } = dims;
  const bandH = Math.max(80, bottom - top);
  const midY = top + bandH / 2;
  const base: Omit<CrowdResult, "glyphs"> = {
    shown,
    population: pop,
    activeCount,
    stuckCount: 0,
    gate: null,
    hub: null,
  };
  const glyphs: PlacedGlyph[] = [];

  // -------------------------------------------------------------- field
  if (input.formation === "field") {
    const cols = portrait ? 11 : 18;
    const rows = Math.ceil(shown / cols);
    const areaW = W * 0.8;
    const cell = Math.min(areaW / cols, bandH / Math.max(rows, 1));
    const size = cell * 0.6;
    const gridW = cols * cell;
    const gridH = rows * cell;
    const ox = (W - gridW) / 2 + cell / 2;
    const oy = top + Math.max(0, (bandH - gridH) / 2) + cell / 2;
    for (let i = 0; i < shown; i += 1) {
      const r = Math.floor(i / cols);
      const c = i % cols;
      const appear = smooth(i * 0.22, i * 0.22 + 9, localFrame);
      const lit = hash01(i + 7) < frac;
      const tw = lit ? 0.6 + 0.4 * Math.sin(localFrame * 0.13 + i * 0.7) : 0;
      glyphs.push({
        key: i,
        x: ox + c * cell,
        y: oy + r * cell,
        size,
        color: lit ? litColor : colors.idle,
        glow: lit ? 0.65 + 0.35 * tw : 0.1,
        opacity: appear * (lit ? 1 : 0.42),
      });
    }
    return { ...base, glyphs };
  }

  // -------------------------------------------------- rush / jam (gate)
  if (input.formation === "rush" || input.formation === "jam") {
    const instant = input.formation === "jam";
    const gateX = W * (portrait ? 0.62 : 0.72);
    const opening = bandH * 0.62;
    const gateY = midY;
    const lanes = portrait ? 7 : 11;
    const size = Math.min(bandH / 10, W / 30);
    let stuck = 0;
    for (let i = 0; i < shown; i += 1) {
      const lane = i % lanes;
      const depth = hash01(i * 3 + 1); // 0..1 near/far
      const laneY = gateY - opening / 2 + (opening * (lane + 0.5)) / lanes;
      const y = laneY + (depth - 0.5) * (opening / lanes) * 0.8;
      const sizeI = size * (0.78 + depth * 0.5);
      const speed = instant ? 7 : 1.4 + hash01(i) * 1.4;
      const startX = -70 - (i % 24) * 44 - hash01(i * 5) * 260;
      let x = startX + localFrame * speed * (instant ? 2.4 : 1);
      const admitted = hash01(i * 7 + 3) < frac;
      if (!admitted) {
        const crushX = gateX - 34 - (i % 9) * 15 - depth * 22;
        if (x > crushX) {
          x = crushX;
          stuck += 1;
        }
      }
      if (x > W + 30) continue; // left the frame (admitted, flowed on)
      const opIn = smooth(0, 10, x + 80);
      const pulse = 0.5 + 0.5 * Math.sin(localFrame * 0.12 + i);
      glyphs.push({
        key: i,
        x,
        y,
        size: sizeI,
        color: admitted ? colors.active : litColor,
        glow: admitted ? 0.4 : input.status === "normal" ? 0.3 : 0.6 + 0.3 * pulse,
        opacity: opIn,
      });
    }
    glyphs.sort((a, b) => a.y - b.y); // painter's order (near overlaps far)
    return {
      ...base,
      glyphs,
      stuckCount: Math.round((stuck / shown) * pop),
      gate: { x: gateX, y: gateY, h: opening },
    };
  }

  // ------------------------------------------------------------- queue
  if (input.formation === "queue") {
    const lanes = portrait ? 5 : 7;
    const perLane = Math.ceil(shown / lanes);
    const size = Math.min(bandH / 9, W / 26);
    const spacing = size * 1.35;
    const laneGap = bandH / (lanes + 1);
    const drift = (localFrame * 0.5) % spacing; // slow leftward drain
    for (let i = 0; i < shown; i += 1) {
      const lane = Math.floor(i / perLane);
      const idx = i % perLane;
      const y = top + laneGap * (lane + 1);
      const x = W * 0.84 - idx * spacing - drift;
      const appear = smooth(idx * 0.6, idx * 0.6 + 8, localFrame);
      const lit = idx / perLane < frac; // the served front
      const fadeLeft = smooth(W * 0.08, W * 0.16, x);
      glyphs.push({
        key: i,
        x,
        y,
        size,
        color: lit ? litColor : colors.idle,
        glow: lit ? 0.55 : 0.12,
        opacity: appear * fadeLeft * (lit ? 1 : 0.6),
      });
    }
    return { ...base, glyphs };
  }

  // ----------------------------------------------------------- scatter
  if (input.formation === "scatter") {
    const cx = W / 2;
    const cy = midY;
    const size = Math.min(bandH / 12, W / 34);
    const golden = 2.399963;
    for (let i = 0; i < shown; i += 1) {
      const appear = smooth(i * 0.35, i * 0.35 + 10, localFrame);
      const ang = i * golden;
      const rad = (size * 1.2 + Math.sqrt(i) * size * 1.0) * appear;
      const lit = hash01(i + 2) < frac;
      glyphs.push({
        key: i,
        x: cx + Math.cos(ang) * rad,
        y: cy + Math.sin(ang) * rad * 0.74,
        size,
        color: lit ? litColor : colors.idle,
        glow: lit ? 0.65 : 0.18,
        opacity: appear * (lit ? 1 : 0.55),
      });
    }
    return { ...base, glyphs, hub: { x: cx, y: cy } };
  }

  // ------------------------------------------------------------- orbit
  const cx = W / 2;
  const cy = midY;
  const size = Math.min(bandH / 13, W / 36);
  const rings = 3;
  const maxR = Math.min(W * 0.26, bandH * 0.46);
  for (let i = 0; i < shown; i += 1) {
    const ring = i % rings;
    const ringR = ((ring + 0.8) / rings) * maxR;
    const speed = (rings - ring) * 0.012 + 0.006;
    const appear = smooth(i * 0.25, i * 0.25 + 10, localFrame);
    const ang = hash01(i) * Math.PI * 2 + localFrame * speed;
    const lit = hash01(i + 2) < Math.max(frac, 0.5);
    glyphs.push({
      key: i,
      x: cx + Math.cos(ang) * ringR,
      y: cy + Math.sin(ang) * ringR * 0.64,
      size,
      color: lit ? colors.active : colors.idle,
      glow: lit ? 0.6 : 0.2,
      opacity: appear * (lit ? 1 : 0.6),
    });
  }
  glyphs.sort((a, b) => a.y - b.y);
  return { ...base, glyphs, hub: { x: cx, y: cy } };
}
