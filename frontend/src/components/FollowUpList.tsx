import { useState } from "react";
import type { FollowUp, Language } from "../types";
import { S, followupDetail, followupTitle, followupWho } from "../strings";
import { formatDate, relativeDays } from "../format";
import { Badge, Card, EmptyState } from "./ui";
import { Modal } from "./Modal";

const PRIORITY_STYLES: Record<string, { bar: string; tone: "red" | "amber" | "slate" }> = {
  urgent: { bar: "bg-red-500", tone: "red" },
  high: { bar: "bg-amber-400", tone: "amber" },
  normal: { bar: "bg-slate-300", tone: "slate" },
};

function priorityLabel(priority: string, language: Language) {
  if (priority === "urgent") return S.priorityUrgent[language];
  if (priority === "high") return S.priorityHigh[language];
  return S.priorityNormal[language];
}

function isOverdue(due: string): boolean {
  if (!due) return false;
  const target = new Date(`${due}T00:00:00`);
  if (Number.isNaN(target.getTime())) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return target.getTime() < today.getTime();
}

export function sortFollowups(tasks: FollowUp[]): FollowUp[] {
  const priorityOrder = { urgent: 0, high: 1, normal: 2 } as Record<string, number>;
  return [...tasks].sort((a, b) => {
    // Urgent referrals always stay on top; everything else follows due date,
    // then priority for tasks that share a date.
    const urgent = (task: FollowUp) => (task.priority === "urgent" ? 0 : 1);
    const urgentDiff = urgent(a) - urgent(b);
    if (urgentDiff !== 0) return urgentDiff;
    const dueDiff = (a.due_date || "9999-12-31").localeCompare(b.due_date || "9999-12-31");
    if (dueDiff !== 0) return dueDiff;
    return (priorityOrder[a.priority] ?? 3) - (priorityOrder[b.priority] ?? 3);
  });
}

export function FollowUpList({
  tasks,
  language,
  onComplete,
}: {
  tasks: FollowUp[];
  language: Language;
  onComplete?: (id: string) => void;
}) {
  const [confirming, setConfirming] = useState<FollowUp | null>(null);
  if (!tasks.length) {
    return <EmptyState>{S.followups[language]} · 0</EmptyState>;
  }

  const sorted = sortFollowups(tasks);

  return (
    <>
      <div className="space-y-2">
        {sorted.map((task) => {
          const style = PRIORITY_STYLES[task.priority] ?? PRIORITY_STYLES.normal;
          const overdue = task.priority !== "urgent" && isOverdue(task.due_date);
          return (
            <Card key={task.id ?? `${task.title_key}-${task.due_date}-${task.detail}`} className="relative overflow-hidden">
              <span className={`absolute inset-y-0 left-0 w-1.5 ${style.bar}`} />
              <div className="flex items-start gap-3 py-3 pr-3 pl-4">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <p className="text-sm font-bold text-slate-800">{followupTitle(task, language)}</p>
                    <Badge tone={style.tone}>{priorityLabel(task.priority, language)}</Badge>
                    {overdue && <Badge tone="red">{S.dueOverdue[language]}</Badge>}
                  </div>
                  <p className="mt-0.5 text-xs font-semibold text-slate-600">{followupWho(task, language)}</p>
                  <p className="mt-0.5 text-xs leading-snug text-slate-500">{followupDetail(task, language)}</p>
                  <p className={`mt-1 text-xs font-semibold ${overdue ? "text-red-600" : "text-slate-600"}`}>
                    {formatDate(task.due_date, language)}
                    <span className="ml-1 font-normal text-slate-400">· {relativeDays(task.due_date, language)}</span>
                  </p>
                </div>
                {onComplete && task.id && task.status !== "done" && (
                  <button
                    type="button"
                    onClick={() => setConfirming(task)}
                    className="shrink-0 rounded-full border border-slate-200 px-2.5 py-1 text-[11px] font-semibold text-slate-600 active:bg-slate-50"
                  >
                    {S.markDone[language]}
                  </button>
                )}
              </div>
            </Card>
          );
        })}
      </div>

      <Modal
        open={Boolean(confirming)}
        title={S.confirmDoneTitle[language]}
        closeLabel={S.dismiss[language]}
        onClose={() => setConfirming(null)}
        footer={
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setConfirming(null)}
              className="rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-600"
            >
              {S.cancel[language]}
            </button>
            <button
              type="button"
              onClick={() => {
                if (confirming?.id && onComplete) onComplete(confirming.id);
                setConfirming(null);
              }}
              className="rounded-xl bg-brand-700 px-4 py-3 text-sm font-bold text-white"
            >
              {S.confirmDone[language]}
            </button>
          </div>
        }
      >
        <p className="text-sm leading-relaxed text-slate-600">{S.confirmDoneBody[language]}</p>
        {confirming && (
          <div className="mt-3 rounded-xl bg-slate-50 px-3 py-2">
            <p className="text-sm font-bold text-slate-800">{followupTitle(confirming, language)}</p>
            <p className="text-xs text-slate-500">
              {followupWho(confirming, language)} · {formatDate(confirming.due_date, language)}
            </p>
          </div>
        )}
      </Modal>
    </>
  );
}
