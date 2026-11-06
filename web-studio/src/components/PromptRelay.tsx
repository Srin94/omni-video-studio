import React, { useEffect, useRef, useState } from "react";
import { Copy, Check, ExternalLink, ArrowLeft, ArrowRight, FileSearch, Loader2 } from "lucide-react";
import type { PreparedPrompt, VideoFormat } from "../types";
import { api } from "../api";

interface Props {
  topic: string;
  genre: string;
  format: VideoFormat;
  prepared: PreparedPrompt | null;
  onPrepared: (p: PreparedPrompt) => void;
  onBack: () => void;
  onContinue: () => void;
}

export const PromptRelay: React.FC<Props> = ({ topic, genre, format, prepared, onPrepared, onBack, onContinue }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const requested = useRef<string>("");

  useEffect(() => {
    const key = `${topic}|${genre}|${format}`;
    if (!topic || requested.current === key) return;
    if (prepared && prepared.topic === topic && prepared.genre === genre && prepared.video_format === format) return;
    requested.current = key;
    setLoading(true);
    setError(null);
    api
      .preparePrompt(topic, genre, format)
      .then(onPrepared)
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topic, genre, format]);

  const copy = async () => {
    if (!prepared) return;
    await navigator.clipboard.writeText(prepared.master_prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-ink-400 hover:text-white">
          <ArrowLeft size={16} /> Back
        </button>
        <button
          disabled={!prepared}
          onClick={onContinue}
          className="flex items-center gap-2 rounded-xl bg-brand px-4 py-2 font-semibold text-ink-950 transition hover:bg-brand-glow disabled:opacity-40"
        >
          I have the JSON <ArrowRight size={16} />
        </button>
      </div>

      {/* Topic summary */}
      <section className="rounded-2xl border border-ink-700 bg-ink-900/70 p-5">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <Tag>{genre.replace(/_/g, " ")}</Tag>
          <Tag>{format}</Tag>
          {prepared && <Tag>{prepared.reference_method}</Tag>}
          {prepared && <Tag>{prepared.reference_chars.toLocaleString()} chars grounding</Tag>}
        </div>
        <h2 className="mt-3 text-lg font-semibold">{topic}</h2>

        {prepared?.sources?.length ? (
          <div className="mt-3">
            <p className="mb-1 flex items-center gap-1.5 text-xs uppercase tracking-widest text-ink-600">
              <FileSearch size={13} /> Scraped sources
            </p>
            <ul className="space-y-1">
              {prepared.sources.map((s) => (
                <li key={s}>
                  <a href={s} target="_blank" rel="noreferrer" className="text-xs text-brand hover:underline">
                    {s}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>

      {error && <p className="rounded-lg border border-rose-500/40 bg-rose-500/10 p-3 text-sm text-rose-200">{error}</p>}

      {loading && (
        <div className="flex items-center justify-center gap-2 rounded-2xl border border-ink-700 bg-ink-900/70 p-10 text-ink-400">
          <Loader2 className="animate-spin" size={18} /> Scouting references &amp; assembling the master prompt…
        </div>
      )}

      {/* Master prompt */}
      {prepared && !loading && (
        <section className="rounded-2xl border border-ink-700 bg-ink-900/70 p-5">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-base font-semibold">Master Synthesis Prompt</h3>
            <div className="flex flex-wrap gap-2">
              <a href="https://gemini.google.com/app" target="_blank" rel="noreferrer" className="flex items-center gap-1.5 rounded-lg border border-ink-700 bg-ink-850 px-3 py-1.5 text-sm hover:border-brand/40">
                Open Gemini <ExternalLink size={13} />
              </a>
              <a href="https://claude.ai/new" target="_blank" rel="noreferrer" className="flex items-center gap-1.5 rounded-lg border border-ink-700 bg-ink-850 px-3 py-1.5 text-sm hover:border-brand/40">
                Open Claude <ExternalLink size={13} />
              </a>
              <button
                onClick={copy}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-semibold transition ${
                  copied ? "bg-emerald-500 text-ink-950" : "bg-brand text-ink-950 hover:bg-brand-glow"
                }`}
              >
                {copied ? <Check size={15} /> : <Copy size={15} />} {copied ? "Copied!" : "Copy Master Prompt"}
              </button>
            </div>
          </div>
          <pre className="max-h-[420px] overflow-auto whitespace-pre-wrap rounded-xl border border-ink-800 bg-ink-950 p-4 font-mono text-[12.5px] leading-relaxed text-ink-200">
            {prepared.master_prompt}
          </pre>
          <p className="mt-3 text-xs text-ink-600">
            Paste this into Gemini Advanced or Claude Pro, copy the JSON it returns, then continue to validate &amp; render.
          </p>
        </section>
      )}
    </div>
  );
};

const Tag: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <span className="rounded bg-ink-800 px-2 py-0.5 font-mono text-[11px] uppercase text-ink-300">{children}</span>
);
