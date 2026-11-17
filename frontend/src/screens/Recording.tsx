import { useEffect, useRef, useState } from "react";
import type { DangerHit, Language, VisitRecord } from "../types";
import { S } from "../strings";
import { Card, VoiceOrb } from "../components/ui";
import { DangerBanner } from "../components/DangerBanner";
import { RecordCard } from "../components/RecordCard";

export function RecordingScreen({
  language,
  level,
  phase,
  transcript,
  liveText,
  record,
  danger,
  alarmMessage,
  onStop,
  onCancel,
  onManual,
  onReplayAlarm,
  onInject,
}: {
  language: Language;
  level: number;
  phase: "recording" | "finalising";
  transcript: string;
  liveText: string;
  record: VisitRecord | null;
  danger: DangerHit[];
  alarmMessage: string | null;
  onStop: () => void;
  onCancel: () => void;
  onManual: () => void;
  onReplayAlarm?: () => void;
  onInject: (text: string) => void;
}) {
  const endRef = useRef<HTMLDivElement>(null);
  const [typed, setTyped] = useState("");
  const [quiet, setQuiet] = useState(false);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [transcript, liveText]);

  useEffect(() => {
    setQuiet(false);
    if (phase !== "recording" || transcript) return;
    const timer = window.setTimeout(() => setQuiet(true), 10_000);
    return () => window.clearTimeout(timer);
  }, [phase, transcript]);

  return (
    <div className="space-y-4 pb-10">
      <DangerBanner
        hits={danger}
        language={language}
        message={alarmMessage}
        onReplay={onReplayAlarm}
      />

      <Card className="px-4 py-6">
        {phase === "finalising" ? (
          <div className="flex flex-col items-center gap-3 py-6">
            <span className="h-10 w-10 animate-spin rounded-full border-4 border-brand-200 border-t-brand-700" />
            <p className="text-sm font-semibold text-slate-700">{S.processing[language]}</p>
            <p className="text-xs text-slate-400">{S.finishing[language]}</p>
          </div>
        ) : (
          <div>
            <VoiceOrb
              active
              level={level}
              onClick={onStop}
              label={S.tapToStop[language]}
              hint={S.speakNow[language]}
              language={language}
            />
            <p className="mt-3 text-center text-[11px] leading-snug text-slate-400">
              {S.autoFinishHint[language]}
            </p>
          </div>
        )}
        {phase === "recording" && (
          <div className="mt-4 flex flex-col items-center gap-2">
            <button
              type="button"
              onClick={onCancel}
              className="text-xs font-semibold text-slate-400 underline"
            >
              {S.cancel[language]}
            </button>
            <button
              type="button"
              onClick={onManual}
              className="rounded-full border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-600 active:bg-slate-50"
            >
              ⌨ {S.switchToManual[language]}
            </button>
          </div>
        )}
      </Card>

      {quiet && phase === "recording" && (
        <p className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800">
          {S.noSpeechYet[language]}
        </p>
      )}

      <Card className="overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/70 px-4 py-2">
          <p className="text-xs font-bold tracking-wide text-slate-500 uppercase">
            {S.transcript[language]}
          </p>
          <span className="flex items-center gap-1 text-[11px] font-semibold text-brand-700">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-brand-600" /> {S.live[language]}
          </span>
        </div>
        <div className="max-h-40 overflow-y-auto px-4 py-3">
          {transcript ? (
            <p className="text-sm leading-relaxed text-slate-800">{transcript}</p>
          ) : (
            <p className="text-sm text-slate-400">…</p>
          )}
          {liveText && <p className="mt-1 text-xs text-brand-700/70">“{liveText}”</p>}
          <div ref={endRef} />
        </div>
      </Card>

      {record && (record.patient_name || record.beneficiary_id || record.weight_kg) && (
        <div className="space-y-2">
          <p className="px-1 text-xs font-bold tracking-wide text-slate-500 uppercase">
            {S.recordTitle[language]} · {S.live[language]}
          </p>
          <RecordCard record={record} language={language} />
        </div>
      )}

      {phase === "recording" && (
        <details className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <summary className="cursor-pointer text-[11px] font-bold tracking-wide text-slate-500 uppercase">
            ⌨ {S.typeInstead[language]}
          </summary>
          <form
            className="mt-2 flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (!typed.trim()) return;
              onInject(typed);
              setTyped("");
            }}
          >
            <input
              value={typed}
              onChange={(event) => setTyped(event.target.value)}
              placeholder={S.typePlaceholder[language]}
              className="min-w-0 flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-500"
            />
            <button
              type="submit"
              className="shrink-0 rounded-xl bg-slate-800 px-4 py-2 text-sm font-semibold text-white"
            >
              {S.send[language]}
            </button>
          </form>
          <p className="mt-1.5 text-[11px] leading-snug text-slate-400">{S.typeHint[language]}</p>
        </details>
      )}
    </div>
  );
}

