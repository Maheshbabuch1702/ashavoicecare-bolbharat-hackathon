import type { DangerHit, FollowUp, Language, VisitRecord } from "../types";
import { extractionLabel, languageName, S, visitTypeLabel } from "../strings";
import { formatDate } from "../format";
import { Badge, Card, CheckIcon, SectionTitle } from "../components/ui";
import { FollowUpList } from "../components/FollowUpList";

export function SavedScreen({
  language,
  visitId,
  record,
  followups,
  danger,
  transcript,
  onNew,
  onComplete,
  onOpenVisit,
}: {
  language: Language;
  visitId: string;
  record: VisitRecord;
  followups: FollowUp[];
  danger: DangerHit[];
  transcript: string;
  onNew: () => void;
  onComplete: (id: string) => void;
  onOpenVisit: (id: string) => void;
}) {
  return (
    <div className="space-y-4 pb-10">
      <Card className="flex flex-col items-center px-5 py-7 text-center">
        <span className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
          <CheckIcon className="h-9 w-9" />
        </span>
        <h2 className="mt-3 text-lg font-black text-slate-900">{S.savedTitle[language]}</h2>
        <p className="mt-1 text-sm text-slate-500">{S.savedSubtitle[language]}</p>
        <div className="mt-3 flex flex-wrap justify-center gap-1.5">
          <Badge tone="slate">{visitId}</Badge>
          {record.beneficiary_id && <Badge tone="teal">{record.beneficiary_id}</Badge>}
          <Badge tone="green">{visitTypeLabel(record.visit_type, language)}</Badge>
        </div>
      </Card>

      {danger.length > 0 && (
        <Card className="border-2 border-red-400 bg-red-50 px-4 py-3">
          <p className="text-sm font-bold text-red-700">
            {S.dangerAlert[language]} · {danger.length}
          </p>
          <p className="mt-0.5 text-xs text-red-600">
            {S.referNow[language]}
          </p>
        </Card>
      )}

      <section>
        <SectionTitle action={<Badge tone="amber">{followups.length} {S.pending[language]}</Badge>}>
          {S.followups[language]}
        </SectionTitle>
        <FollowUpList tasks={followups} language={language} onComplete={onComplete} />
      </section>

      <div className="grid gap-2 sm:grid-cols-2">
        <button
          type="button"
          onClick={() => onOpenVisit(visitId)}
          className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm font-bold text-slate-700 active:bg-slate-50"
        >
          {S.visitDetail[language]} →
        </button>
        <button
          type="button"
          onClick={onNew}
          className="w-full rounded-2xl bg-brand-700 px-4 py-3 text-base font-bold text-white shadow-lg shadow-brand-700/20 active:bg-brand-800"
        >
          🎙 {S.newVisit[language]}
        </button>
      </div>

      <details className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
        <summary className="cursor-pointer text-xs font-bold tracking-wide text-slate-500 uppercase">
          {S.transcript[language]}
        </summary>
        <p className="mt-2 text-sm leading-relaxed text-slate-700">{transcript}</p>
        <p className="mt-2 text-[11px] text-slate-400">
          {S.manualNextVisit[language]}: {formatDate(record.next_visit_date, language) || "—"} · {S.languageLabel[language]}: {languageName(record.language, language)} ·{" "}
          {S.extractionLabel[language]}: {extractionLabel(record.extraction_method, language)}
        </p>
      </details>
    </div>
  );
}
