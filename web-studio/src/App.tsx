import React, { useEffect, useState } from "react";
import { Radar, Sparkles, Wand2, Rocket, type LucideIcon } from "lucide-react";
import type { PreparedPrompt, VideoFormat } from "./types";
import { api } from "./api";
import { TopicRadar } from "./components/TopicRadar";
import { PromptRelay } from "./components/PromptRelay";
import { IngestionMonitor } from "./components/IngestionMonitor";

type Step = 1 | 2 | 3;

const STEPS: { n: Step; label: string; icon: LucideIcon }[] = [
  { n: 1, label: "Topic & Radar", icon: Radar },
  { n: 2, label: "Prompt Relay", icon: Wand2 },
  { n: 3, label: "Render & Publish", icon: Rocket },
];

export const App: React.FC = () => {
  const [step, setStep] = useState<Step>(1);
  const [topic, setTopic] = useState("");
  const [genre, setGenre] = useState<string>("PARADOX_LOGIC");
  const [format, setFormat] = useState<VideoFormat>("landscape");
  const [prepared, setPrepared] = useState<PreparedPrompt | null>(null);
  const [health, setHealth] = useState<{ telegram_configured: boolean; youtube_configured: boolean; github_configured?: boolean } | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  const goPrepare = async (t: string, g: string, f: VideoFormat) => {
    setTopic(t);
    setGenre(g);
    setFormat(f);
    setStep(2);
  };

  return (
    <div className="min-h-full">
      {/* Header */}
      <header className="sticky top-0 z-20 border-b border-ink-700/60 bg-ink-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-2">
            <Sparkles className="text-brand" size={22} />
            <span className="font-mono text-sm font-semibold tracking-[0.3em] text-brand">OMNI STUDIO</span>
          </div>
          <div className="hidden items-center gap-3 text-xs text-ink-600 sm:flex">
            <Badge ok={!!health}>API</Badge>
            <Badge ok={health?.github_configured}>GitHub</Badge>
            <Badge ok={health?.telegram_configured}>Telegram</Badge>
            <Badge ok={health?.youtube_configured}>YouTube</Badge>
          </div>
        </div>
      </header>

      {/* Stepper */}
      <nav className="mx-auto max-w-6xl px-4 pt-6 sm:px-6">
        <ol className="flex items-center gap-2 sm:gap-4">
          {STEPS.map((s, i) => {
            const active = step === s.n;
            const done = step > s.n;
            const Icon = s.icon;
            return (
              <li key={s.n} className="flex flex-1 items-center gap-2">
                <button
                  onClick={() => (s.n < step ? setStep(s.n) : undefined)}
                  className={`flex w-full items-center gap-2 rounded-xl border px-3 py-2 text-left transition ${
                    active
                      ? "border-brand/60 bg-brand/10 text-white shadow-glow"
                      : done
                        ? "border-ink-700 bg-ink-850 text-ink-200 hover:border-brand/40"
                        : "border-ink-800 bg-ink-900 text-ink-600"
                  }`}
                >
                  <span className={`grid h-7 w-7 shrink-0 place-items-center rounded-lg font-mono text-xs ${active ? "bg-brand text-ink-950" : "bg-ink-800 text-ink-300"}`}>
                    {done ? "✓" : s.n}
                  </span>
                  <span className="hidden text-sm font-medium sm:block">{s.label}</span>
                  <Icon size={16} />
                </button>
              </li>
            );
          })}
        </ol>
      </nav>

      {/* Views */}
      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
        {step === 1 && (
          <TopicRadar
            initialTopic={topic}
            genre={genre}
            format={format}
            onGenre={setGenre}
            onFormat={setFormat}
            onContinue={goPrepare}
          />
        )}
        {step === 2 && (
          <PromptRelay
            topic={topic}
            genre={genre}
            format={format}
            prepared={prepared}
            onPrepared={setPrepared}
            onBack={() => setStep(1)}
            onContinue={() => setStep(3)}
          />
        )}
        {step === 3 && (
          <IngestionMonitor
            format={format}
            sources={prepared?.sources ?? []}
            telegramConfigured={!!health?.telegram_configured}
            youtubeConfigured={!!health?.youtube_configured}
            githubConfigured={!!health?.github_configured}
            onBack={() => setStep(2)}
          />
        )}
      </main>

      <footer className="mx-auto max-w-6xl px-4 pb-10 pt-4 text-center text-xs text-ink-600 sm:px-6">
        Omni Video Studio · genre-agnostic HITL prompt-relay pipeline
      </footer>
    </div>
  );
};

const Badge: React.FC<{ ok?: boolean; children: React.ReactNode }> = ({ ok, children }) => (
  <span className="flex items-center gap-1 rounded-full border border-ink-700 bg-ink-900 px-2 py-0.5">
    <span className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-emerald-400" : "bg-ink-600"}`} />
    {children}
  </span>
);
