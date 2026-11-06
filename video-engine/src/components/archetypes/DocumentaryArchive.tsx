import React from "react";
import { interpolate } from "remotion";
import type { SceneSpec } from "../../types/schema";
import type { ArchetypeTheme } from "../../styles/archetypes";
import { VisualElementStack } from "../VisualElements";
import { HudTelemetry } from "../HudTelemetry";

// Warm archival dossier: aged paper, grain, an ink "stamp" chapter badge and a
// typewriter title. Best for history, origins and human stories.

export const DocumentaryArchive: React.FC<{
  scene: SceneSpec;
  theme: ArchetypeTheme;
  localFrame: number;
  fps: number;
  portrait: boolean;
}> = ({ scene, theme, localFrame, fps, portrait }) => {
  const reveal = interpolate(localFrame, [0, 18], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      {/* Grain overlay */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: 0.08,
          backgroundImage:
            "repeating-radial-gradient(circle at 20% 30%, #000 0, #000 0.6px, transparent 1.2px, transparent 3px)",
          pointerEvents: "none",
        }}
      />
      {/* Stamp badge */}
      <div
        style={{
          display: "inline-block",
          transform: "rotate(-6deg)",
          border: `3px solid ${theme.accent}`,
          color: theme.accent,
          fontFamily: theme.fontMono,
          fontWeight: 700,
          letterSpacing: 4,
          fontSize: 22,
          padding: "8px 18px",
          borderRadius: 6,
          opacity: reveal,
        }}
      >
        ARCHIVE № {String(scene.scene_id).padStart(2, "0")}
      </div>

      {/* Typewriter-style chapter title */}
      <div
        style={{
          fontFamily: theme.fontDisplay,
          fontSize: portrait ? 72 : 88,
          fontWeight: 800,
          color: theme.textPrimary,
          marginTop: 22,
          maxWidth: "90%",
          lineHeight: 1.02,
          clipPath: `inset(0 ${100 - reveal * 100}% 0 0)`,
          borderRight: reveal < 1 ? `4px solid ${theme.accent}` : "none",
        }}
      >
        {scene.chapter_title}
      </div>

      <div style={{ marginTop: 40 }}>
        <VisualElementStack elements={scene.visual_elements} theme={theme} localFrame={localFrame} fps={fps} />
      </div>

      <div style={{ position: "absolute", right: 0, bottom: portrait ? 0 : 8 }}>
        <HudTelemetry metrics={scene.hud_metrics} theme={theme} localFrame={localFrame} fps={fps} vertical={portrait} />
      </div>
    </div>
  );
};
