import { useMemo, useState } from "react";
import type { BeneficiarySummary, FollowUp, Language, VisitSummary } from "../types";
import { S, dangerLabel, tf, visitDisplayName, visitTypeLabel } from "../strings";
import { formatDate, formatWeight, timeAgo, todayIso } from "../format";
import { Badge, Card, ChevronRightIcon, EmptyState, SearchIcon } from "../components/ui";
import { FollowUpList, sortFollowups } from "../components/FollowUpList";

function dueBucket(task: FollowUp): "urgent" | "overdue" | "today" | "soon" | "later" {
  if (task.priority === "urgent") return "urgent";
  if (!task.due_date) return "later";
  const today = todayIso();
  if (task.due_date < today) return "overdue";
  if (task.due_date === today) return "today";
  const target = new Date(`${task.due_date}T00:00:00`);
  const now = new Date(`${today}T00:00:00`);
  const days = Math.round((target.getTime() - now.getTime()) / 86_400_000);
  return days <= 7 ? "soon" : "later";
}

export function FollowUpsScreen({
  language,
  tasks,
  onComplete,
}: {
  language: Language;
  tasks: FollowUp[];
  onComplete: (id: string) => void;
}) {
  const [filter, setFilter] = useState<"all" | "urgent" | "overdue" | "upcoming">("all");
  const pending = tasks.filter((task) => task.status !== "done");
  const urgent = pending.filter((task) => task.priority === "urgent").length;

  const filtered = useMemo(() => {
    if (filter === "urgent") return pending.filter((task) => task.priority === "urgent");
    if (filter === "overdue") return pending.filter((task) => dueBucket(task) === "overdue");
    if (filter === "upcoming") return pending.filter((task) => ["today", "soon"].includes(dueBucket(task)));
    return pending;
  }, [filter, pending]);

  const groups = useMemo(() => {
    const buckets: { key: "urgent" | "overdue" | "today" | "soon" | "later"; label: string; tasks: FollowUp[] }[] = [
      { key: "urgent", label: S.filterUrgent[language], tasks: [] },
      { key: "overdue", label: S.dueOverdue[language], tasks: [] },
      { key: "today", label: S.dueToday[language], tasks: [] },
      { key: "soon", label: S.dueSoon[language], tasks: [] },
      { key: "later", label: S.dueLater[language], tasks: [] },
    ];
    for (const task of sortFollowups(filtered)) {
      buckets.find((bucket) => bucket.key === dueBucket(task))?.tasks.push(task);
    }
    return buckets.filter((bucket) => bucket.tasks.length > 0);
  }, [filtered, language]);

  const filters: { key: typeof filter; label: string }[] = [
    { key: "all", label: S.filterAll[language] },
    { key: "urgent", label: S.filterUrgent[language] },
    { key: "overdue", label: S.filterOverdue[language] },
    { key: "upcoming", label: S.filterUpcoming[language] },
  ];

  return (
    <div className="space-y-4 pb-24 lg:pb-8">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-xl font-black text-slate-900">{S.followups[language]}</h2>
        <Badge tone="amber">{pending.length} {S.pending[language]}</Badge>
        {urgent > 0 && <Badge tone="red">{urgent} {S.urgent[language]}</Badge>}
      </div>
      <p className="-mt-2 text-xs text-slate-500">{S.generatedAutomatically[language]}</p>

      <div className="flex flex-wrap gap-1.5">
        {filters.map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => setFilter(item.key)}
            className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
              filter === item.key ? "bg-brand-700 text-white" : "bg-white text-slate-600 ring-1 ring-slate-200"
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {groups.length ? (
        <div className="space-y-5">
          {groups.map((group) => (
            <section key={group.key}>
              <div className="mb-2 flex items-center gap-2 px-1">
                <h3
                  className={`text-xs font-bold tracking-wide uppercase ${
                    group.key === "urgent" || group.key === "overdue" ? "text-red-600" : "text-slate-500"
                  }`}
                >
                  {group.label}
                </h3>
                <span className="text-[11px] text-slate-400">{group.tasks.length}</span>
              </div>
              <FollowUpList tasks={group.tasks} language={language} onComplete={onComplete} />
            </section>
          ))}
        </div>
      ) : (
        <EmptyState>{filter === "all" ? S.noPendingTasks[language] : S.noResults[language]}</EmptyState>
      )}
    </div>
  );
}

export function HistoryScreen({
  language,
  visits,
  beneficiaries,
  onOpenVisit,
  onManual,
}: {
  language: Language;
  visits: VisitSummary[];
  beneficiaries: BeneficiarySummary[];
  onOpenVisit: (id: string) => void;
  onManual: () => void;
}) {
  const [search, setSearch] = useState("");
  const [beneficiary, setBeneficiary] = useState("");
  const [visitType, setVisitType] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return visits.filter((visit) => {
      if (beneficiary) {
        if (beneficiary.startsWith("NAME:")) {
          if ((visit.patient_name || "").toLowerCase() !== beneficiary.slice(5)) return false;
        } else if (visit.beneficiary_id !== beneficiary) {
          return false;
        }
      }
      if (visitType && visit.visit_type !== visitType) return false;
      const day = (visit.created_at || "").slice(0, 10);
      if (fromDate && day < fromDate) return false;
      if (toDate && day > toDate) return false;
      if (!needle) return true;
      return [visit.patient_name, visit.beneficiary_id, visit.transcript, visit.observations]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle));
    });
  }, [visits, search, beneficiary, visitType, fromDate, toDate]);

  const hasFilters = Boolean(search || beneficiary || visitType || fromDate || toDate);
  const clear = () => {
    setSearch("");
    setBeneficiary("");
    setVisitType("");
    setFromDate("");
    setToDate("");
  };

  const inputClass =
    "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100";

  return (
    <div className="space-y-4 pb-24 lg:pb-8">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="text-xl font-black text-slate-900">{S.recentVisits[language]}</h2>
          <p className="text-xs text-slate-500">
            {filtered.length === 1
              ? S.resultsCountOne[language]
              : tf("resultsCount", language, { count: filtered.length })}
          </p>
        </div>
        {hasFilters && (
          <button type="button" onClick={clear} className="text-xs font-semibold text-brand-700">
            {S.clearFilters[language]}
          </button>
        )}
      </div>

      <Card className="space-y-3 p-3">
        <div className="relative">
          <SearchIcon className="pointer-events-none absolute top-2.5 left-3 h-4 w-4 text-slate-400" />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder={S.searchPlaceholder[language]}
            className={`${inputClass} pl-9`}
          />
        </div>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          <select value={beneficiary} onChange={(event) => setBeneficiary(event.target.value)} className={inputClass}>
            <option value="">{S.allPatients[language]}</option>
            {beneficiaries.map((person) => (
              <option key={person.id} value={person.id}>
                {person.name || person.id} ({person.visits})
              </option>
            ))}
          </select>
          <select value={visitType} onChange={(event) => setVisitType(event.target.value)} className={inputClass}>
            <option value="">{S.allTypes[language]}</option>
            {["pregnancy_anc", "newborn_hbnc", "postnatal", "immunization", "family_planning", "general"].map((value) => (
              <option key={value} value={value}>
                {visitTypeLabel(value, language)}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-[11px] font-semibold text-slate-500">
            {S.dateFrom[language]}
            <input type="date" value={fromDate} onChange={(event) => setFromDate(event.target.value)} className={inputClass} />
          </label>
          <label className="flex items-center gap-2 text-[11px] font-semibold text-slate-500">
            {S.dateTo[language]}
            <input type="date" value={toDate} onChange={(event) => setToDate(event.target.value)} className={inputClass} />
          </label>
        </div>
      </Card>

      {filtered.length ? (
        <div className="grid gap-2 lg:grid-cols-2">
          {filtered.map((visit) => {
            const danger = Array.isArray(visit.danger_json) ? visit.danger_json : [];
            const name = visitDisplayName(visit, language);
            return (
              <button
                key={visit.id}
                type="button"
                onClick={() => onOpenVisit(visit.id)}
                className="text-left"
              >
                <Card className="h-full px-4 py-3 transition hover:border-brand-300 hover:shadow-md">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-bold text-slate-900">
                        {name}{" "}
                        {visit.beneficiary_id && (
                          <span className="text-xs font-medium text-slate-400">{visit.beneficiary_id}</span>
                        )}
                      </p>
                      <p className="text-xs text-slate-500">
                        {visitTypeLabel(visit.visit_type, language)}
                        {visit.weight_kg ? ` · ${formatWeight(visit.weight_kg, language)}` : ""}
                      </p>
                      <p className="mt-1 text-[11px] text-slate-400">
                        {S.nextVisitShort[language]} {formatDate(visit.next_visit_date, language) || "—"} ·{" "}
                        {timeAgo(visit.created_at, language)}
                      </p>
                    </div>
                    <div className="flex shrink-0 flex-col items-end gap-1">
                      {danger.length > 0 && <Badge tone="red">{S.dangerShort[language]}</Badge>}
                      <Badge tone="green">
                        {visit.status === "confirmed" ? S.statusConfirmed[language] : visit.status}
                      </Badge>
                      <ChevronRightIcon className="h-4 w-4 text-slate-300" />
                    </div>
                  </div>
                  {danger.length > 0 && (
                    <p className="mt-2 line-clamp-2 rounded-lg bg-red-50 px-2 py-1 text-[11px] text-red-700">
                      {danger.map((hit) => dangerLabel(hit, language)).join(" · ")}
                    </p>
                  )}
                </Card>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="space-y-3">
          <EmptyState>{hasFilters ? S.noResults[language] : S.noVisits[language]}</EmptyState>
          <button
            type="button"
            onClick={onManual}
            className="w-full rounded-2xl bg-brand-700 px-4 py-3 text-sm font-bold text-white"
          >
            ⌨ {S.enterManually[language]}
          </button>
        </div>
      )}
    </div>
  );
}
