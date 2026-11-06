import React from "react";
import { interpolate } from "remotion";
import type { SceneSpec } from "../../types/schema";
import type { ArchetypeTheme } from "../../styles/archetypes";
import { VisualElementStack } from "../VisualElements";
import { HudTelemetry } from "../HudTelemetry";

// Cinematic charcoal with 2.39:1 letterbox accents and a floating timeline
// breadcrumb. Best for chronology, investigations and cause-and-effect.

export const NarrativeStoryboard: React.FC<{
  scene: SceneSpec;
  theme: ArchetypeTheme;
  localFrame: number;
  fps: number;
  portrait: boolean;
  sceneCount: number;
}> = ({ scene, theme, localFrame, fps, portrait, sceneCount }) => {
  const reveal = interpolate(localFrame, [0, 18], [0, 1], { extrapolateRight: "clamp" });
  const progress = sceneCount > 1 ? (scene.scene_id - 1) / (sceneCount - 1) : 0;

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      {/* Timeline breadcrumb */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, opacity: reveal }}>
        <div style={{ flex: 1, height: 3, background: theme.cardBorder, position: "relative" }}>
          <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${progress * 100}%`, background: theme.accent }} />
          <div
            style={{
              position: "absolute",
              left: `${progress * 100}%`,
              top: "50%",
              transform: "translate(-50%, -50%)",
              width: 16,
              height: 16,
              borderRadius: "50%",
              background: theme.accent,
              boxShadow: `0 0 14px ${theme.accent}`,
            }}
          />
        </div>
        <div style={{ fontFamily: theme.fontMono, fontSize: 18, color: theme.textMuted }}>
          CH {String(scene.scene_id).padStart(2, "0")}/{String(sceneCount).padStart(2, "0")}
        </div>
      </div>

      <div
        style={{
          fontFamily: theme.fontDisplay,
          fontSize: portrait ? 64 : 84,
          fontWeight: 800,
          color: theme.textPrimary,
          marginTop: 28,
          letterSpacing: -0.5,
          opacity: reveal,
          transform: `translateY(${interpolate(reveal, [0, 1], [18, 0])}px)`,
          maxWidth: "90%",
          lineHeight: 1.02,
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
