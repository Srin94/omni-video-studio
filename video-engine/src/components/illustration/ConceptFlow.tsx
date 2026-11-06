import React from "react";
import { interpolate, spring } from "remotion";
import * as Lucide from "lucide-react";
import type { ArchetypeTheme } from "../../styles/archetypes";
import { HIGHLIGHT } from "../../styles/archetypes";
import type { ConceptFlowSpec, FlowNode } from "../../types/schema";
import { smooth } from "./glyphs";

// Concept flow diagram: tier-based nodes (tier = column, so it reads left→right)
// joined by cubic-bézier edges with packets streaming along them — the "explain
// the flow while talking" surface. Node icons come from lucide-react by name.

const PACKET_OFFSETS = [0, 0.22, 0.44, 0.66, 0.88];

const pascal = (s: string): string =>
  (s || "")
    .split(/[^a-zA-Z0-9]+/)
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join("");

type IconComp = React.ComponentType<{ size?: number; color?: string; strokeWidth?: number }>;
const L = Lucide as unknown as Record<string, IconComp | undefined>;

// Keyword → a KNOWN-GOOD lucide icon. Scanned when an exact name doesn't resolve,
// so a near-miss ("mirror", "ccd sensor", "the model") still gets an on-topic icon
// instead of a blank. Order matters: more specific keywords first.
const ICON_KEYWORDS: [string, string][] = [
  ["telescop", "Telescope"], ["scope", "Telescope"], ["satell", "Satellite"],
  ["orbit", "Orbit"], ["planet", "Orbit"], ["rocket", "Rocket"], ["launch", "Rocket"],
  ["spacecraft", "Rocket"], ["galax", "Star"], ["star", "Star"], ["solar", "Sun"],
  ["sun", "Sun"], ["moon", "Moon"], ["mirror", "Aperture"], ["lens", "Aperture"],
  ["optic", "Aperture"], ["apertur", "Aperture"], ["focus", "Focus"],
  ["photon", "Sparkles"], ["light", "Sparkles"], ["ray", "Sparkles"],
  ["wave", "Radio"], ["signal", "Radio"], ["radio", "Radio"], ["sensor", "Radio"],
  ["detect", "Camera"], ["camera", "Camera"], ["ccd", "Camera"], ["image", "Image"],
  ["eye", "Eye"], ["observ", "Eye"], ["neur", "Brain"], ["brain", "Brain"],
  ["model", "Brain"], ["learn", "Brain"], ["cpu", "Cpu"], ["comput", "Cpu"],
  ["process", "Cpu"], ["chip", "Cpu"], ["silicon", "Cpu"], ["transistor", "Cpu"],
  ["databas", "Database"], ["datastore", "Database"], ["storage", "HardDrive"],
  ["disk", "HardDrive"], ["data", "Database"], ["server", "Server"], ["backend", "Server"],
  ["cloud", "Cloud"], ["internet", "Globe"], ["web", "Globe"], ["globe", "Globe"],
  ["network", "Network"], ["router", "GitMerge"], ["people", "Users"], ["user", "User"],
  ["client", "User"], ["person", "User"], ["human", "User"], ["voter", "Users"],
  ["queue", "List"], ["buffer", "List"], ["list", "List"], ["cache", "Zap"],
  ["energy", "Zap"], ["power", "Zap"], ["electric", "Zap"], ["money", "Banknote"],
  ["cost", "Banknote"], ["price", "Banknote"], ["bank", "Landmark"], ["atom", "Atom"],
  ["molecul", "Atom"], ["electron", "Atom"], ["nucleus", "Atom"], ["gene", "Dna"],
  ["dna", "Dna"], ["genom", "Dna"], ["cell", "Microscope"], ["microb", "Microscope"],
  ["bacteri", "Bug"], ["virus", "Bug"], ["lab", "FlaskConical"], ["chemical", "FlaskConical"],
  ["fire", "Flame"], ["flame", "Flame"], ["heat", "Flame"], ["combust", "Flame"],
  ["ocean", "Waves"], ["sea", "Waves"], ["water", "Droplet"], ["fluid", "Droplet"],
  ["input", "LogIn"], ["source", "LogIn"], ["entry", "LogIn"], ["output", "LogOut"],
  ["result", "Flag"], ["predict", "Flag"], ["start", "Play"], ["begin", "Play"],
  ["end", "Flag"], ["goal", "Flag"], ["time", "Clock"], ["factor", "Factory"],
  ["build", "Building2"], ["city", "Building2"], ["house", "Home"], ["home", "Home"],
  ["car", "Car"], ["vehicle", "Car"], ["traffic", "Car"], ["road", "Route"],
  ["route", "Route"], ["bridge", "GitMerge"], ["merge", "GitMerge"], ["split", "GitBranch"],
  ["branch", "GitBranch"], ["book", "BookOpen"], ["idea", "Lightbulb"], ["secur", "Shield"],
  ["shield", "Shield"], ["defen", "Shield"], ["mail", "Mail"], ["message", "Mail"],
  ["box", "Package"], ["packet", "Package"], ["parcel", "Package"], ["node", "CircleDot"],
  ["signal_v", "Activity"], ["activ", "Activity"],
];

const iconFor = (name?: string): IconComp => {
  const raw = (name || "").trim();
  if (raw) {
    const exact = L[pascal(raw)];
    if (exact) return exact; // the model named a real lucide icon
    const low = raw.toLowerCase();
    for (const [kw, icon] of ICON_KEYWORDS) {
      if (low.includes(kw)) {
        const C = L[icon];
        if (C) return C;
      }
    }
  }
  return L.CircleDot || Lucide.Circle; // guaranteed non-blank fallback
};

const edgeColor = (c: string | undefined | null, theme: ArchetypeTheme): string => {
  if (!c) return theme.accent;
  if (c.startsWith("#")) return c;
  return (HIGHLIGHT as Record<string, string>)[c] ?? theme.accent;
};

const bezier = (
  t: number,
  p0: [number, number],
  c1: [number, number],
  c2: [number, number],
  p3: [number, number],
): [number, number] => {
  const u = 1 - t;
  const a = u * u * u;
  const b = 3 * u * u * t;
  const d = 3 * u * t * t;
  const e = t * t * t;
  return [
    a * p0[0] + b * c1[0] + d * c2[0] + e * p3[0],
    a * p0[1] + b * c1[1] + d * c2[1] + e * p3[1],
  ];
};

interface Placed {
  node: FlowNode;
  x: number;
  y: number;
  w: number;
  h: number;
  index: number;
}

export const ConceptFlow: React.FC<{
  spec: ConceptFlowSpec;
  theme: ArchetypeTheme;
  localFrame: number;
  fps: number;
  width: number;
  height: number;
  portrait: boolean;
}> = ({ spec, theme, localFrame, fps, width, height, portrait }) => {
  const nodes = spec.nodes ?? [];
  const edges = spec.edges ?? [];
  if (nodes.length === 0) return null;

  // Dark-stage ink (see GlyphWorld) — chrome stays readable on any archetype.
  const INK = "#EAF1FB";
  const MUTED = "#90A2B6";
  const CARD = "rgba(12,20,34,0.72)";
  const BORDER = "rgba(255,255,255,0.16)";

  // Orientation-aware layout: the flow runs along the LONG axis so it fills the
  // frame — left→right in landscape, top→bottom in a 9:16 portrait Short. This is
  // the key to portrait: a horizontal flow would cram into a thin band and clip.
  const vertical = portrait;
  const tiers = Array.from(new Set(nodes.map((n) => n.tier ?? 1))).sort((a, b) => a - b);
  const colCount = tiers.length;
  const maxPerTier = Math.max(1, ...tiers.map((t) => nodes.filter((n) => (n.tier ?? 1) === t).length));

  // main axis = the tier direction; cross axis = spread within a tier.
  const mainStart = vertical ? height * 0.25 : width * 0.08;
  // In portrait, stop the flow above the karaoke subtitle band (bottom ~120px)
  // so the last node never collides with the caption.
  const mainEnd = vertical ? height * 0.8 : width * 0.92;
  const crossMargin = (vertical ? width : height) * (vertical ? 0.06 : 0.1);
  const crossLo = vertical ? crossMargin : height * 0.28;
  const crossHi = vertical ? width - crossMargin : height * 0.82;
  const crossSpan = crossHi - crossLo;
  const mainGap = colCount > 1 ? (mainEnd - mainStart) / (colCount - 1) : 0;

  const nodeW = vertical
    ? Math.min(340, crossSpan / maxPerTier - 22)
    : Math.min(260, (width * 0.84) / Math.max(colCount, 1) - 28);
  const nodeH = vertical ? 116 : 104;

  const placed: Placed[] = [];
  let idx = 0;
  tiers.forEach((tier, ti) => {
    const inTier = nodes.filter((n) => (n.tier ?? 1) === tier);
    const mainPos = colCount > 1 ? mainStart + ti * mainGap : (mainStart + mainEnd) / 2;
    const crossGap = crossSpan / (inTier.length + 1);
    inTier.forEach((node, ri) => {
      const crossPos = crossLo + crossGap * (ri + 1);
      placed.push({
        node,
        x: vertical ? crossPos : mainPos,
        y: vertical ? mainPos : crossPos,
        w: nodeW,
        h: nodeH,
        index: idx,
      });
      idx += 1;
    });
  });
  const byId = new Map(placed.map((p) => [p.node.id, p]));
  const focusId = spec.focus_node_id ?? null;

  const titleIn = smooth(2, 16, localFrame);
  const capIn = smooth(20, 36, localFrame);

  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
      {/* Title + caption (top) */}
      {spec.title || spec.caption ? (
        <div style={{ position: "absolute", top: portrait ? 56 : 80, left: portrait ? 56 : 80, right: 80, opacity: titleIn, zIndex: 5 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
            <div style={{ width: 9, height: 9, borderRadius: "50%", background: theme.accent2, boxShadow: `0 0 14px ${theme.accent2}` }} />
            <div style={{ fontFamily: theme.fontMono, fontSize: 18, letterSpacing: 5, textTransform: "uppercase", color: MUTED }}>
              HOW IT FLOWS
            </div>
          </div>
          {spec.title ? (
            <div style={{ fontFamily: theme.fontHeading, fontSize: portrait ? 52 : 66, fontWeight: 800, color: INK, lineHeight: 1.02, letterSpacing: -1, textShadow: "0 2px 24px rgba(0,0,0,0.5)" }}>
              {spec.title}
            </div>
          ) : null}
          {spec.caption ? (
            <div
              style={{
                marginTop: 14,
                fontFamily: theme.fontHeading,
                fontSize: portrait ? 23 : 27,
                color: MUTED,
                maxWidth: portrait ? "88%" : "62%",
                lineHeight: 1.3,
                opacity: capIn,
                transform: `translateY(${interpolate(capIn, [0, 1], [10, 0])}px)`,
              }}
            >
              {spec.caption}
            </div>
          ) : null}
        </div>
      ) : null}

      {/* Edges + packets */}
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} style={{ position: "absolute", inset: 0 }}>
        {edges.map((e, i) => {
          const s = byId.get(e.source);
          const t = byId.get(e.target);
          if (!s || !t) return null;
          let p0: [number, number], c1: [number, number], c2: [number, number], p3: [number, number];
          if (vertical) {
            const sx = s.x, sy = s.y + s.h / 2; // bottom of source
            const tx = t.x, ty = t.y - t.h / 2; // top of target
            const dy = Math.max(50, ty - sy);
            p0 = [sx, sy]; c1 = [sx, sy + dy * 0.5]; c2 = [tx, ty - dy * 0.5]; p3 = [tx, ty];
          } else {
            const sx = s.x + s.w / 2, sy = s.y; // right of source
            const tx = t.x - t.w / 2, ty = t.y; // left of target
            const dx = Math.max(50, tx - sx);
            p0 = [sx, sy]; c1 = [sx + dx * 0.5, sy]; c2 = [tx - dx * 0.5, ty]; p3 = [tx, ty];
          }
          const d = `M${p0[0]},${p0[1]} C${c1[0]},${c1[1]} ${c2[0]},${c2[1]} ${p3[0]},${p3[1]}`;
          const col = edgeColor(e.color, theme);
          const drawn = smooth(8 + i * 3, 8 + i * 3 + 20, localFrame); // draw-on
          const dash = 2000;
          const focusTouch = !focusId || e.source === focusId || e.target === focusId;
          const o = focusTouch ? 1 : 0.28;
          return (
            <g key={`e${i}`} style={{ opacity: o }}>
              <path d={d} fill="none" stroke={col} strokeWidth={9} strokeOpacity={0.12} strokeLinecap="round" />
              <path
                d={d}
                fill="none"
                stroke={col}
                strokeWidth={2.4}
                strokeLinecap="round"
                strokeDasharray={dash}
                strokeDashoffset={dash * (1 - drawn)}
                style={{ filter: `drop-shadow(0 0 5px ${col})` }}
              />
              {e.animate !== false && drawn > 0.9
                ? PACKET_OFFSETS.map((off, pi) => {
                    const tt = (((localFrame * 0.011 + off) % 1) + 1) % 1;
                    const [px, py] = bezier(tt, p0, c1, c2, p3);
                    const fade = Math.min(1, Math.min(tt, 1 - tt) * 8);
                    return (
                      <g key={`p${pi}`} style={{ opacity: fade }}>
                        <circle cx={px} cy={py} r={11} fill={col} opacity={0.16} />
                        <circle cx={px} cy={py} r={4.5} fill={col} />
                      </g>
                    );
                  })
                : null}
              {e.label && focusTouch ? (
                <text
                  x={(p0[0] + p3[0]) / 2}
                  y={(p0[1] + p3[1]) / 2 - 12}
                  textAnchor="middle"
                  fill={MUTED}
                  style={{ fontFamily: theme.fontMono, fontSize: 17, opacity: drawn }}
                >
                  {e.label}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>

      {/* Nodes */}
      {placed.map((p) => {
        const enter = spring({ frame: localFrame - 6 - p.index * 5, fps, config: { damping: 16, stiffness: 150 } });
        const sc = 0.9 + enter * 0.1;
        const rise = (1 - enter) * 18;
        const isFocus = focusId ? p.node.id === focusId : !!p.node.highlight;
        const dim = focusId && p.node.id !== focusId ? 0.55 : 1;
        const col = isFocus ? theme.accent : INK;
        const ring = isFocus ? theme.accent : BORDER;
        const pulse = isFocus ? 0.5 + 0.5 * Math.sin(localFrame * 0.11) : 0;
        const Icon = iconFor(p.node.icon);
        return (
          <div
            key={p.node.id}
            style={{
              position: "absolute",
              left: p.x - p.w / 2,
              top: p.y - p.h / 2,
              width: p.w,
              height: p.h,
              opacity: enter * dim,
              transform: `translateY(${rise}px) scale(${sc})`,
              background: CARD,
              border: `1.5px solid ${ring}`,
              borderRadius: 16,
              display: "flex",
              alignItems: "center",
              gap: 14,
              padding: "0 18px",
              boxShadow: isFocus
                ? `0 0 ${18 + pulse * 18}px ${theme.accent}${Math.round(40 + pulse * 40).toString(16).padStart(2, "0")}, 0 12px 40px rgba(0,0,0,0.4)`
                : "0 10px 34px rgba(0,0,0,0.32)",
            }}
          >
            <div
              style={{
                flex: "0 0 auto",
                width: 52,
                height: 52,
                borderRadius: 12,
                background: `${col}1a`,
                border: `1px solid ${col}55`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                filter: isFocus ? `drop-shadow(0 0 10px ${theme.accent})` : undefined,
              }}
            >
              <Icon size={28} color={col} strokeWidth={2} />
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontFamily: theme.fontHeading, fontSize: portrait ? 22 : 24, fontWeight: 700, color: INK, lineHeight: 1.14, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                {p.node.label}
              </div>
              {p.node.sublabel ? (
                <div style={{ fontFamily: theme.fontMono, fontSize: 14, letterSpacing: 1, textTransform: "uppercase", color: MUTED, marginTop: 3 }}>
                  {p.node.sublabel}
                </div>
              ) : null}
            </div>
          </div>
        );
      })}

    </div>
  );
};
