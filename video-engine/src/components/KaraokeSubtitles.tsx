import React from "react";
import type { WordTimestamp } from "../types/schema";
import type { ArchetypeTheme } from "../styles/archetypes";
import { HIGHLIGHT } from "../styles/archetypes";

// Bottom-center karaoke captions. Word timings now come straight from the TTS
// engine (sentence-accurate), so the active word tracks the voice. A stable
// window of words sits around the cursor; the spoken word glows, upcoming words
// are dimmed, and any callout keyword takes the accent.

const norm = (w: string) => w.toLowerCase().replace(/[^\w'%$.-]/g, "");

export const KaraokeSubtitles: React.FC<{
  words: WordTimestamp[];
  timeSec: number;
  theme: ArchetypeTheme;
  callout: string[];
  overImage?: boolean;
  fallbackText?: string;
  portrait?: boolean;
}> = ({ words, timeSec, theme, callout, overImage = false, fallbackText, portrait = false }) => {
  const calloutSet = new Set(callout.map(norm));
  // Fewer words + smaller type in a narrow 9:16 frame so a line never runs off
  // the right edge.
  const WINDOW = portrait ? 6 : 9; // words visible around the cursor
  const fontSize = portrait ? 36 : 44;
  const sideInset = portrait ? "5%" : "8%";
  // Over a photo we always use light text; on a paper archetype keep dark ink.
  const baseColor = overImage ? "#FFFFFF" : theme.textPrimary;
  const strongShadow = "0 2px 16px rgba(0,0,0,0.85), 0 0 2px rgba(0,0,0,0.9)";

  let content: React.ReactNode;
  if (words && words.length > 0) {
    let active = 0;
    for (let i = 0; i < words.length; i += 1) {
      if (timeSec >= words[i].start_sec) active = i;
    }
    const start = Math.max(0, active - Math.floor(WINDOW / 2));
    const slice = words.slice(start, start + WINDOW);
    content = slice.map((w, i) => {
      const idx = start + i;
      const isActive = idx === active;
      const spoken = idx <= active;
      const isCallout = calloutSet.has(norm(w.word));
      const color = isCallout ? HIGHLIGHT.amber : isActive ? theme.accent : baseColor;
      return (
        <span
          key={idx}
          style={{
            color,
            opacity: spoken ? 1 : 0.42,
            fontWeight: isActive || isCallout ? 800 : 600,
            textShadow:
              isActive && !overImage && theme.mode === "dark"
                ? `0 0 18px ${theme.accent}99`
                : overImage
                ? strongShadow
                : "none",
            marginRight: 14,
            transition: "none",
          }}
        >
          {w.word}
        </span>
      );
    });
  } else if (fallbackText) {
    content = <span style={{ color: baseColor, opacity: 0.9, textShadow: overImage ? strongShadow : "none" }}>{fallbackText}</span>;
  } else {
    return null;
  }

  return (
    <div
      style={{
        position: "absolute",
        left: sideInset,
        right: sideInset,
        bottom: portrait ? 120 : 66,
        textAlign: "center",
        fontFamily: theme.fontHeading,
        fontSize,
        lineHeight: 1.3,
        letterSpacing: -0.3,
        overflowWrap: "break-word",
        padding: overImage ? "10px 24px" : "22px 34px",
        borderRadius: 18,
        background: overImage
          ? "transparent"
          : theme.mode === "dark"
          ? "rgba(0,0,0,0.42)"
          : "rgba(255,255,255,0.55)",
        backdropFilter: overImage ? "none" : "blur(6px)",
        zIndex: 8,
      }}
    >
      {content}
    </div>
  );
};
