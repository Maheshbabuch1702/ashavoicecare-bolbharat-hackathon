import { useState, type ChangeEvent, type FormEvent, type ReactNode } from "react";
import type { Language, ManualVisitPayload, VisitRecord } from "../types";
import { S, t, visitTypeLabel } from "../strings";
import { Card } from "./ui";

const VISIT_TYPES = [
  "pregnancy_anc",
  "newborn_hbnc",
  "postnatal",
  "immunization",
  "family_planning",
  "general",
];

type Draft = {
  patient_name: string;
  beneficiary_id: string;
  visit_type: string;
  weight_kg: string;
  bp: string;
  anc_completed: string;
  ifa_provided: string;
  vaccination_status: string;
  vaccines_due: string;
  next_visit_date: string;
  observations: string;
};

function fromRecord(record?: Partial<VisitRecord> | null): Draft {
  const bool = (value: boolean | null | undefined) =>
    value === true ? "true" : value === false ? "false" : "";
  return {
    patient_name: record?.patient_name ?? "",
    beneficiary_id: record?.beneficiary_id ?? "",
    visit_type: record?.visit_type ?? "pregnancy_anc",
    weight_kg: record?.weight_kg !== null && record?.weight_kg !== undefined ? String(record.weight_kg) : "",
    bp: record?.bp ?? "",
    anc_completed: bool(record?.anc_completed),
    ifa_provided: bool(record?.ifa_provided),
    vaccination_status: record?.vaccination_status ?? "",
    vaccines_due: (record?.vaccines_due ?? []).join(", "),
    next_visit_date: record?.next_visit_date ?? "",
    observations: record?.observations ?? "",
  };
}

const inputClass =
  "w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-100";

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-bold tracking-wide text-slate-600 uppercase">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-[11px] leading-snug text-slate-400">{hint}</span>}
    </label>
  );
}

export function RecordForm({
  language,
  initial,
  mode,
  busy,
  onSubmit,
  onCancel,
}: {
  language: Language;
  initial?: Partial<VisitRecord> | null;
  mode: "create" | "edit";
  busy?: boolean;
  onSubmit: (payload: ManualVisitPayload) => void;
  onCancel: () => void;
}) {
  const [draft, setDraft] = useState<Draft>(() => fromRecord(initial));
  const [error, setError] = useState<string | null>(null);
  const set = (key: keyof Draft) => (event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setDraft((current) => ({ ...current, [key]: event.target.value }));

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!draft.patient_name.trim() && !draft.beneficiary_id.trim()) {
      setError(t("manualIdentityRequired", language));
      return;
    }
    const weight = draft.weight_kg.trim() === "" ? null : Number(draft.weight_kg);
    if (weight !== null && (Number.isNaN(weight) || weight <= 0)) {
      setError(S.manualWeight[language]);
      return;
    }
    setError(null);
    onSubmit({
      patient_name: draft.patient_name.trim() || null,
      beneficiary_id: draft.beneficiary_id.trim() || null,
      visit_type: draft.visit_type,
      weight_kg: weight,
      bp: draft.bp.trim() || null,
      anc_completed: draft.anc_completed === "" ? null : draft.anc_completed === "true",
      ifa_provided: draft.ifa_provided === "" ? null : draft.ifa_provided === "true",
      vaccination_status: draft.vaccination_status || null,
      vaccines_due: draft.vaccines_due
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      next_visit_date: draft.next_visit_date || null,
      observations: draft.observations.trim() || null,
      language,
    });
  };

  return (
    <form onSubmit={submit} className="space-y-4">
      <Card className="space-y-4 p-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label={S.manualName[language]} hint={S.manualNameHint[language]}>
            <input className={inputClass} value={draft.patient_name} onChange={set("patient_name")} autoComplete="off" />
          </Field>
          <Field label={S.manualId[language]}>
            <input className={inputClass} value={draft.beneficiary_id} onChange={set("beneficiary_id")} placeholder="ASHA102" autoComplete="off" />
          </Field>
          <Field label={S.manualVisitType[language]}>
            <select className={inputClass} value={draft.visit_type} onChange={set("visit_type")}>
              {VISIT_TYPES.map((value) => (
                <option key={value} value={value}>
                  {visitTypeLabel(value, language)}
                </option>
              ))}
            </select>
          </Field>
          <Field label={S.manualWeight[language]}>
            <input className={inputClass} value={draft.weight_kg} onChange={set("weight_kg")} inputMode="decimal" placeholder="55" />
          </Field>
          <Field label={S.manualBp[language]}>
            <input className={inputClass} value={draft.bp} onChange={set("bp")} placeholder={S.manualBpPlaceholder[language]} />
          </Field>
          <Field label={S.manualNextVisit[language]}>
            <input className={inputClass} type="date" value={draft.next_visit_date} onChange={set("next_visit_date")} />
          </Field>
          <Field label={S.manualAnc[language]}>
            <select className={inputClass} value={draft.anc_completed} onChange={set("anc_completed")}>
              <option value="">{S.notRecordedOption[language]}</option>
              <option value="true">{S.completedOption[language]}</option>
              <option value="false">{S.notCompletedOption[language]}</option>
            </select>
          </Field>
          <Field label={S.manualIfa[language]}>
            <select className={inputClass} value={draft.ifa_provided} onChange={set("ifa_provided")}>
              <option value="">{S.notRecordedOption[language]}</option>
              <option value="true">{S.providedOption[language]}</option>
              <option value="false">{S.notProvidedOption[language]}</option>
            </select>
          </Field>
          <Field label={S.manualVaccination[language]}>
            <select className={inputClass} value={draft.vaccination_status} onChange={set("vaccination_status")}>
              <option value="">{S.notRecordedOption[language]}</option>
              <option value="given">{S.givenOption[language]}</option>
              <option value="due">{S.dueOption[language]}</option>
            </select>
          </Field>
          <Field label={S.manualVaccinesDue[language]}>
            <input className={inputClass} value={draft.vaccines_due} onChange={set("vaccines_due")} placeholder="BCG, OPV" />
          </Field>
        </div>
        <Field label={S.manualObservations[language]} hint={S.manualObservationsHint[language]}>
          <textarea
            className={`${inputClass} min-h-24 resize-y`}
            value={draft.observations}
            onChange={set("observations")}
            placeholder={language === "ta-IN" ? "எ.கா. காய்ச்சல் இல்லை, குழந்தை நன்றாக பால் குடிக்கிறது." : language === "hi-IN" ? "जैसे बुखार नहीं, शिशु ठीक दूध पी रहा है." : "e.g. No fever, baby is feeding well."}
          />
        </Field>
      </Card>

      {error && (
        <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm font-semibold text-red-700">
          {error}
        </p>
      )}

      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-600 active:bg-slate-50"
        >
          {S.cancel[language]}
        </button>
        <button
          type="submit"
          disabled={busy}
          className="rounded-xl bg-brand-700 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-brand-700/20 active:bg-brand-800 disabled:opacity-60"
        >
          {busy ? S.manualSaving[language] : mode === "create" ? S.manualSave[language] : S.saveChanges[language]}
        </button>
      </div>
    </form>
  );
}
