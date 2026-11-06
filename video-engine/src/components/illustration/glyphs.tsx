// Hand-authored glyph set for the "living world" crowd illustration — the thing
// that draws the countable noun of a sentence (neurons, drivers, dollars, rows)
// as a field of small glowing icons. Each glyph is a filled 24x24 SVG silhouette
// so it reads clearly at ~26px in a crowd of 150+.
//
// Why not lucide for the crowd? Crowd glyphs must be solid single-colour fills
// (outline icons disappear at small size against a glow). lucide-react IS used,
// but for the flow-diagram NODE icons (see ConceptFlow.tsx), where size is large.
//
// Everything here is a pure function of its inputs — no Math.random — so headless
// Chromium renders every frame identically (essential for Remotion).

import React from "react";

export type GlyphKind =
  | "person" | "car" | "coin" | "brain" | "neuron" | "atom" | "dna" | "star"
  | "planet" | "gear" | "file" | "building" | "bulb" | "book" | "flask" | "bolt"
  | "droplet" | "server" | "database" | "box" | "heart" | "tree" | "clock"
  | "ticket" | "request"
  | "satellite" | "wave" | "virus" | "chip" | "fish" | "bird" | "leaf" | "pill"
  | "flame" | "eye" | "shield" | "cloud" | "sun" | "moon" | "rocket"
  | "dot";

// 24x24 viewBox. `fill="currentColor"` on the <svg>; detail sub-shapes may set
// their own fill (a dark alpha) to suggest depth. Stroked children set stroke.
const GLYPH_PATHS: Record<GlyphKind, React.ReactNode> = {
  person: (
    <>
      <circle cx="12" cy="6.4" r="3.6" />
      <path d="M5 21c0-3.9 3.1-7 7-7s7 3.1 7 7z" />
    </>
  ),
  car: (
    <path d="M4 12l1.7-4.4A2 2 0 0 1 7.6 6.4h8.8a2 2 0 0 1 1.9 1.2L20 12v4.6a1 1 0 0 1-1 1h-1.3a2.3 2.3 0 0 1-4.6 0H9.9a2.3 2.3 0 0 1-4.6 0H4a1 1 0 0 1-1-1V12z" />
  ),
  coin: (
    <>
      <circle cx="12" cy="12" r="8.6" />
      <circle cx="12" cy="12" r="4.8" fill="rgba(0,0,0,0.3)" />
    </>
  ),
  brain: (
    <path d="M9 4a3.6 3.6 0 0 0-3.5 4.6A3.4 3.4 0 0 0 5.8 15 3.3 3.3 0 0 0 12 16.4 3.3 3.3 0 0 0 18.2 15a3.4 3.4 0 0 0 .3-6.4A3.6 3.6 0 0 0 15 4a3 3 0 0 0-3 1.7A3 3 0 0 0 9 4z" />
  ),
  neuron: (
    <>
      <g stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinecap="round">
        <path d="M12 12L4.5 5.5M12 12l7.5-5M12 12l-7 7.5M12 12l8 6.5M12 12V3.5M12 12l-8.5 2" />
      </g>
      <circle cx="12" cy="12" r="3.3" />
      <circle cx="4.5" cy="5.5" r="1.1" />
      <circle cx="19.5" cy="7" r="1.1" />
      <circle cx="20" cy="18.5" r="1.1" />
      <circle cx="5" cy="19.5" r="1.1" />
    </>
  ),
  atom: (
    <>
      <circle cx="12" cy="12" r="2" />
      <g stroke="currentColor" strokeWidth="1.3" fill="none">
        <ellipse cx="12" cy="12" rx="10" ry="4.2" />
        <ellipse cx="12" cy="12" rx="10" ry="4.2" transform="rotate(60 12 12)" />
        <ellipse cx="12" cy="12" rx="10" ry="4.2" transform="rotate(120 12 12)" />
      </g>
    </>
  ),
  dna: (
    <g stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round">
      <path d="M8 3c0 4.5 8 4.5 8 9s-8 4.5-8 9" />
      <path d="M16 3c0 4.5-8 4.5-8 9s8 4.5 8 9" />
      <path d="M8.6 7h6.8M7.2 12h9.6M8.6 17h6.8" />
    </g>
  ),
  star: (
    <path d="M12 2l2.9 6.3 6.9.8-5.1 4.7 1.4 6.8L12 18.3 5.9 21.4l1.4-6.8L2.2 9.9l6.9-.8z" />
  ),
  planet: (
    <>
      <circle cx="12" cy="12" r="6" />
      <ellipse cx="12" cy="12" rx="11" ry="3.4" transform="rotate(-20 12 12)" stroke="currentColor" strokeWidth="1.5" fill="none" />
    </>
  ),
  gear: (
    <path fillRule="evenodd" d="M12 1.8l1.5 2.6 2.9-.6.5 2.9 2.7 1.3-1.2 2.7 1.8 2.3-2.2 2 .5 2.9-2.9.4-1.4 2.6-2.8-1.2-2.8 1.2-1.4-2.6-2.9-.4.5-2.9-2.2-2 1.8-2.3L3 11l2.7-1.3.5-2.9 2.9.6L10.5 1.8 12 1.8zm0 7a3.2 3.2 0 1 0 0 6.4 3.2 3.2 0 0 0 0-6.4z" />
  ),
  file: (
    <>
      <path d="M6 3h7.5L18 7.5V21H6z" />
      <path d="M13.3 3.2V7.5H17.8" fill="rgba(0,0,0,0.28)" />
    </>
  ),
  building: (
    <path fillRule="evenodd" d="M4 21V4h8v5h8v12H4zm3-13h2v2H7V8zm0 4h2v2H7v-2zm0 4h2v2H7v-2zm8-4h2v2h-2v-2zm0 4h2v2h-2v-2z" />
  ),
  bulb: (
    <>
      <path d="M12 2.6a6.2 6.2 0 0 0-3.7 11.2c.6.5 1 1.2 1 2V16h5.4v-.2c0-.8.4-1.5 1-2A6.2 6.2 0 0 0 12 2.6z" />
      <rect x="9.3" y="17.4" width="5.4" height="1.7" rx="0.7" />
      <rect x="9.9" y="19.8" width="4.2" height="1.7" rx="0.7" />
    </>
  ),
  book: (
    <>
      <path d="M3 5c3-1.6 6-1.6 9 0 3-1.6 6-1.6 9 0v13.2c-3-1.6-6-1.6-9 0-3-1.6-6-1.6-9 0V5z" />
      <path d="M12 5v13.2" stroke="rgba(0,0,0,0.25)" strokeWidth="1" fill="none" />
    </>
  ),
  flask: (
    <path d="M9 3h6v1.8h-1v4.6l4.5 7.6A2 2 0 0 1 16.8 20H7.2a2 2 0 0 1-1.7-3l4.5-7.6V4.8H9z" />
  ),
  bolt: (
    <path d="M13 2L4 14h6l-1 8 9-12h-6z" />
  ),
  droplet: (
    <path d="M12 3s7 7.4 7 11.6a7 7 0 0 1-14 0C5 10.4 12 3 12 3z" />
  ),
  server: (
    <>
      <rect x="3.5" y="4" width="17" height="7" rx="1.6" />
      <rect x="3.5" y="13" width="17" height="7" rx="1.6" />
      <circle cx="7.5" cy="7.5" r="1.1" fill="rgba(0,0,0,0.32)" />
      <circle cx="7.5" cy="16.5" r="1.1" fill="rgba(0,0,0,0.32)" />
    </>
  ),
  database: (
    <>
      <path d="M12 3c4.2 0 7.5 1.3 7.5 2.9v12.2c0 1.6-3.3 2.9-7.5 2.9s-7.5-1.3-7.5-2.9V5.9C4.5 4.3 7.8 3 12 3z" />
      <ellipse cx="12" cy="5.9" rx="7.5" ry="2.9" fill="rgba(0,0,0,0.3)" />
    </>
  ),
  box: (
    <>
      <path d="M12 2.2l9 5v9.6l-9 5-9-5V7.2z" />
      <path d="M12 2.2v19.6M3 7.2l9 5 9-5" stroke="rgba(0,0,0,0.26)" strokeWidth="1.2" fill="none" />
    </>
  ),
  heart: (
    <path d="M12 21s-7-4.6-9.3-9C1 8.6 2.8 5 6.3 5 8.4 5 10 6.3 12 8.5 14 6.3 15.6 5 17.7 5c3.5 0 5.3 3.6 3.6 7C19 16.4 12 21 12 21z" />
  ),
  tree: (
    <>
      <path d="M12 2l5 7.2h-3l4 6H3l4-6H4z" />
      <rect x="10.5" y="15.2" width="3" height="6" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5.2l3.4 2" stroke="rgba(0,0,0,0.33)" strokeWidth="1.7" fill="none" strokeLinecap="round" />
    </>
  ),
  ticket: (
    <path d="M3 8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2 2 2 0 0 0 0 4 2 2 0 0 1-2 2H5a2 2 0 0 1-2-2 2 2 0 0 0 0-4z" />
  ),
  request: (
    <path d="M3.5 9.2h9V6l7 6-7 6v-3.2h-9z" />
  ),
  satellite: (
    <>
      <rect x="10" y="9" width="4" height="6" rx="1" />
      <path d="M2.5 9.4h5.2v5.2H2.5zM16.3 9.4h5.2v5.2h-5.2z" />
      <g stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinecap="round">
        <path d="M13.5 8.5l2.4-2.4" />
      </g>
      <circle cx="16.4" cy="5.4" r="1.4" />
    </>
  ),
  wave: (
    <g fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round">
      <path d="M4.5 14a7.5 7.5 0 0 1 15 0" />
      <path d="M8 14a4 4 0 0 1 8 0" />
      <circle cx="12" cy="14" r="1.5" fill="currentColor" stroke="none" />
    </g>
  ),
  virus: (
    <>
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="2" fill="rgba(0,0,0,0.3)" />
      <g stroke="currentColor" strokeWidth="1.7" strokeLinecap="round">
        <path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.8 4.8l2.1 2.1M17.1 17.1l2.1 2.1M19.2 4.8l-2.1 2.1M6.9 17.1l-2.1 2.1" />
      </g>
      <circle cx="12" cy="3" r="1.2" /><circle cx="12" cy="21" r="1.2" />
      <circle cx="3" cy="12" r="1.2" /><circle cx="21" cy="12" r="1.2" />
    </>
  ),
  chip: (
    <>
      <rect x="7" y="7" width="10" height="10" rx="1.6" />
      <rect x="10" y="10" width="4" height="4" fill="rgba(0,0,0,0.32)" />
      <g stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
        <path d="M9.5 7V4M12 7V4M14.5 7V4M9.5 20v-3M12 20v-3M14.5 20v-3M7 9.5H4M7 12H4M7 14.5H4M20 9.5h-3M20 12h-3M20 14.5h-3" />
      </g>
    </>
  ),
  fish: (
    <>
      <ellipse cx="11" cy="12" rx="7" ry="4.3" />
      <path d="M17.5 12l4.5-3.2v6.4z" />
      <circle cx="7.5" cy="10.8" r="1.1" fill="rgba(0,0,0,0.45)" />
    </>
  ),
  bird: (
    <path d="M2.5 13.5c3 0 4.2-4.2 6-4.2s3 4.2 4 4.2 2-4.2 4-4.2 3 4.2 6 4.2" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" />
  ),
  leaf: (
    <>
      <path d="M5 19.5c-.5-8.5 6-14.5 14.5-14.5C20 13.5 13.5 19.5 5 19.5z" />
      <path d="M11.5 13L17 7.5" stroke="rgba(0,0,0,0.28)" strokeWidth="1.3" fill="none" strokeLinecap="round" />
    </>
  ),
  pill: (
    <>
      <rect x="3.5" y="9.3" width="17" height="5.4" rx="2.7" />
      <path d="M12 9.3v5.4" stroke="rgba(0,0,0,0.32)" strokeWidth="1.3" fill="none" />
    </>
  ),
  flame: (
    <path d="M12 2c1.3 3.8-3 5.2-3 9a5 5 0 0 0 10 0c0-2.2-1.1-3.4-2.2-4.5.3 2.3-1.2 3.3-2.3 3.3 1.3-4.2-1.8-6-2.5-7.8z" />
  ),
  eye: (
    <>
      <path d="M2 12s4-6.5 10-6.5S22 12 22 12s-4 6.5-10 6.5S2 12 2 12z" />
      <circle cx="12" cy="12" r="3.1" fill="rgba(0,0,0,0.42)" />
    </>
  ),
  shield: (
    <path d="M12 2.2l8 3v6c0 5-3.6 9.2-8 11-4.4-1.8-8-6-8-11v-6z" />
  ),
  cloud: (
    <path d="M7 18.5a4.3 4.3 0 0 1-.5-8.6A5.2 5.2 0 0 1 16.3 9 3.7 3.7 0 0 1 17.2 18.5z" />
  ),
  sun: (
    <>
      <circle cx="12" cy="12" r="4.6" />
      <g stroke="currentColor" strokeWidth="1.9" strokeLinecap="round">
        <path d="M12 1.5v3M12 19.5v3M1.5 12h3M19.5 12h3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M19.8 4.2l-2.1 2.1M6.3 17.7l-2.1 2.1" />
      </g>
    </>
  ),
  moon: (
    <path d="M20.5 14.3A8.3 8.3 0 1 1 9.7 3.5a6.3 6.3 0 0 0 10.8 10.8z" />
  ),
  rocket: (
    <>
      <path d="M12 2c3 2.2 4.8 6 4.8 10.2L15 15.5H9L7.2 12.2C7.2 8 9 4.2 12 2z" />
      <g stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinecap="round" strokeLinejoin="round">
        <path d="M7.4 14.5L5 17l3.4-.6M16.6 14.5L19 17l-3.4-.6" />
      </g>
      <circle cx="12" cy="9" r="1.7" fill="rgba(0,0,0,0.35)" />
    </>
  ),
  dot: <circle cx="12" cy="12" r="5.2" />,
};

// LLM slug variants → our canonical glyph. Keeps a near-miss from falling back
// to a bland dot.
const ALIASES: Record<string, GlyphKind> = {
  people: "person", human: "person", humans: "person", voter: "person",
  voters: "person", citizen: "person", user: "person", users: "person",
  customer: "person", worker: "person", soldier: "person", crowd: "person",
  vehicle: "car", driver: "car", drivers: "car", truck: "car", taxi: "car",
  money: "coin", dollar: "coin", dollars: "coin", cash: "coin", gold: "coin",
  token: "coin", bitcoin: "coin", payment: "coin",
  mind: "brain", thought: "brain", cognition: "brain",
  cell: "neuron", synapse: "neuron", node: "neuron",
  electron: "atom", molecule: "atom", nucleus: "atom", particle: "atom",
  chemical: "flask", gene: "dna", genome: "dna", chromosome: "dna",
  starlight: "star",
  world: "planet", earth: "planet", orbit: "planet",
  cog: "gear", machine: "gear", engine: "gear", mechanism: "gear",
  document: "file", record: "file", records: "file", paper: "file",
  row: "file", rows: "file", page: "file", letter: "file",
  city: "building", house: "building", home: "building", office: "building",
  bank: "building", factory: "building", tower: "building",
  idea: "bulb", innovation: "bulb",
  knowledge: "book", library: "book", study: "book",
  energy: "bolt", power: "bolt", spark: "bolt", electric: "bolt",
  water: "droplet", drop: "droplet", oil: "droplet", blood: "droplet",
  computer: "server", machine_rack: "server",
  data: "database", storage: "database", disk: "database",
  package: "box", crate: "box", supply: "box", cargo: "box", block: "box",
  love: "heart", life: "heart", patient: "heart",
  forest: "tree", plant: "tree", nature: "tree", crop: "leaf", foliage: "leaf",
  time: "clock", hour: "clock", deadline: "clock",
  pass: "ticket", vote_ticket: "ticket",
  message: "request", packet: "request", query: "request", api_call: "request",
  // science / space
  photon: "wave", photons: "wave", light: "wave", lightwave: "wave",
  signal: "wave", signals: "wave", sound: "wave", soundwave: "wave",
  radiation: "wave", wavelength: "wave", frequency: "wave", ray: "wave", rays: "wave",
  pulse: "wave", radio: "wave", microwave: "wave",
  galaxy: "star", galaxies: "star", comet: "star", meteor: "star", sunlight: "star",
  probe: "satellite", spacecraft: "satellite", satellites: "satellite", orbiter: "satellite",
  solar: "sun", sunbeam: "sun", sun: "sun", lunar: "moon", moon: "moon",
  // biology / health
  microbe: "virus", bacteria: "virus", bacterium: "virus", germ: "virus",
  pathogen: "virus", infection: "virus", antigen: "virus", microorganism: "virus",
  drug: "pill", dose: "pill", medicine: "pill", tablet: "pill", capsule: "pill", vaccine: "pill",
  species: "fish", flock: "bird", birds: "bird", migration: "bird",
  // tech / physics
  transistor: "chip", semiconductor: "chip", microchip: "chip", processor: "chip",
  circuit: "chip", silicon: "chip",
  // energy / nature / security
  fire: "flame", wildfire: "flame", heat: "flame", combustion: "flame",
  weather: "cloud", storm: "cloud", vapor: "cloud",
  defense: "shield", security: "shield", antivirus: "shield", protection: "shield", firewall: "shield",
  viewer: "eye", observer: "eye", witness: "eye", camera: "eye", lens: "eye",
  telescope: "eye", surveillance: "eye",
  launch: "rocket", missile: "rocket", spaceship: "rocket",
};

export const resolveGlyph = (name: string | undefined | null): GlyphKind => {
  const key = (name ?? "").toLowerCase().trim().replace(/\s+/g, "_");
  if (key in GLYPH_PATHS) return key as GlyphKind;
  if (key in ALIASES) return ALIASES[key];
  // strip a trailing plural 's' and retry
  const sing = key.replace(/s$/, "");
  if (sing in GLYPH_PATHS) return sing as GlyphKind;
  if (sing in ALIASES) return ALIASES[sing];
  return "dot";
};

export const Glyph: React.FC<{ kind: GlyphKind; size: number; color: string; style?: React.CSSProperties }> = ({
  kind,
  size,
  color,
  style,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    style={{ color, display: "block", ...style }}
  >
    {GLYPH_PATHS[kind] ?? GLYPH_PATHS.dot}
  </svg>
);

// ---------------------------------------------------------------------------
// Deterministic helpers (shared by the formation engine). No Math.random —
// every frame must be reproducible for headless rendering.
// ---------------------------------------------------------------------------
export const hash01 = (i: number): number => {
  const x = Math.sin(i * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

// Clamped interpolate — the house smoothstep.
import { interpolate } from "remotion";
export const smooth = (a: number, b: number, x: number): number =>
  interpolate(x, [a, b], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
