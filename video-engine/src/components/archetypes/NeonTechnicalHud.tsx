import React from "react";
import { interpolate } from "remotion";
import type { SceneSpec } from "../../types/schema";
import type { ArchetypeTheme } from "../../styles/archetypes";
import { VisualElementStack } from "../VisualElements";
import { HudTelemetry } from "../HudTelemetry";

// Dark oscilloscope console: a live signal line sweeps across a glowing grid,
// telemetry sits up top. Best for mechanisms, systems and "how it works".

const Oscilloscope: React.FC<{ frame: number; theme: ArchetypeTheme; width: number }> = ({ frame, theme, width }) => {
  const pts: string[] = [];
  const h = 90;
  for (let x = 0; x <= width; x += 8) {
    const y =
      h / 2 +
      Math.sin((x + frame * 6) / 42) * 22 +
      Math.sin((x + frame * 3) / 17) * 8;
    pts.push(`${x},${y.toFixed(1)}`);
  }
  return (
    <svg width="100%" height={h} viewBox={`0 0 ${width} ${h}`} preserveAspectRatio="none" style={{ display: "block" }}>
      <polyline points={pts.join(" ")} fill="none" stroke={theme.accent} strokeWidth={3} style={{ filter: `drop-shadow(0 0 6px ${theme.accent})` }} />
    </svg>
  );
};

export const NeonTechnicalHud: React.FC<{
  scene: SceneSpec;
  theme: ArchetypeTheme;
  localFrame: number;
  fps: number;
  portrait: boolean;
}> = ({ scene, theme, localFrame, fps, portrait }) => {
  const reveal = interpolate(localFrame, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 14, opacity: reveal }}>
        <div style={{ width: 12, height: 12, borderRadius: "50%", background: theme.accent2, boxShadow: `0 0 14px ${theme.accent2}` }} />
        <div style={{ fontFamily: theme.fontMono, fontSize: 22, letterSpacing: 4, color: theme.textMuted, textTransform: "uppercase" }}>
          SYS://TELEMETRY · CH-{String(scene.scene_id).padStart(2, "0")}
        </div>
      </div>

      <div
        style={{
          fontFamily: theme.fontHeading,
          fontSize: portrait ? 60 : 72,
          fontWeight: 800,
          color: theme.textPrimary,
          marginTop: 16,
          letterSpacing: -0.5,
          opacity: reveal,
          maxWidth: "92%",
          lineHeight: 1,
        }}
      >
        {scene.chapter_title}
      </div>

      <div style={{ marginTop: 20, border: `1px solid ${theme.cardBorder}`, borderRadius: 12, padding: 12, background: "rgba(8,16,28,0.5)" }}>
        <Oscilloscope frame={localFrame} theme={theme} width={portrait ? 900 : 1100} />
      </div>

      <div style={{ marginTop: 22 }}>
        <HudTelemetry metrics={scene.hud_metrics} theme={theme} localFrame={localFrame} fps={fps} />
      </div>

      <div style={{ marginTop: 24 }}>
        <VisualElementStack elements={scene.visual_elements} theme={theme} localFrame={localFrame} fps={fps} />
      </div>
    </div>
  );
};
