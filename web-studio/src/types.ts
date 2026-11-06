export type VideoFormat = "landscape" | "portrait";

export const GENRES = [
  { id: "ALL", label: "All" },
  { id: "SCIENCE_PHYSICS", label: "Science & Physics" },
  { id: "EVERYDAY_TECH", label: "Everyday Tech" },
  { id: "PARADOX_LOGIC", label: "Game Theory & Paradoxes" },
  { id: "MONEY_BUSINESS", label: "Business & Money" },
  { id: "HISTORY_CULTURE", label: "History & Mysteries" },
  { id: "CRIME_MYSTERY", label: "True Crime Forensics" },
] as const;

export type GenreId = (typeof GENRES)[number]["id"];

export interface TrendCard {
  title: string;
  source: string;
  url: string;
  genre: string;
  hook_score: number;
  blurb: string;
  traffic: string;
}

export interface PreparedPrompt {
  topic: string;
  genre: string;
  video_format: VideoFormat;
  sources: string[];
  reference_chars: number;
  reference_method: string;
  reference_preview: string;
  master_prompt: string;
}

export interface ValidationSummary {
  youtube_title?: string;
  genre?: string;
  video_format?: string;
  bgm_mood?: string;
  scene_count?: number;
  estimated_duration_sec?: number;
  archetypes_used?: string[];
  tag_count?: number;
}

export interface ValidationResult {
  ok: boolean;
  errors: string[];
  warnings: string[];
  summary: ValidationSummary;
}

export interface JobStage {
  key: string;
  label: string;
  status: "pending" | "running" | "done" | "skipped" | "error";
  detail: string;
}

export interface JobStatus {
  job_id: string;
  stages: JobStage[];
  status: "queued" | "running" | "done" | "error";
  title: string;
  elapsed_sec: number;
  video_id?: string | null;
  error?: string | null;
}
