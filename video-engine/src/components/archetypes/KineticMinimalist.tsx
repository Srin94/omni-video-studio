import React from "react";
import { interpolate, spring } from "remotion";
import type { SceneSpec } from "../../types/schema";
import type { ArchetypeTheme } from "../../styles/archetypes";
import { VisualElementStack } from "../VisualElements";
import { HudTelemetry } from "../HudTelemetry";

// Stark, high-contrast kinetic typography. A giant chapter number slams in, the
// title sits in a bold Swiss grid. Best for one shocking statistic or a sharp
// either/or contrast.

export const KineticMinimalist: React.FC<{
  scene: SceneSpec;
  theme: ArchetypeTheme;
  localFrame: number;
  fps: number;
  portrait: boolean;
}> = ({ scene, theme, localFrame, fps, portrait }) => {
  const slam = spring({ frame: localFrame, fps, config: { damping: 14, stiffness: 160 } });
  const titleIn = interpolate(localFrame, [6, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 28 }}>
        <div
          style={{
            fontFamily: theme.fontHeading,
            fontSize: portrait ? 180 : 240,
            fontWeight: 800,
            lineHeight: 0.8,
            color: theme.accent,
            transform: `scale(${interpolate(slam, [0, 1], [1.4, 1])})`,
            transformOrigin: "left top",
            opacity: slam,
          }}
        >
          {String(scene.scene_id).padStart(2, "0")}
        </div>
        <div
          style={{
            fontFamily: theme.fontHeading,
            fontSize: portrait ? 60 : 72,
            fontWeight: 800,
            letterSpacing: -1,
            textTransform: "uppercase",
            color: theme.textPrimary,
            marginTop: 18,
            opacity: titleIn,
            transform: `translateX(${interpolate(titleIn, [0, 1], [40, 0])}px)`,
            maxWidth: "70%",
            lineHeight: 0.98,
          }}
        >
          {scene.chapter_title}
        </div>
      </div>

      <div style={{ height: 8, background: theme.accent, width: `${interpolate(slam, [0, 1], [0, 100])}%`, marginTop: 24, marginBottom: 36 }} />

      <VisualElementStack elements={scene.visual_elements} theme={theme} localFrame={localFrame} fps={fps} />

      <div style={{ position: "absolute", right: 0, bottom: portrait ? 0 : 8 }}>
        <HudTelemetry metrics={scene.hud_metrics} theme={theme} localFrame={localFrame} fps={fps} vertical={portrait} />
      </div>
    </div>
  );
};
