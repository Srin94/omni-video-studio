import React from "react";
import { AbsoluteFill, Img, staticFile, interpolate } from "remotion";
import type { CameraMovement } from "../types/schema";

// Full-bleed, slowly-moving topic photo/diagram — the thing that turns the
// video from a slideshow into a documentary. The image is fetched at ~1.15x the
// frame so a continuous Ken-Burns move never exposes an edge, and a cinematic
// scrim keeps the overlaid text legible on any photo.

const kenBurns = (camera: CameraMovement, p: number) => {
  switch (camera) {
    case "slow_zoom_out":
      return { scale: interpolate(p, [0, 1], [1.14, 1.03]), x: 0, y: 0 };
    case "pan_right":
      return { scale: 1.1, x: interpolate(p, [0, 1], [-3.2, 3.2]), y: 0 };
    case "static_focus":
      return { scale: interpolate(p, [0, 1], [1.04, 1.07]), x: 0, y: 0 };
    case "slow_zoom_in":
    default:
      return { scale: interpolate(p, [0, 1], [1.03, 1.14]), x: 0, y: 0 };
  }
};

export const BrollLayer: React.FC<{
  asset: string;
  camera: CameraMovement;
  progress: number; // 0..1 across the scene
  accent: string;
}> = ({ asset, camera, progress, accent }) => {
  const { scale, x, y } = kenBurns(camera, Math.max(0, Math.min(1, progress)));
  return (
    <AbsoluteFill style={{ backgroundColor: "#05070c", overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          transform: `scale(${scale}) translate(${x}%, ${y}%)`,
          transformOrigin: "center center",
        }}
      >
        <Img src={staticFile(asset)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>

      {/* Cinematic scrim: darker at top & bottom where text lives, clear in the
          middle so the subject stays visible. */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(3,6,12,0.74) 0%, rgba(3,6,12,0.18) 30%, rgba(3,6,12,0.16) 52%, rgba(3,6,12,0.88) 100%)",
        }}
      />
      {/* Accent wash + vignette for a graded, branded feel. */}
      <AbsoluteFill style={{ background: `radial-gradient(1400px 900px at 78% 24%, ${accent}1f 0%, transparent 60%)` }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 340px rgba(0,0,0,0.55)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
