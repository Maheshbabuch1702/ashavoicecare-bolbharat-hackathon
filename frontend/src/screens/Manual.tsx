import type { Language, ManualVisitPayload, VisitRecord } from "../types";
import { S } from "../strings";
import { RecordForm } from "../components/RecordForm";

export function ManualScreen({
  language,
  initial,
  busy,
  onSave,
  onCancel,
}: {
  language: Language;
  initial?: Partial<VisitRecord> | null;
  busy: boolean;
  onSave: (payload: ManualVisitPayload) => void;
  onCancel: () => void;
}) {
  return (
    <div className="space-y-4 pb-24 lg:pb-8">
      <button
        type="button"
        onClick={onCancel}
        className="inline-flex items-center gap-1 text-sm font-semibold text-brand-700"
      >
        ← {S.back[language]}
      </button>
      <div>
        <h2 className="text-xl font-black text-slate-900">{S.manualTitle[language]}</h2>
        <p className="mt-1 max-w-2xl text-sm leading-relaxed text-slate-500">{S.manualSubtitle[language]}</p>
      </div>
      <RecordForm
        language={language}
        initial={initial}
        mode="create"
        busy={busy}
        onSubmit={onSave}
        onCancel={onCancel}
      />
    </div>
  );
}
