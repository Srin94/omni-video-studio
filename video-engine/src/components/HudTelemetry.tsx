import React from "react";
import { interpolate, spring } from "remotion";
import type { DynamicHUDMetric } from "../types/schema";
import type { ArchetypeTheme } from "../styles/archetypes";

// Floating telemetry micro-cards that spring in and reflect scene.hud_metrics.
// Shared by every archetype; positioned by the archetype itself.

const deltaColor = (delta: string | null | undefined, theme: ArchetypeTheme): string => {
  if (!delta) return theme.textMuted;
  const d = delta.toLowerCase();
  if (d.includes("+") || d.includes("up") || d.includes("gain")) return "#34D399";
  if (d.includes("-") || d.includes("fall") || d.includes("down") || d.includes("critical") || d.includes("loss"))
    return "#F43F5E";
  return theme.accent;
};

export const HudTelemetry: React.FC<{
  metrics: DynamicHUDMetric[];
  theme: ArchetypeTheme;
  localFrame: number;
  fps: number;
  vertical?: boolean;
}> = ({ metrics, theme, localFrame, fps, vertical }) => {
  if (!metrics || metrics.length === 0) return null;
  return (
    <div
      style={{
        display: "flex",
        flexDirection: vertical ? "column" : "row",
        gap: 16,
        flexWrap: "wrap",
      }}
    >
      {metrics.slice(0, 4).map((m, i) => {
        const s = spring({ frame: localFrame - i * 4, fps, config: { damping: 16, stiffness: 120 } });
        return (
          <div
            key={`${m.label}-${i}`}
            style={{
              minWidth: 180,
              padding: "16px 20px",
              background: theme.card,
              border: `1px solid ${theme.cardBorder}`,
              borderRadius: 14,
              opacity: s,
              transform: `translateY(${interpolate(s, [0, 1], [18, 0])}px)`,
              boxShadow: theme.mode === "dark" ? `0 0 24px ${theme.accent}18` : "none",
            }}
          >
            <div
              style={{
                fontFamily: theme.fontMono,
                fontSize: 15,
                letterSpacing: 2,
                textTransform: "uppercase",
                color: theme.textMuted,
              }}
            >
              {m.label}
            </div>
            <div
              style={{
                fontFamily: theme.fontMono,
                fontSize: 34,
                fontWeight: 700,
                color: theme.textPrimary,
                marginTop: 4,
                lineHeight: 1.05,
              }}
            >
              {m.value}
            </div>
            {m.delta ? (
              <div style={{ fontFamily: theme.fontMono, fontSize: 16, fontWeight: 700, marginTop: 4, color: deltaColor(m.delta, theme) }}>
                {m.delta}
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
};
