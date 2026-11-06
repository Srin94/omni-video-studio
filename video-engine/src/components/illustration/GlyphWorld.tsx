import React from "react";
import { interpolate } from "remotion";
import type { ArchetypeTheme } from "../../styles/archetypes";
import { HIGHLIGHT } from "../../styles/archetypes";
import type { GlyphWorldSpec } from "../../types/schema";
import { Glyph, resolveGlyph, smooth } from "./glyphs";
import { computeCrowd, type CrowdColors, type CrowdInput, type Dims } from "./formations";

// The "living world" scene: draws the countable noun of the narration as a crowd
// of glowing glyphs moving in a formation that matches the verb, with a live
// count that ticks up and a one-line story-beat caption. This is the primary
// engagement surface — the picture IS the explanation.

const compact = (n: number): string => {
  if (n >= 1e9) return `${(n / 1e9).toFixed(n >= 1e10 ? 0 : 1).replace(/\.0$/, "")}B`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(n >= 1e7 ? 0 : 1).replace(/\.0$/, "")}M`;
  if (n >= 1e3) return Math.round(n).toLocaleString();
  return `${Math.round(n)}`;
};

export const GlyphWorld: React.FC<{
  spec: GlyphWorldSpec;
  theme: ArchetypeTheme;
  localFrame: number;
  fps: number;
  width: number;
  height: number;
  portrait: boolean;
}> = ({ spec, theme, localFrame, width, height, portrait }) => {
  const kind = resolveGlyph(spec.unit_icon);
  const status = spec.status ?? "normal";

  // Dark-stage ink (illustrations always render on a dark canvas), so chrome is
  // readable on any archetype — only the ACCENT comes from the theme.
  const INK = "#EAF1FB";
  const MUTED = "#90A2B6";
  const CARD = "rgba(10,16,26,0.62)";
  const BORDER = "rgba(255,255,255,0.16)";

  const colors: CrowdColors = {
    active: theme.accent,
    idle: MUTED,
    warn: HIGHLIGHT.amber,
    crit: HIGHLIGHT.crimson,
  };
  const litColor = status === "critical" ? colors.crit : status === "warning" ? colors.warn : colors.active;

  // Crowd band: leave room for the headline up top and the caption at the bottom.
  const dims: Dims = {
    W: width,
    H: height,
    top: height * (portrait ? 0.3 : 0.26),
    bottom: height * (portrait ? 0.82 : 0.84),
    portrait,
  };
  const input: CrowdInput = {
    unit_icon: kind,
    formation: spec.formation,
    population: spec.population,
    active_fraction: spec.active_fraction,
    status,
  };
  const crowd = computeCrowd(input, colors, localFrame, dims);

  // Count-up readouts.
  const popNow = Math.round(interpolate(localFrame, [6, 44], [0, crowd.population], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const activeNow = Math.round(interpolate(localFrame, [10, 50], [0, crowd.activeCount], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const headIn = smooth(2, 16, localFrame);
  const capIn = smooth(18, 34, localFrame);

  const pad = portrait ? 56 : 80;
  const crushGlow = status !== "normal" && (spec.formation === "jam" || spec.formation === "rush");
  const statusColor = status === "critical" ? colors.crit : colors.warn;

  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
      {/* Ambient status-tinted wash behind the crowd */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(60% 50% at 50% ${portrait ? 54 : 56}%, ${litColor}${crushGlow ? "22" : "14"} 0%, transparent 70%)`,
        }}
      />

      {/* Gate posts (rush / jam) */}
      {crowd.gate ? (
        <>
          <div
            style={{
              position: "absolute",
              left: crowd.gate.x - 5,
              top: dims.top,
              width: 10,
              height: Math.max(0, crowd.gate.y - crowd.gate.h / 2 - dims.top),
              borderRadius: 5,
              background: statusColor,
              boxShadow: `0 0 26px ${statusColor}`,
              opacity: 0.9,
            }}
          />
          <div
            style={{
              position: "absolute",
              left: crowd.gate.x - 5,
              top: crowd.gate.y + crowd.gate.h / 2,
              width: 10,
              height: Math.max(0, dims.bottom - (crowd.gate.y + crowd.gate.h / 2)),
              borderRadius: 5,
              background: statusColor,
              boxShadow: `0 0 26px ${statusColor}`,
              opacity: 0.9,
            }}
          />
        </>
      ) : null}

      {/* Central hub (scatter / orbit) */}
      {crowd.hub ? (
        <div
          style={{
            position: "absolute",
            left: crowd.hub.x,
            top: crowd.hub.y,
            transform: "translate(-50%,-50%)",
            filter: `drop-shadow(0 0 18px ${theme.accent})`,
          }}
        >
          <Glyph kind={spec.formation === "orbit" ? resolveGlyph(spec.unit_icon) : "server"} size={portrait ? 64 : 76} color={theme.accent} />
        </div>
      ) : null}

      {/* The crowd */}
      {crowd.glyphs.map((g) => (
        <div
          key={g.key}
          style={{
            position: "absolute",
            left: g.x,
            top: g.y,
            transform: "translate(-50%,-50%)",
            opacity: g.opacity,
            filter: g.glow > 0 ? `drop-shadow(0 0 ${7 * g.glow}px ${g.color})` : undefined,
            willChange: "transform",
          }}
        >
          <Glyph kind={kind} size={g.size} color={g.color} />
        </div>
      ))}

      {/* Headline + live count (top) */}
      <div style={{ position: "absolute", top: pad, left: pad, right: pad, opacity: headIn, zIndex: 5 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10 }}>
          <div style={{ width: 9, height: 9, borderRadius: "50%", background: litColor, boxShadow: `0 0 14px ${litColor}` }} />
          <div style={{ fontFamily: theme.fontMono, fontSize: 18, letterSpacing: 5, textTransform: "uppercase", color: MUTED }}>
            {(spec.section_label || spec.formation).toUpperCase()}
          </div>
        </div>
        {spec.headline ? (
          <div
            style={{
              fontFamily: theme.fontHeading,
              fontSize: portrait ? 58 : 76,
              fontWeight: 800,
              color: INK,
              lineHeight: 1.02,
              letterSpacing: -1,
              maxWidth: portrait ? "100%" : "72%",
              textShadow: "0 2px 24px rgba(0,0,0,0.55)",
            }}
          >
            {spec.headline}
          </div>
        ) : null}
        {spec.caption ? (
          <div
            style={{
              marginTop: 14,
              fontFamily: theme.fontHeading,
              fontSize: portrait ? 23 : 27,
              color: MUTED,
              maxWidth: portrait ? "88%" : "60%",
              lineHeight: 1.3,
              opacity: capIn,
              transform: `translateY(${interpolate(capIn, [0, 1], [10, 0])}px)`,
            }}
          >
            {spec.caption}
          </div>
        ) : null}
      </div>

      {/* Live count pill (top-right) */}
      <div
        style={{
          position: "absolute",
          top: pad,
          right: pad,
          padding: "14px 22px",
          borderRadius: 16,
          background: CARD,
          border: `1px solid ${BORDER}`,
          backdropFilter: "blur(6px)",
          textAlign: "right",
          opacity: headIn,
          boxShadow: `0 0 28px ${litColor}22`,
          zIndex: 5,
        }}
      >
        <div style={{ fontFamily: theme.fontDisplay, fontSize: portrait ? 40 : 52, fontWeight: 800, color: theme.accent, lineHeight: 1 }}>
          {compact(popNow)}
        </div>
        <div style={{ fontFamily: theme.fontMono, fontSize: 15, letterSpacing: 2, textTransform: "uppercase", color: MUTED, marginTop: 4 }}>
          {spec.unit_label || "total"}
        </div>
        {crowd.activeCount > 0 && spec.active_label ? (
          <div style={{ fontFamily: theme.fontMono, fontSize: 17, fontWeight: 700, color: litColor, marginTop: 8 }}>
            {compact(activeNow)} {spec.active_label}
          </div>
        ) : null}
      </div>

      {/* Status chip */}
      {status !== "normal" ? (
        <div
          style={{
            position: "absolute",
            top: portrait ? pad + 212 : pad + 168,
            right: pad,
            padding: "7px 16px",
            borderRadius: 999,
            background: `${statusColor}1f`,
            border: `1px solid ${statusColor}`,
            color: statusColor,
            fontFamily: theme.fontMono,
            fontSize: 15,
            fontWeight: 700,
            letterSpacing: 2,
            textTransform: "uppercase",
            opacity: smooth(20, 32, localFrame),
            zIndex: 5,
          }}
        >
          {status === "critical" ? "● CRITICAL" : "▲ WARNING"}
        </div>
      ) : null}

    </div>
  );
};
