import type { FollowUp, Language, Stats, VisitSummary } from "../types";
import { S, tf, visitDisplayName, visitTypeLabel } from "../strings";
import { formatWeight, timeAgo } from "../format";
import { Card, ChevronRightIcon, EmptyState, SectionTitle, Spinner, VoiceOrb } from "../components/ui";
import { FollowUpList } from "../components/FollowUpList";

function Stat({
  value,
  label,
  tone = "teal",
  onClick,
}: {
  value: number;
  label: string;
  tone?: "teal" | "amber" | "red" | "slate";
  onClick?: () => void;
}) {
  const tones = {
    teal: "text-brand-700",
    amber: "text-amber-600",
    red: "text-red-600",
    slate: "text-slate-700",
  } as const;
  const content = (
    <Card className={`h-full px-4 py-3 ${onClick ? "transition hover:border-brand-300" : ""}`}>
      <p className={`text-3xl font-black tabular-nums ${tones[tone]}`}>{value}</p>
      <p className="mt-0.5 text-[11px] leading-tight font-semibold tracking-wide text-slate-500 uppercase">
        {label}
      </p>
    </Card>
  );
  return onClick ? (
    <button type="button" onClick={onClick} className="text-left">
      {content}
    </button>
  ) : (
    content
  );
}

function VisitRow({
  visit,
  language,
  onOpen,
}: {
  visit: VisitSummary;
  language: Language;
  onOpen: (id: string) => void;
}) {
  const hasDanger = Array.isArray(visit.danger_json) && visit.danger_json.length > 0;
  const name = visitDisplayName(visit, language);
  return (
    <button
      type="button"
      onClick={() => onOpen(visit.id)}
      className="flex w-full items-center gap-3 border-b border-slate-100 px-4 py-3 text-left last:border-0 hover:bg-slate-50"
    >
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
          hasDanger ? "bg-red-100 text-red-600" : "bg-brand-50 text-brand-700"
        }`}
      >
        {(visit.patient_name || "?").slice(0, 1).toUpperCase()}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-slate-800">
          {name}
          {hasDanger && <span className="ml-1.5 text-[11px] font-bold text-red-600">● {S.dangerShort[language]}</span>}
        </p>
        <p className="truncate text-xs text-slate-500">
          {visitTypeLabel(visit.visit_type, language)}
          {visit.weight_kg ? ` · ${formatWeight(visit.weight_kg, language)}` : ""}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-1">
        <p className="text-[11px] font-medium text-slate-400">{timeAgo(visit.created_at, language)}</p>
        <ChevronRightIcon className="h-4 w-4 text-slate-300" />
      </div>
    </button>
  );
}

export function HomeScreen({
  language,
  stats,
  history,
  pending,
  level,
  starting,
  onStart,
  onManual,
  onOpenLists,
  onComplete,
  onOpenVisit,
}: {
  language: Language;
  stats: Stats;
  history: VisitSummary[];
  pending: FollowUp[];
  level: number;
  starting: boolean;
  onStart: () => void;
  onManual: () => void;
  onOpenLists: (tab: "followups" | "history") => void;
  onComplete: (id: string) => void;
  onOpenVisit: (id: string) => void;
}) {
  const urgentText =
    stats.urgent_alerts === 1
      ? tf("urgentReferralsPending", language, { count: stats.urgent_alerts })
      : tf("urgentReferralsPendingPlural", language, { count: stats.urgent_alerts });

  return (
    <div className="space-y-5 pb-24 lg:pb-8">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat value={stats.today_visits} label={S.todayVisits[language]} />
        <Stat
          value={stats.pending_followups}
          label={S.followupsPending[language]}
          tone="amber"
          onClick={() => onOpenLists("followups")}
        />
        <Stat
          value={stats.urgent_alerts}
          label={S.urgentAlerts[language]}
          tone="red"
          onClick={() => onOpenLists("followups")}
        />
        <Stat value={stats.total_visits} label={S.totalVisits[language]} tone="slate" onClick={() => onOpenLists("history")} />
      </div>

      {stats.urgent_alerts > 0 && (
        <button
          type="button"
          onClick={() => onOpenLists("followups")}
          className="w-full rounded-2xl border-2 border-red-400 bg-red-50 px-4 py-3 text-left"
        >
          <p className="text-sm font-bold text-red-700">{urgentText}</p>
          <p className="text-xs text-red-600">{S.tapOpenFollowups[language]}</p>
        </button>
      )}

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.75fr)]">
        <div className="space-y-5">
          <Card className="flex flex-col items-center px-4 py-7">
            {starting ? (
              <div className="flex flex-col items-center gap-3 py-10">
                <Spinner className="h-10 w-10 text-brand-700" />
                <p className="text-sm font-semibold text-slate-700">{S.startingMic[language]}</p>
              </div>
            ) : (
              <VoiceOrb
                active={false}
                level={level}
                onClick={onStart}
                label={S.tapToSpeak[language]}
                hint={S.subtitle[language]}
                language={language}
              />
            )}
            <button
              type="button"
              onClick={onManual}
              className="mt-5 w-full max-w-sm rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm font-bold text-slate-700 active:bg-slate-50"
            >
              ⌨ {S.enterManually[language]}
            </button>
            <p className="mt-2 text-center text-[11px] text-slate-400">{S.manualFallback[language]}</p>
          </Card>

          <section>
            <SectionTitle
              action={
                <button
                  type="button"
                  onClick={() => onOpenLists("followups")}
                  className="text-xs font-semibold text-brand-700"
                >
                  {S.viewAll[language]}
                </button>
              }
            >
              {S.followups[language]}
            </SectionTitle>
            <FollowUpList tasks={pending.slice(0, 3)} language={language} onComplete={onComplete} />
          </section>
        </div>

        <div className="space-y-5">
          <section>
            <SectionTitle
              action={
                <button
                  type="button"
                  onClick={() => onOpenLists("history")}
                  className="text-xs font-semibold text-brand-700"
                >
                  {S.viewAll[language]}
                </button>
              }
            >
              {S.recentVisits[language]}
            </SectionTitle>
            {history.length ? (
              <Card className="overflow-hidden">
                {history.slice(0, 5).map((visit) => (
                  <VisitRow key={visit.id} visit={visit} language={language} onOpen={onOpenVisit} />
                ))}
              </Card>
            ) : (
              <EmptyState>{S.noVisits[language]}</EmptyState>
            )}
          </section>

          <Card className="border-brand-200 bg-brand-50/60 p-4">
            <p className="text-xs font-bold tracking-wide text-brand-800 uppercase">{S.quickActions[language]}</p>
            <div className="mt-2 grid gap-2">
              <button
                type="button"
                onClick={onManual}
                className="rounded-xl bg-white px-3 py-2.5 text-left text-sm font-semibold text-slate-700 shadow-sm active:bg-slate-50"
              >
                ⌨ {S.enterManually[language]}
              </button>
              <button
                type="button"
                onClick={() => onOpenLists("followups")}
                className="rounded-xl bg-white px-3 py-2.5 text-left text-sm font-semibold text-slate-700 shadow-sm active:bg-slate-50"
              >
                ✓ {S.followupsNav[language]} <span className="text-slate-400">({pending.length})</span>
              </button>
              <button
                type="button"
                onClick={() => onOpenLists("history")}
                className="rounded-xl bg-white px-3 py-2.5 text-left text-sm font-semibold text-slate-700 shadow-sm active:bg-slate-50"
              >
                🕘 {S.historyNav[language]}
              </button>
            </div>
          </Card>

          <p className="px-2 text-center text-[11px] leading-relaxed text-slate-400">{S.understandNote[language]}</p>
        </div>
      </div>
    </div>
  );
}
