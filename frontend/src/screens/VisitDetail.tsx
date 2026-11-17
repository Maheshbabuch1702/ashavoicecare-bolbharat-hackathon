import { useState } from "react";
import type { Correction, Language, ManualVisitPayload, VisitDetail, VisitRecord } from "../types";
import { extractionLabel, fieldLabel, S, visitDisplayName, visitTypeLabel } from "../strings";
import { formatDate, timeAgo } from "../format";
import { Badge, Card, SectionTitle } from "../components/ui";
import { DangerBanner } from "../components/DangerBanner";
import { RecordCard } from "../components/RecordCard";
import { FollowUpList } from "../components/FollowUpList";
import { RecordForm } from "../components/RecordForm";

function recordFromVisit(visit: VisitDetail): VisitRecord {
  if (visit.extracted_json) return visit.extracted_json;
  return {
    beneficiary_id: visit.beneficiary_id,
    patient_name: visit.patient_name,
    visit_type: visit.visit_type,
    weight_kg: visit.weight_kg,
    bp: visit.bp ?? null,
    anc_completed: visit.anc_completed ?? null,
    ifa_provided: visit.ifa_provided ?? null,
    vaccination_status: visit.vaccination_status ?? null,
    vaccines_due: visit.vaccines_due ?? [],
    next_visit_date: visit.next_visit_date,
    observations: visit.observations ?? null,
    language: visit.language ?? "en-IN",
    transcript: visit.transcript ?? "",
    confidence: {},
    extraction_method: visit.extraction_method ?? "rules",
  };
}

function correctionValue(correction: Correction, language: Language): string {
  const value = correction.value;
  if (typeof value === "boolean") return value ? "✓" : "✗";
  if (Array.isArray(value)) return value.join(", ");
  if (value === null || value === undefined || value === "") return S.notSpecified[language];
  return String(value);
}

export function VisitDetailScreen({
  language,
  visit,
  onBack,
  onSave,
  onComplete,
}: {
  language: Language;
  visit: VisitDetail;
  onBack: () => void;
  onSave: (id: string, payload: ManualVisitPayload) => Promise<void>;
  onComplete: (id: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const record = recordFromVisit(visit);
  const danger = Array.isArray(visit.danger_json) ? visit.danger_json : [];
  const corrections = visit.corrections_json ?? [];
  const name = visitDisplayName(visit, language);

  return (
    <div className="space-y-4 pb-24 lg:pb-8">
      <button
        type="button"
        onClick={onBack}
        className="inline-flex items-center gap-1 text-sm font-semibold text-brand-700"
      >
        ← {S.back[language]}
      </button>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-xl font-black text-slate-900">{name}</h2>
          <p className="text-sm text-slate-500">
            {visitTypeLabel(visit.visit_type, language)}
            {visit.beneficiary_id && <span className="text-slate-400"> · {visit.beneficiary_id}</span>}
          </p>
          <p className="mt-1 text-xs text-slate-400">
            {S.recordedOn[language]} {formatDate(visit.created_at.slice(0, 10), language)} ·{" "}
            {timeAgo(visit.created_at, language)} · {visit.id}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge tone="green">{visit.status === "confirmed" ? S.statusConfirmed[language] : visit.status}</Badge>
          <Badge tone="slate">{extractionLabel(visit.extraction_method, language)}</Badge>
          {!editing && (
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="rounded-full bg-brand-700 px-3 py-1.5 text-xs font-bold text-white"
            >
              ✎ {S.editRecord[language]}
            </button>
          )}
        </div>
      </div>

      <DangerBanner hits={danger} language={language} message={null} />

      {editing ? (
        <div className="space-y-3">
          <p className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-relaxed text-amber-800">
            {S.editedNote[language]}
          </p>
          <RecordForm
            language={language}
            initial={record}
            mode="edit"
            busy={busy}
            onCancel={() => setEditing(false)}
            onSubmit={async (payload) => {
              setBusy(true);
              try {
                await onSave(visit.id, payload);
                setEditing(false);
              } finally {
                setBusy(false);
              }
            }}
          />
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.25fr)_minmax(300px,0.75fr)]">
          <div className="space-y-4">
            <RecordCard record={record} language={language} saved />

            <Card className="overflow-hidden">
              <div className="border-b border-slate-100 bg-slate-50/70 px-4 py-2">
                <p className="text-xs font-bold tracking-wide text-slate-500 uppercase">{S.transcript[language]}</p>
              </div>
              <p className="px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap text-slate-700">
                {visit.transcript || S.notSpecified[language]}
              </p>
            </Card>

            <Card className="overflow-hidden">
              <div className="border-b border-slate-100 bg-slate-50/70 px-4 py-2">
                <p className="text-xs font-bold tracking-wide text-slate-500 uppercase">{S.corrections[language]}</p>
              </div>
              {corrections.length ? (
                <ul className="divide-y divide-slate-100">
                  {corrections.map((correction, index) => (
                    <li key={`${correction.field}-${index}`} className="px-4 py-2.5">
                      <p className="text-xs font-semibold text-slate-500">{fieldLabel(correction.field, language)}</p>
                      <p className="text-sm text-slate-800">{correctionValue(correction, language)}</p>
                      {correction.utterance && (
                        <p className="mt-0.5 text-[11px] text-slate-400">“{correction.utterance}”</p>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="px-4 py-3 text-sm text-slate-400">{S.noCorrections[language]}</p>
              )}
            </Card>
          </div>

          <div className="space-y-4">
            <section>
              <SectionTitle
                action={<Badge tone="amber">{visit.followups.filter((task) => task.status !== "done").length} {S.pending[language]}</Badge>}
              >
                {S.followups[language]}
              </SectionTitle>
              <FollowUpList
                tasks={visit.followups.filter((task) => task.status !== "done")}
                language={language}
                onComplete={onComplete}
              />
            </section>
          </div>
        </div>
      )}
    </div>
  );
}
