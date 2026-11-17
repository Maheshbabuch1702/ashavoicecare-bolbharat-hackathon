import type { DangerHit, Language } from "../types";
import { S, dangerLabel } from "../strings";
import { AlertIcon } from "./ui";

export function DangerBanner({
  hits,
  language,
  message,
  onReplay,
}: {
  hits: DangerHit[];
  language: Language;
  message?: string | null;
  onReplay?: () => void;
}) {
  if (!hits.length) return null;
  return (
    <div className="rise overflow-hidden rounded-2xl border-2 border-red-500 bg-red-600 text-white shadow-lg shadow-red-600/20">
      <div className="flex items-start gap-3 p-4">
        <span className="mt-0.5 rounded-full bg-white/20 p-2">
          <AlertIcon className="h-6 w-6" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-base font-bold tracking-tight">{S.dangerAlert[language]}</p>
          <ul className="mt-1 space-y-0.5 text-sm font-medium text-red-50">
            {hits.map((hit) => (
              <li key={hit.code}>• {dangerLabel(hit, language)}</li>
            ))}
          </ul>
          <div className="mt-3 rounded-xl bg-white px-3 py-2 text-sm font-bold text-red-700">
            {message || S.referNow[language]}
          </div>
          <div className="mt-2 flex items-center justify-between gap-2">
            <p className="text-[11px] leading-snug text-red-100/90">
              {S.guideline[language]}: {hits[0].source}
            </p>
            {onReplay && (
              <button
                type="button"
                onClick={onReplay}
                className="shrink-0 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold text-white active:bg-white/25"
              >
                ▶ {S.playAgain[language]}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
