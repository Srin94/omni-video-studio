import React from "react";
import { interpolate, spring } from "remotion";
import type { SceneSpec } from "../types/schema";
import type { ArchetypeTheme } from "../styles/archetypes";
import { HIGHLIGHT } from "../styles/archetypes";

// The overlay for scenes that HAVE topic imagery. Deliberately restrained — the
// photo is the star — so it never becomes "a slide on top of a picture": a
// lower-third chapter title, a slim HUD readout, and at most one floating glass
// fact card. Everything has a shadow so it reads on any image.

const shadow = "0 2px 18px rgba(0,0,0,0.75)";

const HudChips: React.FC<{ scene: SceneSpec; theme: ArchetypeTheme; o: number }> = ({ scene, theme, o }) => {
  const metrics = (scene.hud_metrics ?? []).slice(0, 3);
  if (metrics.length === 0) return null;
  return (
    <div style={{ display: "flex", gap: 14, flexWrap: "wrap", opacity: o }}>
      {metrics.map((m, i) => (
        <div
          key={i}
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: 10,
            padding: "10px 16px",
            borderRadius: 10,
            background: "rgba(8,12,20,0.46)",
            border: `1px solid ${theme.accent}44`,
            backdropFilter: "blur(7px)",
          }}
        >
          <span style={{ fontFamily: theme.fontMono, fontSize: 16, letterSpacing: 2, color: theme.textMuted, textTransform: "uppercase" }}>
            {m.label}
          </span>
          <span style={{ fontFamily: theme.fontDisplay, fontSize: 26, fontWeight: 800, color: "#fff", textShadow: shadow }}>
            {m.value}
          </span>
          {m.delta ? (
            <span style={{ fontFamily: theme.fontMono, fontSize: 15, color: theme.accent2, fontWeight: 700 }}>{m.delta}</span>
          ) : null}
        </div>
      ))}
    </div>
  );
};

const GlassFact: React.FC<{ scene: SceneSpec; theme: ArchetypeTheme; rise: number }> = ({ scene, theme, rise }) => {
  const el = (scene.visual_elements ?? [])[0];
  if (!el) return null;
  const accent = HIGHLIGHT[el.highlight_color] ?? theme.accent;
  const big = el.element_type === "stat_card";
  return (
    <div
      style={{
        maxWidth: "42%",
        padding: "22px 26px",
        borderRadius: 16,
        background: "rgba(8,12,20,0.52)",
        border: `1px solid ${accent}66`,
        borderLeft: `6px solid ${accent}`,
        backdropFilter: "blur(10px)",
        boxShadow: "0 18px 50px rgba(0,0,0,0.45)",
        transform: `translateX(${interpolate(rise, [0, 1], [40, 0])}px)`,
        opacity: rise,
      }}
    >
      {el.badge ? (
        <div style={{ fontFamily: theme.fontMono, fontSize: 14, letterSpacing: 2, textTransform: "uppercase", color: theme.textMuted, marginBottom: 8 }}>
          {el.badge}
        </div>
      ) : null}
      <div
        style={{
          fontFamily: big ? theme.fontDisplay : theme.fontHeading,
          fontSize: big ? 60 : 32,
          fontWeight: 800,
          color: big ? accent : "#fff",
          lineHeight: 1.05,
          textShadow: shadow,
        }}
      >
        {el.headline}
      </div>
      <div style={{ fontFamily: theme.fontHeading, fontSize: 22, color: "#D7DEE8", marginTop: 10, textShadow: shadow }}>
        {el.subtext}
      </div>
    </div>
  );
};

export const CinematicOverlay: React.FC<{
  scene: SceneSpec;
  theme: ArchetypeTheme;
  localFrame: number;
  fps: number;
  portrait: boolean;
}> = ({ scene, theme, localFrame, fps, portrait }) => {
  const o = interpolate(localFrame, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  const rise = spring({ frame: localFrame - 4, fps, config: { damping: 18, stiffness: 110 } });
  const pad = portrait ? 56 : 84;

  return (
    <div style={{ position: "absolute", inset: 0, padding: pad, zIndex: 4 }}>
      {/* Floating fact, upper-right */}
      <div style={{ position: "absolute", top: pad + 70, right: pad, display: "flex", justifyContent: "flex-end" }}>
        <GlassFact scene={scene} theme={theme} rise={rise} />
      </div>

      {/* Lower-third chapter title + HUD, sitting above the caption bar */}
      <div style={{ position: "absolute", left: pad, right: pad, bottom: portrait ? 230 : 190 }}>
        <div
          style={{
            display: "inline-block",
            width: 64,
            height: 5,
            borderRadius: 3,
            background: theme.accent,
            boxShadow: `0 0 16px ${theme.accent}`,
            marginBottom: 18,
            transform: `scaleX(${o})`,
            transformOrigin: "left",
          }}
        />
        <div
          style={{
            fontFamily: theme.fontDisplay,
            fontSize: portrait ? 58 : 82,
            fontWeight: 800,
            color: "#fff",
            letterSpacing: -0.5,
            lineHeight: 1.0,
            textShadow: shadow,
            maxWidth: "80%",
            opacity: o,
            transform: `translateY(${interpolate(rise, [0, 1], [20, 0])}px)`,
          }}
        >
          {scene.chapter_title}
        </div>
        <div style={{ marginTop: 20 }}>
          <HudChips scene={scene} theme={theme} o={o} />
        </div>
      </div>
    </div>
  );
};
