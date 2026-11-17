export type Language = "en-IN" | "ta-IN" | "hi-IN";

export type Phase = "home" | "recording" | "finalising" | "review" | "saved";

export interface VisitRecord {
  beneficiary_id: string | null;
  patient_name: string | null;
  visit_type: string;
  weight_kg: number | null;
  bp: string | null;
  anc_completed: boolean | null;
  ifa_provided: boolean | null;
  vaccination_status: string | null;
  vaccines_due: string[];
  next_visit_date: string | null;
  observations: string | null;
  language: string;
  transcript: string;
  confidence: Record<string, number>;
  extraction_method: string;
}

export interface DangerHit {
  code: string;
  category: "pregnancy" | "newborn" | "postpartum";
  label: string;
  label_local: string;
  matched_text: string;
  urgency: string;
  source: string;
}

export interface FollowUp {
  id?: string;
  title: string;
  title_key?: string;
  detail: string;
  due_date: string;
  priority: "urgent" | "high" | "normal";
  reason?: string;
  kind?: string;
  status?: string;
  patient_name?: string | null;
  beneficiary_id?: string | null;
  created_at?: string;
  completed_at?: string | null;
}

export interface Correction {
  field: string;
  value: unknown;
  utterance?: string;
  at?: string;
}

export interface DangerAlert {
  id?: string;
  code: string;
  label: string;
  category: string;
  urgency: string;
  referral_status?: string;
  matched_text?: string;
  source?: string;
}

export interface BeneficiarySummary {
  id: string;
  name: string | null;
  visits: number;
  last_seen: string;
}

export interface Stats {
  today_visits: number;
  pending_followups: number;
  urgent_alerts: number;
  total_visits: number;
}

export interface VisitSummary {
  id: string;
  beneficiary_id: string | null;
  patient_name: string | null;
  visit_type: string;
  weight_kg: number | null;
  bp?: string | null;
  anc_completed?: boolean | null;
  ifa_provided?: boolean | null;
  vaccination_status?: string | null;
  vaccines_due?: string[];
  next_visit_date: string | null;
  observations?: string | null;
  status: string;
  created_at: string;
  transcript?: string;
  language?: string;
  extraction_method?: string;
  danger_json: DangerHit[];
  corrections_json?: Correction[];
  extracted_json?: VisitRecord;
  followups?: FollowUp[];
  alerts?: DangerAlert[];
}

export interface VisitDetail extends VisitSummary {
  followups: FollowUp[];
  alerts: DangerAlert[];
}

export interface ManualVisitPayload {
  beneficiary_id: string | null;
  patient_name: string | null;
  visit_type: string;
  weight_kg: number | null;
  bp: string | null;
  anc_completed: boolean | null;
  ifa_provided: boolean | null;
  vaccination_status: string | null;
  vaccines_due: string[];
  next_visit_date: string | null;
  observations: string | null;
  language: string;
}

export interface ManualVisitResponse {
  visit_id: string;
  record: VisitRecord;
  transcript: string;
  followups: FollowUp[];
  danger: DangerHit[];
  missing: string[];
  saved_at: string;
  source: string;
}

export type ServerMessage =
  | { type: "ready"; language: string; gnani_configured: boolean }
  | { type: "recording"; language: string; sample_rate: number; frame_bytes: number }
  | { type: "stt_connected"; config: Record<string, unknown> }
  | { type: "speech_start" }
  | { type: "partial"; text: string; transcript: string; record: VisitRecord; danger: DangerHit[] }
  | {
      type: "alarm";
      danger: DangerHit[];
      new: DangerHit[];
      message: string;
      language: string;
    }
  | {
      type: "draft";
      record: VisitRecord;
      missing: string[];
      unclear: string[];
      danger: DangerHit[];
      followups: FollowUp[];
      readback: string;
      language: string;
      corrected?: boolean;
    }
  | {
      type: "saved";
      visit_id: string;
      beneficiary_id: string | null;
      followups: FollowUp[];
      danger: DangerHit[];
      record: VisitRecord;
      transcript: string;
      saved_at: string;
    }
  | { type: "speak"; id: number; text: string; language: string }
  | { type: "stop_audio" }
  | { type: "language_changed"; language: string }
  | { type: "pong" }
  | { type: "error"; message: string; fatal?: boolean };
