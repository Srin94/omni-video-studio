import type {
  JobStatus,
  PreparedPrompt,
  TrendCard,
  ValidationResult,
  VideoFormat,
} from "./types";

// Same-origin by default (local dev proxies /api -> :8000). For a deployed
// studio talking to a separately-hosted backend, set VITE_API_BASE at build
// time, e.g. VITE_API_BASE=https://omni-api.onrender.com
const API_BASE = (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "");

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail: unknown;
    try {
      detail = (await res.json())?.detail;
    } catch {
      detail = await res.text();
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return (await res.json()) as T;
}

export const api = {
  health: () =>
    req<{ ok: boolean; telegram_configured: boolean; youtube_configured: boolean; github_configured?: boolean }>(
      "/api/health"
    ),

  trends: (genre?: string, force = false) =>
    req<{ count: number; genre: string; trends: TrendCard[] }>(
      `/api/trends?${new URLSearchParams({ ...(genre && genre !== "ALL" ? { genre } : {}), ...(force ? { force: "true" } : {}) })}`
    ),

  preparePrompt: (topic: string, genre: string, format: VideoFormat) =>
    req<PreparedPrompt>("/api/prepare-prompt", {
      method: "POST",
      body: JSON.stringify({ topic, genre, format }),
    }),

  validate: (json_text: string, format: VideoFormat, sources: string[]) =>
    req<ValidationResult>("/api/validate-json", {
      method: "POST",
      body: JSON.stringify({ json_text, format, sources }),
    }),

  startRender: (
    json_text: string,
    format: VideoFormat,
    sources: string[],
    opts: { dry_run?: boolean; skip_approval?: boolean; skip_video?: boolean } = {}
  ) =>
    req<{ job_id: string; summary: unknown; warnings: string[] }>("/api/start-render", {
      method: "POST",
      body: JSON.stringify({ json_text, format, sources, ...opts }),
    }),

  status: (jobId: string) => req<JobStatus>(`/api/status/${jobId}`),

  // Hosted/mobile path: commit the payload to render-jobs/ on GitHub, which
  // fires the Actions render workflow (no local render on the free backend).
  dispatchRender: (json_text: string, format: VideoFormat, sources: string[]) =>
    req<{
      ok: boolean;
      title: string;
      path: string;
      branch: string;
      actions_url: string;
      commit_url: string;
    }>("/api/dispatch-render", {
      method: "POST",
      body: JSON.stringify({ json_text, format, sources }),
    }),
};
