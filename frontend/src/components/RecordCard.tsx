import type { ReactNode } from "react";
import type { Language, VisitRecord } from "../types";
import { extractionLabel, fieldLabel, S, visitTypeLabel } from "../strings";
import { formatDate, formatWeight } from "../format";
import { Badge, Card } from "./ui";

function Value({ children, muted }: { children: ReactNode; muted?: boolean }) {
  return (
    <span className={`text-sm font-semibold ${muted ? "text-slate-400 italic" : "text-slate-900"}`}>
      {children}
    </span>
  );
}

function Row({
  field,
  language,
  children,
  missing,
  uncertain,
}: {
  field: string;
  language: Language;
  children: ReactNode;
  missing?: boolean;
  uncertain?: boolean;
}) {
  return (
    <div
      className={`flex items-center justify-between gap-3 border-b border-slate-100 px-4 py-3 last:border-0 ${
        missing ? "bg-amber-50/70" : ""
      }`}
    >
      <div className="min-w-0">
        <p className="text-[13px] font-medium text-slate-500">{fieldLabel(field, language)}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2 text-right">
        {children}
        {missing && <Badge tone="amber">{S.needsAnswer[language]}</Badge>}
        {uncertain && !missing && <Badge tone="slate">{S.confidenceLow[language]}</Badge>}
      </div>
    </div>
  );
}

function statusText(value: boolean | null, language: Language, kind: "anc" | "ifa") {
  if (value === null) return S.notSpecified[language];
  if (kind === "anc") {
    if (value) return language === "ta-IN" ? "முடிந்தது" : language === "hi-IN" ? "पूरी हुई" : "Completed";
    return language === "ta-IN" ? "முடிக்கவில்லை" : language === "hi-IN" ? "नहीं हुई" : "Not completed";
  }
  if (value) return language === "ta-IN" ? "வழங்கப்பட்டது" : language === "hi-IN" ? "दी गई" : "Provided";
  return language === "ta-IN" ? "வழங்கப்படவில்லை" : language === "hi-IN" ? "नहीं दी गई" : "Not provided";
}

export function RecordCard({
  record,
  missing = [],
  unclear = [],
  language,
  dense = false,
  saved = false,
}: {
  record: VisitRecord;
  missing?: string[];
  unclear?: string[];
  language: Language;
  dense?: boolean;
  saved?: boolean;
}) {
  const isMissing = (field: string) => missing.includes(field);
  const isUnclear = (field: string) => unclear.includes(field);

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/70 px-4 py-2.5">
        <p className="text-sm font-bold text-slate-700">{S.recordTitle[language]}</p>
        <div className="flex items-center gap-1.5">
          <Badge tone={saved ? "green" : "teal"}>{saved ? S.statusConfirmed[language] : S.draftBadge[language]}</Badge>
          <Badge tone="slate">{extractionLabel(record.extraction_method, language)}</Badge>
        </div>
      </div>

      <Row field="beneficiary_id" language={language} missing={isMissing("beneficiary_id")}>
        {record.beneficiary_id ? (
          <Value>{record.beneficiary_id}</Value>
        ) : (
          <Value muted>{S.notSpecified[language]}</Value>
        )}
      </Row>

      <Row field="patient_name" language={language} missing={isMissing("patient_name")}>
        {record.patient_name ? (
          <Value>{record.patient_name}</Value>
        ) : (
          <Value muted>{S.notSpecified[language]}</Value>
        )}
      </Row>

      <Row field="visit_type" language={language}>
        <Value>{visitTypeLabel(record.visit_type, language)}</Value>
      </Row>

      {!dense && (
        <Row field="weight_kg" language={language} missing={isMissing("weight_kg")} uncertain={isUnclear("weight_kg")}>
          {record.weight_kg !== null ? (
            <Value>{formatWeight(record.weight_kg, language)}</Value>
          ) : (
            <Value muted>{S.notSpecified[language]}</Value>
          )}
        </Row>
      )}

      {record.bp && (
        <Row field="bp" language={language}>
          <Value>{record.bp}</Value>
        </Row>
      )}

      <Row field="anc_completed" language={language} uncertain={isUnclear("anc_completed")}>
        <Value muted={record.anc_completed === null}>
          {statusText(record.anc_completed, language, "anc")}
        </Value>
      </Row>

      <Row field="ifa_provided" language={language} uncertain={isUnclear("ifa_provided")}>
        <Value muted={record.ifa_provided === null}>
          {statusText(record.ifa_provided, language, "ifa")}
        </Value>
      </Row>

      <Row field="vaccination_status" language={language} uncertain={isUnclear("vaccination_status")}>
        <Value muted={!record.vaccination_status || record.vaccination_status === "not_specified"}>
          {record.vaccination_status === "given"
            ? language === "ta-IN"
              ? "வழங்கப்பட்டது"
              : language === "hi-IN"
                ? "हो गया"
                : "Given"
            : record.vaccination_status === "due"
              ? language === "ta-IN"
                ? "நிலுவை"
                : language === "hi-IN"
                  ? "बाकी"
                  : "Due"
              : S.notSpecified[language]}
          {record.vaccines_due && record.vaccines_due.length > 0 && (
            <span className="ml-1 text-xs font-normal text-slate-400">
              ({record.vaccines_due.join(", ")})
            </span>
          )}
        </Value>
      </Row>

      <Row field="next_visit_date" language={language} missing={isMissing("next_visit_date")}>
        {record.next_visit_date ? (
          <Value>{formatDate(record.next_visit_date, language)}</Value>
        ) : (
          <Value muted>{S.notSpecified[language]}</Value>
        )}
      </Row>

      {record.observations && (
        <div className="border-t border-slate-100 px-4 py-3">
          <p className="text-[13px] font-medium text-slate-500">{fieldLabel("observations", language)}</p>
          <p className="mt-1 text-sm text-slate-800">{record.observations}</p>
        </div>
      )}
    </Card>
  );
}
