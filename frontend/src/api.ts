import type {
  BeneficiarySummary,
  FollowUp,
  ManualVisitPayload,
  ManualVisitResponse,
  Stats,
  VisitDetail,
  VisitSummary,
} from "./types";

const configuredBase = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
const BASE = configuredBase.replace(/\/$/, "");

export function wsUrl(language: string): string {
  const base = BASE
    ? BASE.replace(/^http/, "ws")
    : `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}`;
  return `${base}/ws/visit?language=${encodeURIComponent(language)}`;
}

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    let detail = "";
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // non-JSON error body
    }
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return (await response.json()) as T;
}

export const api = {
  config: () => json<{ languages: { code: string; label: string }[]; gnani_configured: boolean }>("/api/config"),

  stats: () => json<Stats>("/api/stats"),

  visits: (limit = 200) =>
    json<{ visits: VisitSummary[] }>(`/api/visits?limit=${limit}`).then((data) => data.visits),

  visit: (id: string) => json<VisitDetail>(`/api/visits/${encodeURIComponent(id)}`),

  beneficiaries: (search = "") =>
    json<{ beneficiaries: BeneficiarySummary[] }>(
      `/api/beneficiaries?search=${encodeURIComponent(search)}`,
    ).then((data) => data.beneficiaries),

  createManual: (payload: ManualVisitPayload) =>
    json<ManualVisitResponse>("/api/visits/manual", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateVisit: (id: string, payload: Partial<ManualVisitPayload>) =>
    json<{ ok: boolean; visit: VisitDetail }>(`/api/visits/${encodeURIComponent(id)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  followups: () => json<{ followups: FollowUp[] }>("/api/followups?status=pending").then((data) => data.followups),

  completeFollowup: (id: string) => json<{ ok: boolean }>(`/api/followups/${id}/complete`, { method: "POST" }),

  reopenFollowup: (id: string) => json<{ ok: boolean }>(`/api/followups/${id}/reopen`, { method: "POST" }),

  async speak(text: string, language: string): Promise<ArrayBuffer> {
    const response = await fetch(`${BASE}/api/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, language }),
    });
    if (!response.ok) throw new Error("Text-to-speech failed");
    return response.arrayBuffer();
  },

  /** Yield 16-bit mono PCM chunks as Gnani synthesises them. */
  async *speakStream(text: string, language: string): AsyncGenerator<Int16Array> {
    const response = await fetch(`${BASE}/api/tts/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, language }),
    });
    if (!response.ok || !response.body) throw new Error("Text-to-speech stream failed");
    const reader = response.body.getReader();
    let carry = new Uint8Array(0);
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (!value || value.length === 0) continue;
        const bytes = new Uint8Array(carry.length + value.length);
        bytes.set(carry);
        bytes.set(value, carry.length);
        const even = bytes.length - (bytes.length % 2);
        if (even === 0) {
          carry = bytes;
          continue;
        }
        const view = new DataView(bytes.buffer, bytes.byteOffset, even);
        const pcm = new Int16Array(even / 2);
        for (let i = 0; i < pcm.length; i += 1) pcm[i] = view.getInt16(i * 2, true);
        carry = bytes.slice(even);
        yield pcm;
      }
    } finally {
      await reader.cancel().catch(() => undefined);
    }
  },
};
