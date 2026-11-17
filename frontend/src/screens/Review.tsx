import type { DangerHit, FollowUp, Language, VisitRecord } from "../types";
import { fieldLabel, S } from "../strings";
import { Badge, Card, MicIcon, SectionTitle } from "../components/ui";
import { DangerBanner } from "../components/DangerBanner";
import { RecordCard } from "../components/RecordCard";
import { FollowUpList } from "../components/FollowUpList";

export function ReviewScreen({
  language,
  record,
  missing,
  unclear,
  danger,
  followups,
  alarmMessage,
  speaking,
  level,
  onConfirm,
  onReplay,
  onCancel,
  onManual,
  onReplayAlarm,
}: {
  language: Language;
  record: VisitRecord;
  missing: string[];
  unclear: string[];
  danger: DangerHit[];
  followups: FollowUp[];
  alarmMessage: string | null;
  speaking: boolean;
  level: number;
  onConfirm: () => void;
  onReplay: () => void;
  onCancel: () => void;
  onManual: (record: VisitRecord) => void;
  onReplayAlarm?: () => void;
}) {
  return (
    <div className="space-y-4 pb-10">
      <DangerBanner hits={danger} language={language} message={alarmMessage} onReplay={onReplayAlarm} />

      {missing.length > 0 && (
        <Card className="border-amber-300 bg-amber-50 px-4 py-3">
          <p className="text-sm font-bold text-amber-900">{S.needsAnswer[language]}</p>
          <p className="mt-0.5 text-xs leading-relaxed text-amber-800">
            {missing.map((field) => fieldLabel(field, language)).join(" · ")}
          </p>
          <p className="mt-1 text-[11px] text-amber-700">{S.correctionHint[language]}</p>
        </Card>
      )}

      <RecordCard record={record} missing={missing} unclear={unclear} language={language} />

      <Card className={`flex items-center gap-3 px-4 py-3 ${speaking ? "border-brand-300 bg-brand-50" : ""}`}>
        <span className="relative flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 text-brand-700">
          <MicIcon className="h-5 w-5" />
          {speaking && <span className="absolute inset-0 animate-ping rounded-full bg-brand-400/40" />}
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-slate-800">
            {speaking ? S.speakingInterrupt[language] : S.correctionHint[language]}
          </p>
          <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-slate-200">
            <div
              className="h-full rounded-full bg-brand-600 transition-all duration-100"
              style={{ width: `${Math.round(Math.min(1, level) * 100)}%` }}
            />
          </div>
        </div>
      </Card>

      <div className="grid gap-2">
        <button
          type="button"
          onClick={onConfirm}
          className="w-full rounded-2xl bg-brand-700 px-4 py-4 text-base font-bold text-white shadow-lg shadow-brand-700/20 active:bg-brand-800"
        >
          ✓ {S.confirm[language]}
        </button>
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={onReplay}
            className="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-700 active:bg-slate-50"
          >
            ▶ {S.playAgain[language]}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-500 active:bg-slate-50"
          >
            {S.cancel[language]}
          </button>
        </div>
        <button
          type="button"
          onClick={() => onManual(record)}
          className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-600 active:bg-slate-50"
        >
          ⌨ {S.enterManually[language]}
        </button>
      </div>

      <section>
        <SectionTitle
          action={<Badge tone="amber">{followups.length} {S.pending[language]}</Badge>}
        >
          {S.followups[language]} · {S.willBeCreated[language]}
        </SectionTitle>
        <FollowUpList tasks={followups} language={language} />
      </section>
    </div>
  );
}
