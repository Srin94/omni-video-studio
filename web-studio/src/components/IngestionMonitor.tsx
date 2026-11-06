import React, { useEffect, useRef, useState } from "react";
import { ArrowLeft, CheckCircle2, XCircle, AlertTriangle, Loader2, Rocket, Github, ExternalLink } from "lucide-react";
import type { JobStatus, ValidationResult, VideoFormat } from "../types";
import { api } from "../api";

interface Props {
  format: VideoFormat;
  sources: string[];
  telegramConfigured: boolean;
  youtubeConfigured: boolean;
  githubConfigured: boolean;
  onBack: () => void;
}

const STATUS_ICON: Record<string, React.ReactNode> = {
  done: <CheckCircle2 size={18} className="text-emerald-400" />,
  running: <Loader2 size={18} className="animate-spin text-brand" />,
  error: <XCircle size={18} className="text-rose-400" />,
  skipped: <span className="text-sm text-ink-600">skipped</span>,
  pending: <span className="h-4 w-4 rounded-full border border-ink-600" />,
};

type DispatchResult = { title: string; actions_url: string; commit_url: string };

export const IngestionMonitor: React.FC<Props> = ({ format, sources, telegramConfigured, youtubeConfigured, githubConfigured, onBack }) => {
  const [jsonText, setJsonText] = useState("");
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [validating, setValidating] = useState(false);
  const [dryRun, setDryRun] = useState(true);
  const [skipApproval, setSkipApproval] = useState(true);
  const [skipVideo, setSkipVideo] = useState(false);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [launching, setLaunching] = useState(false);
  const [dispatching, setDispatching] = useState(false);
  const [dispatchResult, setDispatchResult] = useState<DispatchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  const renderOnGithub = async () => {
    setDispatching(true);
    setError(null);
    setDispatchResult(null);
    try {
      const r = await api.dispatchRender(jsonText, format, sources);
      setDispatchResult({ title: r.title, actions_url: r.actions_url, commit_url: r.commit_url });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setDispatching(false);
    }
  };

  const validate = async () => {
    setValidating(true);
    setError(null);
    try {
      setValidation(await api.validate(jsonText, format, sources));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setValidating(false);
    }
  };

  const launch = async () => {
    setLaunching(true);
    setError(null);
    try {
      const res = await api.startRender(jsonText, format, sources, {
        dry_run: dryRun,
        skip_approval: skipApproval,
        skip_video: skipVideo,
      });
      poll(res.job_id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLaunching(false);
    }
  };

  const poll = (jobId: string) => {
    const tick = async () => {
      try {
        const j = await api.status(jobId);
        setJob(j);
        if (j.status === "done" || j.status === "error") {
          if (pollRef.current) window.clearInterval(pollRef.current);
        }
      } catch {
        /* keep polling */
      }
    };
    tick();
    pollRef.current = window.setInterval(tick, 2000);
  };

  useEffect(() => () => {
    if (pollRef.current) window.clearInterval(pollRef.current);
  }, []);

  const s = validation?.summary;

  return (
    <div className="space-y-5">
      <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-ink-400 hover:text-white">
        <ArrowLeft size={16} /> Back to prompt
      </button>

      {/* JSON ingest */}
      <section className="rounded-2xl border border-ink-700 bg-ink-900/70 p-5">
        <h2 className="text-lg font-semibold">Paste Model Response JSON</h2>
        <textarea
          value={jsonText}
          onChange={(e) => {
            setJsonText(e.target.value);
            setValidation(null);
          }}
          placeholder='{ "genre": "PARADOX_LOGIC", "scenes": [ ... ], ... }'
          className="mt-3 h-56 w-full resize-y rounded-xl border border-ink-800 bg-ink-950 p-4 font-mono text-[12.5px] outline-none placeholder:text-ink-600 focus:border-brand/60"
        />
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <button
            disabled={!jsonText.trim() || validating}
            onClick={validate}
            className="flex items-center gap-2 rounded-xl border border-brand/50 bg-brand/15 px-4 py-2 font-semibold text-brand transition hover:bg-brand/25 disabled:opacity-40"
          >
            {validating ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />} Validate Schema
          </button>
          {validation && (
            <span className={`flex items-center gap-1.5 text-sm ${validation.ok ? "text-emerald-400" : "text-rose-400"}`}>
              {validation.ok ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
              {validation.ok ? "Valid payload" : `${validation.errors.length} error(s)`}
            </span>
          )}
        </div>

        {validation && !validation.ok && (
          <ul className="mt-3 space-y-1 rounded-lg border border-rose-500/40 bg-rose-500/10 p-3 text-sm text-rose-200">
            {validation.errors.map((e, i) => (
              <li key={i} className="font-mono text-xs">• {e}</li>
            ))}
          </ul>
        )}
        {validation?.warnings?.length ? (
          <ul className="mt-3 space-y-1 rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-amber-200">
            {validation.warnings.map((w, i) => (
              <li key={i} className="flex items-center gap-1.5 text-xs">
                <AlertTriangle size={13} /> {w}
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      {/* Summary card */}
      {validation?.ok && s && (
        <section className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-5">
          <h3 className="text-base font-semibold text-emerald-200">{s.youtube_title}</h3>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Stat label="Genre" value={(s.genre || "").replace(/_/g, " ")} />
            <Stat label="Scenes" value={String(s.scene_count ?? "—")} />
            <Stat label="Est. duration" value={`${Math.round(s.estimated_duration_sec ?? 0)}s`} />
            <Stat label="BGM" value={s.bgm_mood ?? "—"} />
          </div>
          {s.archetypes_used?.length ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {s.archetypes_used.map((a) => (
                <span key={a} className="rounded bg-ink-800 px-2 py-0.5 font-mono text-[11px] text-ink-300">{a}</span>
              ))}
            </div>
          ) : null}

          {/* Pipeline options */}
          <div className="mt-4 flex flex-wrap gap-4 border-t border-ink-700 pt-4 text-sm">
            <Check label="Dry run (no upload)" checked={dryRun} onChange={setDryRun} />
            <Check label="Skip Telegram approval" checked={skipApproval} onChange={setSkipApproval} />
            <Check label="Skip video render" checked={skipVideo} onChange={setSkipVideo} />
          </div>
          {!dryRun && !youtubeConfigured && (
            <p className="mt-2 text-xs text-amber-300">YouTube isn’t configured — upload will be skipped automatically.</p>
          )}

          <div className="mt-4 flex flex-wrap items-center gap-3">
            {/* Primary: render on the free GitHub Actions farm (works on mobile,
                no local Node/Chrome needed). */}
            <button
              disabled={dispatching}
              onClick={renderOnGithub}
              className="flex items-center gap-2 rounded-xl bg-brand px-5 py-2.5 font-semibold text-ink-950 transition hover:bg-brand-glow disabled:opacity-40"
            >
              {dispatching ? <Loader2 size={18} className="animate-spin" /> : <Github size={18} />} Render on GitHub
            </button>
            {/* Secondary: local full pipeline (only works when the backend runs
                on a machine with the Remotion renderer installed). */}
            <button
              disabled={launching || (!!job && job.status === "running")}
              onClick={launch}
              className="flex items-center gap-2 rounded-xl border border-ink-600 px-4 py-2.5 font-medium text-ink-200 transition hover:border-brand/50 hover:text-white disabled:opacity-40"
            >
              {launching ? <Loader2 size={18} className="animate-spin" /> : <Rocket size={18} />} Render locally
            </button>
          </div>
          <p className="mt-2 text-xs text-ink-500">
            <span className="text-ink-300">Render on GitHub</span> runs the free Actions render farm and delivers the
            finished video to Telegram — the mobile-friendly path.{" "}
            {!githubConfigured && <span className="text-amber-300">Set GITHUB_TOKEN on the backend to enable it.</span>}
          </p>

          {dispatchResult && (
            <div className="mt-4 rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-4">
              <p className="flex items-center gap-2 text-sm font-semibold text-emerald-200">
                <CheckCircle2 size={16} /> Render queued: {dispatchResult.title}
              </p>
              <p className="mt-1 text-xs text-ink-300">
                A GitHub runner is building your video now (~12–18 min). It'll land in your Telegram when done, and the
                run shows up here:
              </p>
              <a
                href={dispatchResult.actions_url}
                target="_blank"
                rel="noreferrer"
                className="mt-2 inline-flex items-center gap-1.5 text-sm text-brand hover:underline"
              >
                <ExternalLink size={14} /> View the render run on GitHub Actions
              </a>
            </div>
          )}
        </section>
      )}

      {error && <p className="rounded-lg border border-rose-500/40 bg-rose-500/10 p-3 text-sm text-rose-200">{error}</p>}

      {/* Live pipeline stepper */}
      {job && (
        <section className="rounded-2xl border border-ink-700 bg-ink-900/70 p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-base font-semibold">Pipeline</h3>
            <span className="font-mono text-xs text-ink-500">
              {job.status} · {job.elapsed_sec}s
            </span>
          </div>
          <ol className="space-y-2">
            {job.stages.map((st) => (
              <li key={st.key} className="flex items-center gap-3 rounded-lg border border-ink-800 bg-ink-950 px-3 py-2.5">
                <span className="grid w-6 place-items-center">{STATUS_ICON[st.status] ?? STATUS_ICON.pending}</span>
                <span className={`flex-1 text-sm ${st.status === "pending" ? "text-ink-600" : "text-ink-100"}`}>{st.label}</span>
                {st.detail && <span className="truncate font-mono text-[11px] text-ink-500">{st.detail}</span>}
              </li>
            ))}
          </ol>
          {job.video_id && (
            <a href={`https://youtu.be/${job.video_id}`} target="_blank" rel="noreferrer" className="mt-3 inline-block text-sm text-brand hover:underline">
              ▶ Published: https://youtu.be/{job.video_id}
            </a>
          )}
          {job.error && <p className="mt-3 text-sm text-rose-300">Error: {job.error}</p>}
        </section>
      )}
    </div>
  );
};

const Stat: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="rounded-lg border border-ink-700 bg-ink-900 p-3">
    <div className="text-[10px] uppercase tracking-widest text-ink-600">{label}</div>
    <div className="mt-1 truncate font-mono text-sm text-ink-100">{value}</div>
  </div>
);

const Check: React.FC<{ label: string; checked: boolean; onChange: (v: boolean) => void }> = ({ label, checked, onChange }) => (
  <label className="flex cursor-pointer items-center gap-2 text-ink-300">
    <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="h-4 w-4 accent-[#38BDF8]" />
    {label}
  </label>
);
