import React from "react";
import { Composition, staticFile } from "remotion";
import "./global.css";
import { MasterComposition } from "./MasterComposition";
import type { OmniRenderPayload } from "./types/schema";
import { FALLBACK_PAYLOAD } from "./fallbackPayload";

const FPS = 60;
const DIMS: Record<string, { width: number; height: number }> = {
  landscape: { width: 1920, height: 1080 },
  portrait: { width: 1080, height: 1920 },
};

// Load the render payload the Python pipeline copies into
// public/assets/render_payload.json. Falls back to the bundled sample so the
// studio / render always has something valid to draw.
const loadPayload = async (): Promise<OmniRenderPayload> => {
  try {
    const res = await fetch(staticFile("assets/render_payload.json"));
    if (!res.ok) throw new Error(`status ${res.status}`);
    const json = (await res.json()) as OmniRenderPayload;
    if (!json.scenes || json.scenes.length === 0) throw new Error("no scenes");
    return json;
  } catch (err) {
    // eslint-disable-next-line no-console
    console.warn("[Root] Using fallback payload:", err);
    return FALLBACK_PAYLOAD;
  }
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="OmniMasterVideo"
      component={MasterComposition}
      durationInFrames={Math.ceil(FALLBACK_PAYLOAD.total_duration_sec * FPS)}
      fps={FPS}
      width={DIMS.landscape.width}
      height={DIMS.landscape.height}
      defaultProps={{ payload: FALLBACK_PAYLOAD }}
      calculateMetadata={async () => {
        const payload = await loadPayload();
        const dims = DIMS[payload.video_format] ?? DIMS.landscape;
        const duration = Math.max(1, Math.ceil((payload.total_duration_sec || 1) * FPS));
        return { durationInFrames: duration, props: { payload }, width: dims.width, height: dims.height, fps: FPS };
      }}
    />
  );
};
