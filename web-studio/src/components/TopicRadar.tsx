import React, { useEffect, useState } from "react";
import { Monitor, Smartphone, RefreshCw, Flame, ArrowRight } from "lucide-react";
import { GENRES, type TrendCard, type VideoFormat } from "../types";
import { api } from "../api";

interface Props {
  initialTopic: string;
  genre: string;
  format: VideoFormat;
  onGenre: (g: string) => void;
  onFormat: (f: VideoFormat) => void;
  onContinue: (topic: string, genre: string, format: VideoFormat) => void;
}

export const TopicRadar: React.FC<Props> = ({ initialTopic, genre, format, onGenre, onFormat, onContinue }) => {
  const [topic, setTopic] = useState(initialTopic);
  const [filter, setFilter] = useState<string>("ALL");
  const [trends, setTrends] = useState<TrendCard[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async (f: string, force = false) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.trends(f, force);
      setTrends(res.trends);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(filter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const useTopic = (t: string, g: string) => {
    onGenre(g);
    onContinue(t, g, format);
  };

  return (
    <div className="space-y-6">
      {/* Hero input + format toggle */}
      <section className="rounded-2xl border border-ink-700 bg-ink-900/70 p-5 sm:p-6">
        <h1 className="text-xl font-semibold sm:text-2xl">What topic is on your mind today?</h1>
        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && topic.trim() && onContinue(topic.trim(), genre, format)}
            placeholder="e.g. How Shazam recognises a song in 3 seconds"
            className="flex-1 rounded-xl border border-ink-700 bg-ink-950 px-4 py-3 text-base outline-none placeholder:text-ink-600 focus:border-brand/60"
          />
          <button
            disabled={!topic.trim()}
            onClick={() => onContinue(topic.trim(), genre, format)}
            className="flex items-center justify-center gap-2 rounded-xl bg-brand px-5 py-3 font-semibold text-ink-950 transition hover:bg-brand-glow disabled:cursor-not-allowed disabled:opacity-40"
          >
            Assemble Prompt <ArrowRight size={18} />
          </button>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <span className="text-xs uppercase tracking-widest text-ink-600">Format</span>
          <div className="flex overflow-hidden rounded-lg border border-ink-700">
            <ToggleBtn active={format === "landscape"} onClick={() => onFormat("landscape")}>
              <Monitor size={15} /> 16:9 · 3-5 min
            </ToggleBtn>
            <ToggleBtn active={format === "portrait"} onClick={() => onFormat("portrait")}>
              <Smartphone size={15} /> 9:16 · 60s
            </ToggleBtn>
          </div>
        </div>
      </section>

      {/* Genre pills (also drive the active genre for the prompt) */}
      <div className="flex flex-wrap gap-2">
        {GENRES.map((g) => {
          const active = g.id === "ALL" ? filter === "ALL" : genre === g.id;
          return (
            <button
              key={g.id}
              onClick={() => {
                if (g.id === "ALL") {
                  setFilter("ALL");
                } else {
                  onGenre(g.id);
                  setFilter(g.id);
                }
              }}
              className={`rounded-full border px-3 py-1.5 text-sm transition ${
                active ? "border-brand/60 bg-brand/15 text-white" : "border-ink-700 bg-ink-900 text-ink-300 hover:border-brand/40"
              }`}
            >
              {g.label}
            </button>
          );
        })}
      </div>

      {/* Live Trend Radar */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <Flame className="text-amber-400" size={18} /> Live Idea Radar
          </h2>
          <button
            onClick={() => load(filter, true)}
            className="flex items-center gap-1.5 rounded-lg border border-ink-700 bg-ink-900 px-3 py-1.5 text-sm text-ink-300 hover:border-brand/40"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
        </div>

        {error && <p className="rounded-lg border border-rose-500/40 bg-rose-500/10 p-3 text-sm text-rose-200">{error}</p>}

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {loading && trends.length === 0
            ? Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-36 animate-pulse rounded-xl border border-ink-800 bg-ink-900/50" />)
            : trends.map((t, i) => (
                <article key={i} className="group flex flex-col justify-between rounded-xl border border-ink-700 bg-ink-900/70 p-4 transition hover:border-brand/40">
                  <div>
                    <div className="flex items-start justify-between gap-2">
                      <HookScore score={t.hook_score} />
                      <span className="rounded bg-ink-800 px-1.5 py-0.5 font-mono text-[10px] uppercase text-ink-400">
                        {t.genre.replace(/_/g, " ")}
                      </span>
                    </div>
                    <h3 className="mt-2 line-clamp-3 text-sm font-medium leading-snug">{t.title}</h3>
                    {t.blurb && <p className="mt-1 line-clamp-2 text-xs text-ink-600">{t.blurb}</p>}
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <span className="truncate text-[11px] text-ink-600">{t.source}</span>
                    <button
                      onClick={() => useTopic(t.title, t.genre)}
                      className="shrink-0 rounded-lg bg-brand/15 px-2.5 py-1 text-xs font-semibold text-brand transition group-hover:bg-brand group-hover:text-ink-950"
                    >
                      Use This →
                    </button>
                  </div>
                </article>
              ))}
        </div>
        {!loading && trends.length === 0 && !error && (
          <p className="py-10 text-center text-sm text-ink-600">No trends right now — type a topic above to get started.</p>
        )}
      </section>
    </div>
  );
};

const ToggleBtn: React.FC<{ active: boolean; onClick: () => void; children: React.ReactNode }> = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-1.5 px-3 py-2 text-sm transition ${active ? "bg-brand text-ink-950" : "bg-ink-900 text-ink-300 hover:bg-ink-800"}`}
  >
    {children}
  </button>
);

const HookScore: React.FC<{ score: number }> = ({ score }) => {
  const color = score >= 75 ? "text-emerald-400" : score >= 55 ? "text-amber-400" : "text-ink-400";
  return (
    <div className="flex items-center gap-1">
      <span className={`font-mono text-lg font-bold ${color}`}>{score}</span>
      <span className="text-[10px] uppercase tracking-wide text-ink-600">hook</span>
    </div>
  );
};
