import React from "react";
import { interpolate, spring } from "remotion";
import type { VisualElement } from "../types/schema";
import type { ArchetypeTheme } from "../styles/archetypes";
import { HIGHLIGHT } from "../styles/archetypes";

// Renders one VisualElement in a way that suits its type. Archetypes compose
// these; each archetype passes its own theme so a stat_card looks native to the
// canvas it sits on.

interface Props {
  el: VisualElement;
  theme: ArchetypeTheme;
  localFrame: number;
  fps: number;
  index: number;
}

const useEnter = (localFrame: number, fps: number, index: number) =>
  spring({ frame: localFrame - index * 6, fps, config: { damping: 18, stiffness: 110 } });

const Shell: React.FC<{ theme: ArchetypeTheme; accent: string; s: number; children: React.ReactNode }> = ({
  theme,
  accent,
  s,
  children,
}) => (
  <div
    style={{
      background: theme.card,
      border: `1px solid ${theme.cardBorder}`,
      borderLeft: `6px solid ${accent}`,
      borderRadius: 16,
      padding: "26px 30px",
      opacity: s,
      transform: `translateY(${interpolate(s, [0, 1], [26, 0])}px)`,
      boxShadow: theme.mode === "dark" ? `0 10px 40px rgba(0,0,0,0.35)` : `4px 4px 0 ${theme.cardBorder}`,
    }}
  >
    {children}
  </div>
);

export const VisualElementCard: React.FC<Props> = ({ el, theme, localFrame, fps, index }) => {
  const s = useEnter(localFrame, fps, index);
  const accent = HIGHLIGHT[el.highlight_color] ?? theme.accent;

  const label = (text: string) => (
    <div style={{ fontFamily: theme.fontMono, fontSize: 15, letterSpacing: 2, textTransform: "uppercase", color: theme.textMuted, marginBottom: 10 }}>
      {text}
    </div>
  );

  switch (el.element_type) {
    case "stat_card":
      return (
        <Shell theme={theme} accent={accent} s={s}>
          {el.badge ? label(el.badge) : null}
          <div style={{ fontFamily: theme.fontDisplay, fontSize: 76, fontWeight: 800, color: accent, lineHeight: 1 }}>
            {el.headline}
          </div>
          <div style={{ fontFamily: theme.fontHeading, fontSize: 26, color: theme.textMuted, marginTop: 10 }}>
            {el.subtext}
          </div>
        </Shell>
      );

    case "quote_callout":
      return (
        <Shell theme={theme} accent={accent} s={s}>
          <div style={{ fontFamily: theme.fontDisplay, fontSize: 40, fontStyle: "italic", color: theme.textPrimary, lineHeight: 1.25 }}>
            <span style={{ color: accent, fontSize: 56 }}>“</span>
            {el.headline}
          </div>
          <div style={{ fontFamily: theme.fontMono, fontSize: 20, color: theme.textMuted, marginTop: 14 }}>
            — {el.subtext}
          </div>
        </Shell>
      );

    case "comparison_split": {
      const [a, b] = el.headline.split(/\s+vs\.?\s+/i);
      return (
        <Shell theme={theme} accent={accent} s={s}>
          {el.badge ? label(el.badge) : null}
          <div style={{ display: "flex", alignItems: "stretch", gap: 18 }}>
            <div style={{ flex: 1, textAlign: "center" }}>
              <div style={{ fontFamily: theme.fontHeading, fontSize: 40, fontWeight: 800, color: theme.textMuted }}>{a ?? el.headline}</div>
            </div>
            <div style={{ fontFamily: theme.fontMono, fontSize: 32, fontWeight: 800, color: accent, alignSelf: "center" }}>VS</div>
            <div style={{ flex: 1, textAlign: "center" }}>
              <div style={{ fontFamily: theme.fontHeading, fontSize: 40, fontWeight: 800, color: accent }}>{b ?? ""}</div>
            </div>
          </div>
          <div style={{ fontFamily: theme.fontHeading, fontSize: 24, color: theme.textMuted, marginTop: 16, textAlign: "center" }}>
            {el.subtext}
          </div>
        </Shell>
      );
    }

    case "node_network":
      return (
        <Shell theme={theme} accent={accent} s={s}>
          {label(el.badge ?? "SYSTEM")}
          <div style={{ fontFamily: theme.fontHeading, fontSize: 36, fontWeight: 800, color: theme.textPrimary }}>{el.headline}</div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 18, flexWrap: "wrap" }}>
            {el.subtext.split(/\s*(?:->|→|,)\s*/).filter(Boolean).map((node, i, arr) => (
              <React.Fragment key={i}>
                <div style={{ padding: "10px 18px", borderRadius: 10, border: `1px solid ${accent}`, color: theme.textPrimary, fontFamily: theme.fontMono, fontSize: 22 }}>
                  {node}
                </div>
                {i < arr.length - 1 ? <span style={{ color: accent, fontSize: 28 }}>→</span> : null}
              </React.Fragment>
            ))}
          </div>
        </Shell>
      );

    case "map_pin":
      return (
        <Shell theme={theme} accent={accent} s={s}>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ width: 20, height: 20, borderRadius: "50% 50% 50% 0", background: accent, transform: "rotate(-45deg)", boxShadow: `0 0 18px ${accent}` }} />
            <div style={{ fontFamily: theme.fontHeading, fontSize: 42, fontWeight: 800, color: theme.textPrimary }}>{el.headline}</div>
          </div>
          <div style={{ fontFamily: theme.fontHeading, fontSize: 24, color: theme.textMuted, marginTop: 10 }}>{el.subtext}</div>
        </Shell>
      );

    case "timeline_milestone":
      return (
        <Shell theme={theme} accent={accent} s={s}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 16 }}>
            <div style={{ fontFamily: theme.fontMono, fontSize: 44, fontWeight: 800, color: accent }}>{el.headline}</div>
            <div style={{ height: 2, flex: 1, background: theme.cardBorder }} />
          </div>
          <div style={{ fontFamily: theme.fontHeading, fontSize: 26, color: theme.textPrimary, marginTop: 12 }}>{el.subtext}</div>
        </Shell>
      );

    default:
      return (
        <Shell theme={theme} accent={accent} s={s}>
          <div style={{ fontFamily: theme.fontHeading, fontSize: 36, fontWeight: 800, color: theme.textPrimary }}>{el.headline}</div>
          <div style={{ fontFamily: theme.fontHeading, fontSize: 24, color: theme.textMuted, marginTop: 8 }}>{el.subtext}</div>
        </Shell>
      );
  }
};

export const VisualElementStack: React.FC<{
  elements: VisualElement[];
  theme: ArchetypeTheme;
  localFrame: number;
  fps: number;
}> = ({ elements, theme, localFrame, fps }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
    {elements.slice(0, 3).map((el, i) => (
      <VisualElementCard key={i} el={el} theme={theme} localFrame={localFrame} fps={fps} index={i} />
    ))}
  </div>
);
