import React from "react";
import {
  AbsoluteFill,
  Audio,
  staticFile,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { SceneSpec, OmniRenderPayload } from "./types/schema";
import { getArchetype, gridBackground } from "./styles/archetypes";
import { DocumentaryArchive } from "./components/archetypes/DocumentaryArchive";
import { KineticMinimalist } from "./components/archetypes/KineticMinimalist";
import { NeonTechnicalHud } from "./components/archetypes/NeonTechnicalHud";
import { NarrativeStoryboard } from "./components/archetypes/NarrativeStoryboard";
import { KaraokeSubtitles } from "./components/KaraokeSubtitles";
import { BrollLayer } from "./components/BrollLayer";
import { CinematicOverlay } from "./components/CinematicOverlay";
import { IllustrationStage, hasIllustration } from "./components/illustration/IllustrationStage";

export type MasterProps = { payload: OmniRenderPayload };

const CHANNEL_NAME = "Omni Studio";

interface ActiveScene {
  scene: SceneSpec;
  index: number;
  localFrame: number;
}

const useActiveScene = (payload: OmniRenderPayload, fps: number, frame: number): ActiveScene => {
  const timeSec = frame / fps;
  let index = 0;
  for (let i = 0; i < payload.scenes.length; i += 1) {
    if (timeSec >= payload.scenes[i].start_sec) index = i;
  }
  const scene = payload.scenes[index] ?? payload.scenes[0];
  const sceneStartFrame = Math.round((scene?.start_sec ?? 0) * fps);
  return { scene, index, localFrame: frame - sceneStartFrame };
};

// Continuous "camera drift" per scene.camera_movement.
const cameraTransform = (scene: SceneSpec, localFrame: number, durFrames: number): string => {
  const p = durFrames > 1 ? Math.min(1, localFrame / durFrames) : 0;
  switch (scene.camera_movement) {
    case "slow_zoom_in":
      return `scale(${interpolate(p, [0, 1], [1.0, 1.06])})`;
    case "slow_zoom_out":
      return `scale(${interpolate(p, [0, 1], [1.06, 1.0])})`;
    case "pan_right":
      return `translateX(${interpolate(p, [0, 1], [-1.5, 1.5])}%) scale(1.04)`;
    case "static_focus":
    default:
      return "scale(1.01)";
  }
};

const SceneDirector: React.FC<{
  scene: SceneSpec;
  theme: ReturnType<typeof getArchetype>;
  localFrame: number;
  fps: number;
  portrait: boolean;
  sceneCount: number;
}> = ({ scene, theme, localFrame, fps, portrait, sceneCount }) => {
  switch (scene.visual_archetype) {
    case "DOCUMENTARY_ARCHIVE":
      return <DocumentaryArchive scene={scene} theme={theme} localFrame={localFrame} fps={fps} portrait={portrait} />;
    case "KINETIC_MINIMALIST":
      return <KineticMinimalist scene={scene} theme={theme} localFrame={localFrame} fps={fps} portrait={portrait} />;
    case "NARRATIVE_STORYBOARD":
      return <NarrativeStoryboard scene={scene} theme={theme} localFrame={localFrame} fps={fps} portrait={portrait} sceneCount={sceneCount} />;
    case "NEON_TECHNICAL_HUD":
    default:
      return <NeonTechnicalHud scene={scene} theme={theme} localFrame={localFrame} fps={fps} portrait={portrait} />;
  }
};

export const MasterComposition: React.FC<MasterProps> = ({ payload }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();
  const portrait = height > width;
  const active = useActiveScene(payload, fps, frame);
  const scene = active.scene;
  const theme = getArchetype(scene?.visual_archetype ?? "NEON_TECHNICAL_HUD");
  const paper = theme.mode === "light";
  const hasAudio = payload.words.length > 0;
  const illus = hasIllustration(scene);
  const broll = !illus ? scene?.broll_asset ?? null : null;

  const durFrames = Math.max(1, Math.round((scene?.duration_sec ?? 4) * fps));
  const sceneProgress = durFrames > 1 ? Math.min(1, active.localFrame / durFrames) : 0;
  const enter = interpolate(active.localFrame, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const kicker = spring({ frame: active.localFrame, fps, config: { damping: 18, stiffness: 120 } });

  const gx = (frame * 0.2) % 64;
  const gy = (frame * 0.1) % 64;
  const progress = durationInFrames > 1 ? frame / (durationInFrames - 1) : 0;
  const narrative = scene?.visual_archetype === "NARRATIVE_STORYBOARD";
  const pad = portrait ? 56 : 72;

  // Illustrations always sit on a consistent DARK stage (predictable glow +
  // contrast) regardless of the archetype's own light/dark canvas.
  const illusBg = `radial-gradient(1200px 820px at 72% 18%, ${theme.accent}22 0%, transparent 60%), linear-gradient(150deg, #080C14 0%, #0C1424 100%)`;
  const archetypeBg = `radial-gradient(1200px 820px at 72% 20%, ${theme.accent}14 0%, transparent 60%), linear-gradient(150deg, ${theme.canvasBg} 0%, ${theme.canvasBg2} 100%)`;

  return (
    <AbsoluteFill
      style={{
        background: illus ? illusBg : archetypeBg,
        fontFamily: theme.fontHeading,
        color: illus ? "#EAF1FB" : theme.textPrimary,
        overflow: "hidden",
      }}
    >
      {hasAudio ? <Audio src={staticFile("assets/narration.wav")} /> : null}

      {illus ? (
        /* ---- Animated illustration: glyph-world crowd or concept-flow diagram -- */
        <>
          <AbsoluteFill
            style={{
              ...gridBackground(theme),
              backgroundColor: "transparent",
              backgroundPosition: `${gx}px ${gy}px`,
              opacity: 0.4,
              pointerEvents: "none",
            }}
          />
          <AbsoluteFill style={{ zIndex: 2 }}>
            <IllustrationStage
              scene={scene}
              theme={theme}
              localFrame={active.localFrame}
              fps={fps}
              width={width}
              height={height}
              portrait={portrait}
            />
          </AbsoluteFill>
        </>
      ) : broll ? (
        /* ---- B-roll scene: topic photo + restrained cinematic overlay ---- */
        <>
          <BrollLayer asset={broll} camera={scene.camera_movement} progress={sceneProgress} accent={theme.accent} />
          <CinematicOverlay scene={scene} theme={theme} localFrame={active.localFrame} fps={fps} portrait={portrait} />
        </>
      ) : (
        /* ---- No image found: fall back to the archetype canvas ---------- */
        <>
          <AbsoluteFill
            style={{
              ...gridBackground(theme),
              backgroundColor: "transparent",
              backgroundPosition: `${gx}px ${gy}px`,
              opacity: paper ? 0.5 : 0.6,
              pointerEvents: "none",
            }}
          />
          {narrative ? (
            <>
              <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: "7%", background: "#000", zIndex: 7 }} />
              <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: "7%", background: "#000", zIndex: 7 }} />
            </>
          ) : null}
          <div
            style={{
              position: "absolute",
              top: pad + 44,
              left: pad,
              right: pad,
              bottom: portrait ? 200 : 170,
              zIndex: 3,
              opacity: enter,
              transform: `${cameraTransform(scene, active.localFrame, durFrames)} translateY(${interpolate(kicker, [0, 1], [18, 0])}px)`,
              transformOrigin: "center center",
            }}
          >
            {scene ? (
              <SceneDirector scene={scene} theme={theme} localFrame={active.localFrame} fps={fps} portrait={portrait} sceneCount={payload.scenes.length} />
            ) : null}
          </div>
        </>
      )}

      {/* Channel wordmark (no slide counter — this is a video, not a deck) */}
      <div style={{ position: "absolute", top: pad - 18, left: pad, zIndex: 6 }}>
        <div style={{ fontFamily: theme.fontMono, fontSize: 20, letterSpacing: 7, fontWeight: 700, color: "#fff", opacity: 0.92, textShadow: "0 2px 12px rgba(0,0,0,0.7)" }}>
          {CHANNEL_NAME.toUpperCase()}
        </div>
      </div>

      {/* Karaoke subtitles */}
      <KaraokeSubtitles
        words={payload.words}
        timeSec={frame / fps}
        theme={theme}
        callout={scene?.callout_keywords ?? []}
        overImage={!!broll || illus}
        portrait={portrait}
        fallbackText={hasAudio ? undefined : scene?.narration_text}
      />

      {/* B-roll attribution (Creative Commons credit) */}
      {broll && scene?.broll_attribution ? (
        <div
          style={{
            position: "absolute",
            right: 12,
            bottom: 12,
            zIndex: 9,
            fontFamily: theme.fontMono,
            fontSize: 13,
            color: "rgba(255,255,255,0.62)",
            textShadow: "0 1px 6px rgba(0,0,0,0.9)",
          }}
        >
          {scene.broll_attribution}
        </div>
      ) : null}

      {/* Progress bar */}
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 5, background: "rgba(255,255,255,0.12)", zIndex: 9 }}>
        <div style={{ width: `${progress * 100}%`, height: "100%", background: theme.accent, boxShadow: `0 0 12px ${theme.accent}` }} />
      </div>
    </AbsoluteFill>
  );
};
