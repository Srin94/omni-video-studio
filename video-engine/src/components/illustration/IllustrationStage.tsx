import React from "react";
import type { SceneSpec } from "../../types/schema";
import type { ArchetypeTheme } from "../../styles/archetypes";
import { GlyphWorld } from "./GlyphWorld";
import { ConceptFlow } from "./ConceptFlow";

// True when a scene carries a renderable animated illustration. Used by the
// Master composition to prefer it over a static B-roll photo / text canvas.
export const hasIllustration = (scene: SceneSpec | undefined | null): boolean => {
  const il = scene?.illustration;
  if (!il) return false;
  if (il.kind === "concept_flow") return !!(il.flow && il.flow.nodes && il.flow.nodes.length > 0);
  return !!(il.world && il.world.population > 0);
};

export const IllustrationStage: React.FC<{
  scene: SceneSpec;
  theme: ArchetypeTheme;
  localFrame: number;
  fps: number;
  width: number;
  height: number;
  portrait: boolean;
}> = ({ scene, theme, localFrame, fps, width, height, portrait }) => {
  const il = scene.illustration;
  if (!il) return null;
  if (il.kind === "concept_flow" && il.flow && il.flow.nodes?.length) {
    return <ConceptFlow spec={il.flow} theme={theme} localFrame={localFrame} fps={fps} width={width} height={height} portrait={portrait} />;
  }
  if (il.world && il.world.population > 0) {
    return <GlyphWorld spec={il.world} theme={theme} localFrame={localFrame} fps={fps} width={width} height={height} portrait={portrait} />;
  }
  return null;
};
