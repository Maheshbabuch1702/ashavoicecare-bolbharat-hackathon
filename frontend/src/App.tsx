import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, wsUrl } from "./api";
import { VoiceClient } from "./audio";
import type {
  BeneficiarySummary,
  DangerHit,
  FollowUp,
  Language,
  ManualVisitPayload,
  Phase,
  ServerMessage,
  Stats,
  VisitDetail,
  VisitRecord,
  VisitSummary,
} from "./types";
import {
  S,
  tf,
} from "./strings";
import { formatLongDate, todayIso } from "./format";
import { greetingKey, loadWorker, saveWorker, type WorkerProfile } from "./worker";
import { LanguageTabs } from "./components/ui";
import { Modal, Toast } from "./components/Modal";
import { HomeScreen } from "./screens/Home";
import { RecordingScreen } from "./screens/Recording";
import { ReviewScreen } from "./screens/Review";
import { SavedScreen } from "./screens/Saved";
import { FollowUpsScreen, HistoryScreen } from "./screens/Lists";
import { ManualScreen } from "./screens/Manual";
import { VisitDetailScreen } from "./screens/VisitDetail";

type Tab = "home" | "followups" | "history";

// End-of-speech: after the worker has spoken, three seconds below the speech
// threshold finalises the note. The mic level is 0..1 (RMS × 6 in audio.ts).
const ENDPOINT_SILENCE_MS = 3_000;
const SPEECH_LEVEL = 0.16;
type AppError = { message: string; kind: "voice" | "general"; openTab?: boolean };
type ToastState = {
  message: string;
  tone?: "success" | "error" | "info";
  actionLabel?: string;
  onAction?: () => void;
};

const EMPTY_STATS: Stats = { today_visits: 0, pending_followups: 0, urgent_alerts: 0, total_visits: 0 };
const LANGUAGES: Language[] = ["en-IN", "ta-IN", "hi-IN"];
const LANGUAGE_KEY = "asha.voicecare.language";

function loadLanguage(): Language {
  try {
    const stored = localStorage.getItem(LANGUAGE_KEY) as Language | null;
    if (stored && LANGUAGES.includes(stored)) return stored;
    const browser = navigator.language;
    if (browser.startsWith("ta")) return "ta-IN";
    if (browser.startsWith("hi")) return "hi-IN";
  } catch {
    // storage can be blocked
  }
  return "en-IN";
}

function mediaErrorName(error: unknown): string {
  return error instanceof Error ? error.name : "";
}

function isInIframe(): boolean {
  try {
    return window.self !== window.top;
  } catch {
    return true;
  }
}

export default function App() {
  const [language, setLanguage] = useState<Language>(loadLanguage);
  const [worker, setWorker] = useState<WorkerProfile>(loadWorker);
  const [profileOpen, setProfileOpen] = useState(false);
  const [newVisitOpen, setNewVisitOpen] = useState(false);
  const [phase, setPhase] = useState<Phase>("home");
  const [tab, setTab] = useState<Tab>("home");

  const [level, setLevel] = useState(0);
  const [speaking, setSpeaking] = useState(false);
  const [saving, setSaving] = useState(false);
  const [starting, setStarting] = useState(false);

  const [transcript, setTranscript] = useState("");
  const [liveText, setLiveText] = useState("");
  const [liveRecord, setLiveRecord] = useState<VisitRecord | null>(null);

  const [record, setRecord] = useState<VisitRecord | null>(null);
  const [missing, setMissing] = useState<string[]>([]);
  const [unclear, setUnclear] = useState<string[]>([]);
  const [danger, setDanger] = useState<DangerHit[]>([]);
  const [alarmMessage, setAlarmMessage] = useState<string | null>(null);
  const [readback, setReadback] = useState("");
  const [followups, setFollowups] = useState<FollowUp[]>([]);
  const [savedId, setSavedId] = useState<string | null>(null);

  const [manualOpen, setManualOpen] = useState(false);
  const [manualInitial, setManualInitial] = useState<Partial<VisitRecord> | null>(null);
  const [manualBusy, setManualBusy] = useState(false);

  const [detailId, setDetailId] = useState<string | null>(null);
  const [detail, setDetail] = useState<VisitDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailReturnTab, setDetailReturnTab] = useState<Tab>("home");

  const [stats, setStats] = useState<Stats>(EMPTY_STATS);
  const [history, setHistory] = useState<VisitSummary[]>([]);
  const [beneficiaries, setBeneficiaries] = useState<BeneficiarySummary[]>([]);
  const [pending, setPending] = useState<FollowUp[]>([]);
  const [error, setError] = useState<AppError | null>(null);
  const [offline, setOffline] = useState(!navigator.onLine);
  const [voiceConfigured, setVoiceConfigured] = useState<boolean | null>(null);
  const [toast, setToast] = useState<ToastState | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const voiceRef = useRef<VoiceClient | null>(null);
  const speechSeq = useRef(0);
  const languageRef = useRef(language);
  const phaseRef = useRef(phase);
  const speakingRef = useRef(speaking);
  const stopVisitRef = useRef<(immediate?: boolean) => void>(() => {});
  const stoppingRef = useRef(false);
  const speechHeardRef = useRef(false);
  const lastSpeechAtRef = useRef(0);
  const heardTextRef = useRef(false);

  useEffect(() => {
    languageRef.current = language;
    try {
      localStorage.setItem(LANGUAGE_KEY, language);
    } catch {
      // ignore storage failures
    }
  }, [language]);

  useEffect(() => {
    phaseRef.current = phase;
  }, [phase]);

  useEffect(() => {
    speakingRef.current = speaking;
  }, [speaking]);

  useEffect(() => {
    const on = () => setOffline(false);
    const off = () => setOffline(true);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
    };
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), toast.actionLabel ? 9_000 : 4_500);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const refreshData = useCallback(async () => {
    const [statsResult, visitsResult, followupsResult, beneficiariesResult] = await Promise.allSettled([
      api.stats(),
      api.visits(200),
      api.followups(),
      api.beneficiaries(),
    ]);
    if (statsResult.status === "fulfilled") setStats(statsResult.value);
    if (visitsResult.status === "fulfilled") setHistory(visitsResult.value);
    if (followupsResult.status === "fulfilled") setPending(followupsResult.value);
    if (beneficiariesResult.status === "fulfilled") setBeneficiaries(beneficiariesResult.value);
  }, []);

  useEffect(() => {
    void refreshData();
  }, [refreshData]);

  // The speech key lives only on the server. Check it before offering voice so
  // a misconfigured deployment fails clearly instead of after the mic opens.
  useEffect(() => {
    let alive = true;
    void api
      .config()
      .then((config) => {
        if (alive) setVoiceConfigured(config.gnani_configured);
      })
      .catch(() => {
        if (alive) setVoiceConfigured(null);
      });
    return () => {
      alive = false;
    };
  }, [newVisitOpen]);

  // ---------------------------------------------------------------- speech
  const stopAudio = useCallback(() => {
    speechSeq.current += 1;
    voiceRef.current?.stop();
    setSpeaking(false);
  }, []);

  const playSpeech = useCallback(async (text: string, lang: Language, mute = false) => {
    const voice = voiceRef.current;
    if (!voice || !text) return;
    const id = ++speechSeq.current;
    setSpeaking(true);
    try {
      try {
        await voice.playPcm(api.speakStream(text, lang), 16000, { mute });
      } catch (err) {
        console.warn("Streaming TTS failed; falling back to WAV", err);
        const wav = await api.speak(text, lang);
        if (id !== speechSeq.current) return;
        await voice.play(wav, { mute });
      }
    } catch (err) {
      console.warn("TTS failed", err);
    } finally {
      if (id === speechSeq.current) setSpeaking(false);
    }
  }, []);

  // --------------------------------------------------------------- socket
  const handleMessage = useCallback(
    (message: ServerMessage) => {
      switch (message.type) {
        case "ready":
          break;
        case "partial":
          heardTextRef.current = true;
          setTranscript(message.transcript);
          setLiveText(message.text);
          setLiveRecord(message.record);
          setDanger(message.danger);
          break;
        case "alarm": {
          setDanger(message.danger);
          setAlarmMessage(message.message);
          void playSpeech(message.message, message.language as Language, true);
          break;
        }
        case "draft":
          setRecord(message.record);
          setMissing(message.missing);
          setUnclear(message.unclear);
          setDanger(message.danger);
          setFollowups(message.followups);
          setReadback(message.readback);
          setTranscript(message.record.transcript);
          setSaving(false);
          setPhase("review");
          break;
        case "speak":
          void playSpeech(message.text, message.language as Language);
          break;
        case "stop_audio":
          stopAudio();
          break;
        case "saved":
          setSavedId(message.visit_id);
          setRecord(message.record);
          setFollowups(message.followups);
          setDanger(message.danger);
          setTranscript(message.transcript);
          setSaving(false);
          setPhase("saved");
          voiceRef.current?.micOff();
          void refreshData();
          setToast({ message: S.visitSaved[languageRef.current], tone: "success" });
          break;
        case "error": {
          const fatal = Boolean(message.fatal);
          setError({
            message: message.message,
            kind: "voice",
          });
          setSaving(false);
          if (fatal || phaseRef.current === "recording") {
            voiceRef.current?.micOff();
            setPhase("home");
          } else if (phaseRef.current === "finalising") {
            stoppingRef.current = false;
            speechHeardRef.current = false;
            lastSpeechAtRef.current = 0;
            heardTextRef.current = false;
            setPhase("recording");
          }
          break;
        }
        default:
          break;
      }
    },
    [playSpeech, refreshData, stopAudio],
  );

  const connect = useCallback(async (): Promise<WebSocket> => {
    const existing = wsRef.current;
    if (existing && existing.readyState === WebSocket.OPEN) return existing;

    return new Promise((resolve, reject) => {
      const socket = new WebSocket(wsUrl(languageRef.current));
      socket.binaryType = "arraybuffer";

      const timer = window.setTimeout(() => {
        socket.close();
        reject(new Error("timeout"));
      }, 8_000);

      socket.onopen = () => {
        window.clearTimeout(timer);
        wsRef.current = socket;
        resolve(socket);
      };
      socket.onerror = () => {
        window.clearTimeout(timer);
        reject(new Error("socket"));
      };
      socket.onmessage = (event) => {
        try {
          handleMessage(JSON.parse(event.data as string) as ServerMessage);
        } catch {
          // ignore malformed frames
        }
      };
      socket.onclose = () => {
        wsRef.current = null;
      };
    });
  }, [handleMessage]);

  const handleLevel = useCallback((value: number) => {
    setLevel(value);
    // Ignore the mic while the agent speaks so read-back audio cannot end the
    // visit; barge-in clears `speaking` and the worker's reply is picked up.
    if (phaseRef.current !== "recording" || speakingRef.current) {
      speechHeardRef.current = false;
      lastSpeechAtRef.current = 0;
      return;
    }
    const now = performance.now();
    if (value > SPEECH_LEVEL) {
      speechHeardRef.current = true;
      lastSpeechAtRef.current = now;
      return;
    }
    if (
      speechHeardRef.current &&
      heardTextRef.current &&
      lastSpeechAtRef.current > 0 &&
      now - lastSpeechAtRef.current >= ENDPOINT_SILENCE_MS
    ) {
      speechHeardRef.current = false;
      lastSpeechAtRef.current = 0;
      stopVisitRef.current(true);
    }
  }, []);

  const ensureVoice = useCallback((): VoiceClient => {
    if (!voiceRef.current) {
      voiceRef.current = new VoiceClient({
        onFrame: (frame) => {
          const socket = wsRef.current;
          if (socket && socket.readyState === WebSocket.OPEN) socket.send(frame);
        },
        onLevel: handleLevel,
        onBargeIn: () => {
          voiceRef.current?.stop();
          speakingRef.current = false;
          speechHeardRef.current = false;
          lastSpeechAtRef.current = 0;
          setSpeaking(false);
          const socket = wsRef.current;
          if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: "barge_in" }));
          }
        },
      });
    }
    return voiceRef.current;
  }, [handleLevel]);

  const resetVisitState = useCallback(() => {
    stoppingRef.current = false;
    speechHeardRef.current = false;
    lastSpeechAtRef.current = 0;
    heardTextRef.current = false;
    setDanger([]);
    setAlarmMessage(null);
    setTranscript("");
    setLiveText("");
    setLiveRecord(null);
    setRecord(null);
    setMissing([]);
    setUnclear([]);
    setFollowups([]);
    setReadback("");
    setSavedId(null);
  }, []);

  const voiceErrorMessage = useCallback((err: unknown): AppError => {
    const name = mediaErrorName(err);
    if (isInIframe()) {
      return { message: S.errorIframe[languageRef.current], kind: "voice", openTab: true };
    }
    if (!window.isSecureContext) {
      return { message: S.errorInsecure[languageRef.current], kind: "voice", openTab: true };
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      return { message: S.errorUnsupported[languageRef.current], kind: "voice" };
    }
    if (name === "NotAllowedError" || name === "PermissionDeniedError" || name === "SecurityError") {
      return { message: S.errorMicDenied[languageRef.current], kind: "voice" };
    }
    if (name === "NotFoundError" || name === "DevicesNotFoundError") {
      return { message: S.errorNoMic[languageRef.current], kind: "voice" };
    }
    if (name === "NotReadableError" || name === "TrackStartError") {
      return { message: S.errorMicBusy[languageRef.current], kind: "voice" };
    }
    if (name === "NotSupportedError") {
      return { message: S.errorUnsupported[languageRef.current], kind: "voice" };
    }
    if (name === "timeout") {
      return { message: S.errorSocket[languageRef.current], kind: "voice" };
    }
    if (name === "socket") {
      return { message: S.errorSocket[languageRef.current], kind: "voice" };
    }
    return { message: S.errorVoiceService[languageRef.current], kind: "voice" };
  }, []);

  // --------------------------------------------------------------- actions
  const startVisit = useCallback(async () => {
    if (starting) return;
    if (voiceConfigured === false) {
      setNewVisitOpen(false);
      setError({ message: S.voiceNotConfigured[languageRef.current], kind: "voice", openTab: true });
      return;
    }
    setNewVisitOpen(false);
    setManualOpen(false);
    setDetailId(null);
    setDetail(null);
    setError(null);
    resetVisitState();
    setTab("home");
    setStarting(true);

    try {
      if (!window.isSecureContext) {
        setError({ message: S.errorInsecure[languageRef.current], kind: "voice", openTab: true });
        return;
      }
      if (!navigator.mediaDevices?.getUserMedia) {
        setError({ message: S.errorUnsupported[languageRef.current], kind: "voice" });
        return;
      }

      // Ask for the microphone before opening the network socket so the worker
      // gets an immediate permission prompt instead of a silent timeout.
      const voice = ensureVoice();
      await voice.start();
      const socket = await connect();
      socket.send(
        JSON.stringify({ type: "start", language: languageRef.current, sample_rate: voice.sampleRate }),
      );
      setPhase("recording");
    } catch (err) {
      voiceRef.current?.micOff();
      setError(voiceErrorMessage(err));
      setPhase("home");
    } finally {
      setStarting(false);
    }
  }, [connect, ensureVoice, resetVisitState, starting, voiceConfigured, voiceErrorMessage]);

  const endVisit = useCallback((immediate = false) => {
    if (stoppingRef.current) return;
    stoppingRef.current = true;
    speechHeardRef.current = false;
    lastSpeechAtRef.current = 0;
    heardTextRef.current = false;
    setPhase("finalising");
    const socket = wsRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "stop", quiet: !immediate }));
    }
  }, []);

  const stopVisit = useCallback(() => endVisit(false), [endVisit]);

  useEffect(() => {
    stopVisitRef.current = endVisit;
  }, [endVisit]);

  const cancelVisit = useCallback(() => {
    stopAudio();
    voiceRef.current?.micOff();
    const socket = wsRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: "cancel" }));
    setPhase("home");
    resetVisitState();
    setSaving(false);
  }, [resetVisitState, stopAudio]);

  const confirmVisit = useCallback(() => {
    const socket = wsRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      setError({ message: S.errorSocket[languageRef.current], kind: "voice" });
      return;
    }
    setSaving(true);
    socket.send(JSON.stringify({ type: "confirm" }));
  }, []);

  const replayRecord = useCallback(() => {
    if (readback) void playSpeech(readback, languageRef.current);
  }, [playSpeech, readback]);

  const replayAlarm = useCallback(() => {
    if (alarmMessage) void playSpeech(alarmMessage, languageRef.current, true);
  }, [alarmMessage, playSpeech]);

  const injectText = useCallback((text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    const socket = wsRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "inject", text: trimmed }));
    } else {
      setError({ message: S.errorSocket[languageRef.current], kind: "voice" });
    }
  }, []);

  const openManual = useCallback(
    (initial: Partial<VisitRecord> | null = null) => {
      if (phase !== "home") cancelVisit();
      setNewVisitOpen(false);
      setDetailId(null);
      setDetail(null);
      setError(null);
      setManualInitial(initial);
      setManualOpen(true);
      setTab("home");
    },
    [cancelVisit, phase],
  );

  const saveManual = useCallback(
    async (payload: ManualVisitPayload) => {
      setManualBusy(true);
      try {
        const result = await api.createManual(payload);
        setRecord(result.record);
        setFollowups(result.followups);
        setDanger(result.danger);
        setTranscript(result.transcript);
        setMissing(result.missing);
        setAlarmMessage(null);
        setSavedId(result.visit_id);
        setManualOpen(false);
        setManualInitial(null);
        setPhase("saved");
        setTab("home");
        setToast({ message: S.manualSavedToast[languageRef.current], tone: "success" });
        void refreshData();
      } catch (err) {
        console.warn("Manual save failed", err);
        setError({
          message: S.errorSaveManual[languageRef.current],
          kind: "general",
        });
      } finally {
        setManualBusy(false);
      }
    },
    [refreshData],
  );

  const completeFollowup = useCallback(
    async (id: string) => {
      const task = pending.find((item) => item.id === id) ?? followups.find((item) => item.id === id);
      setPending((current) => current.filter((item) => item.id !== id));
      setFollowups((current) => current.filter((item) => item.id !== id));
      try {
        await api.completeFollowup(id);
        setToast({
          message: S.taskDone[languageRef.current],
          tone: "success",
          actionLabel: S.undo[languageRef.current],
          onAction: async () => {
            try {
              await api.reopenFollowup(id);
              await refreshData();
              setToast({ message: S.taskRestored[languageRef.current], tone: "info" });
            } catch {
              await refreshData();
            }
          },
        });
        void refreshData();
      } catch {
        setToast({ message: S.errorGeneric[languageRef.current], tone: "error" });
        void refreshData();
      }
      void task;
    },
    [followups, pending, refreshData],
  );

  const openVisit = useCallback(async (id: string) => {
    setDetailReturnTab(tab);
    setDetailId(id);
    setDetail(null);
    setDetailLoading(true);
    setManualOpen(false);
    setTab("history");
    setError(null);
    try {
      const result = await api.visit(id);
      setDetail(result);
    } catch (err) {
      console.warn("Visit load failed", err);
      setError({
        message: S.errorLoadVisit[languageRef.current],
        kind: "general",
      });
      setDetailId(null);
    } finally {
      setDetailLoading(false);
    }
  }, [tab]);

  const saveVisitEdit = useCallback(
    async (id: string, payload: ManualVisitPayload) => {
      try {
        const result = await api.updateVisit(id, payload);
        setDetail(result.visit);
        void refreshData();
        setToast({ message: S.toastUpdated[languageRef.current], tone: "success" });
      } catch (err) {
        console.warn("Visit update failed", err);
        setError({
          message: S.errorUpdateVisit[languageRef.current],
          kind: "general",
        });
        throw err;
      }
    },
    [refreshData],
  );

  const startNew = useCallback(() => {
    setPhase("home");
    setTab("home");
    setDetailId(null);
    setDetail(null);
    setManualOpen(false);
    setManualInitial(null);
    setRecord(null);
    setSavedId(null);
    setTranscript("");
    setLiveRecord(null);
    setDanger([]);
    setFollowups([]);
    setMissing([]);
    setUnclear([]);
    setAlarmMessage(null);
    setError(null);
    void refreshData();
  }, [refreshData]);

  const openTab = useCallback(() => {
    window.open(window.location.href, "_blank", "noopener,noreferrer");
  }, []);

  const greeting = useMemo(
    () => tf(greetingKey(), language, { name: worker.name || S.workerProfile[language] }),
    [language, worker.name],
  );

  // ---------------------------------------------------------------- layout
  const inVisit = phase !== "home";
  const showSidebar = !manualOpen && !detailId && !inVisit;
  const navItems: { key: Tab; icon: string; label: string; badge?: number }[] = [
    { key: "home", icon: "🏠", label: S.homeNav[language] },
    { key: "followups", icon: "✓", label: S.followupsNav[language], badge: pending.length },
    { key: "history", icon: "🕘", label: S.historyNav[language] },
  ];

  return (
    <div className="min-h-full">
      <header className="bg-gradient-to-br from-brand-900 via-brand-700 to-brand-600 text-white shadow-lg">
        <div className="mx-auto flex max-w-screen-2xl items-center gap-2 px-4 py-3 lg:px-8">
          <button
            type="button"
            onClick={() => setNewVisitOpen(true)}
            aria-label={S.newVisit[language]}
            title={S.newVisit[language]}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/15 text-2xl font-black leading-none transition hover:bg-white/25 active:scale-95"
          >
            ＋
          </button>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-black leading-tight">ASHA VoiceCare</p>
            <p className="truncate text-[10px] font-medium tracking-wider text-white/60 uppercase">
              {S.appTagline[language]}
            </p>
          </div>
          <button
            type="button"
            onClick={() => setNewVisitOpen(true)}
            className="hidden rounded-full bg-white px-3 py-1.5 text-xs font-bold text-brand-800 sm:inline-flex"
          >
            ＋ {S.newVisit[language]}
          </button>
          <LanguageTabs value={language} onChange={setLanguage} disabled={inVisit} />
          <button
            type="button"
            onClick={() => setProfileOpen(true)}
            aria-label={S.workerProfile[language]}
            title={S.workerProfile[language]}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/15 text-sm font-black text-white ring-1 ring-white/30 hover:bg-white/25"
          >
            {(worker.name || "A").slice(0, 1).toUpperCase()}
          </button>
        </div>

        {phase === "home" ? (
          <div className="mx-auto max-w-screen-2xl px-4 pb-5 lg:px-8">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div className="min-w-0">
                <h1 className="text-[22px] font-black leading-tight sm:text-2xl">{greeting}</h1>
                <p className="mt-1 text-sm text-white/80">
                  {worker.village || "—"} · {formatLongDate(todayIso(), language)}
                </p>
              </div>
              <p className="hidden max-w-md text-right text-xs leading-relaxed text-white/60 sm:block">
                {S.subtitle[language]}
              </p>
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl px-4 pb-3 text-xs font-semibold text-white/70 lg:px-6">
            {phase === "recording" && S.listening[language]}
            {phase === "finalising" && S.processing[language]}
            {phase === "review" && S.confirm[language]}
            {phase === "saved" && S.savedTitle[language]}
          </div>
        )}
      </header>

      <div className="mx-auto max-w-screen-2xl px-4 pt-4 lg:px-8">
        {offline && (
          <div className="mb-3 rounded-xl bg-slate-800 px-3 py-2 text-xs font-semibold text-white">
            ⚠ {S.offline[language]} — {S.offlineNote[language]}
          </div>
        )}

        {error && (
          <div className="mb-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-red-800">
            <div className="flex items-start gap-2">
              <p className="min-w-0 flex-1 text-xs font-semibold leading-relaxed">{error.message}</p>
              <button
                type="button"
                onClick={() => setError(null)}
                className="shrink-0 text-red-400 hover:text-red-700"
                aria-label={S.dismiss[language]}
              >
                ✕
              </button>
            </div>
            {error.kind === "voice" && (
              <div className="mt-2 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => void startVisit()}
                  className="rounded-lg bg-red-700 px-3 py-1.5 text-[11px] font-bold text-white"
                >
                  {S.retry[language]}
                </button>
                <button
                  type="button"
                  onClick={() => openManual()}
                  className="rounded-lg border border-red-300 bg-white px-3 py-1.5 text-[11px] font-bold text-red-700"
                >
                  ⌨ {S.useManual[language]}
                </button>
                {error.openTab && (
                  <button
                    type="button"
                    onClick={openTab}
                    className="rounded-lg border border-red-300 bg-white px-3 py-1.5 text-[11px] font-bold text-red-700"
                  >
                    ↗ {S.openInNewTab[language]}
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        <div className={showSidebar ? "lg:grid lg:grid-cols-[220px_minmax(0,1fr)] lg:gap-6" : ""}>
          {showSidebar && (
            <aside className="hidden lg:block">
              <div className="sticky top-4 space-y-4">
                <nav className="space-y-1">
                  {navItems.map((item) => (
                    <button
                      key={item.key}
                      type="button"
                      onClick={() => {
                        setTab(item.key);
                        setDetailId(null);
                        setDetail(null);
                      }}
                      className={`flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition ${
                        tab === item.key
                          ? "bg-brand-700 text-white shadow"
                          : "text-slate-600 hover:bg-white hover:text-slate-900"
                      }`}
                    >
                      <span className="text-base leading-none">{item.icon}</span>
                      <span className="flex-1">{item.label}</span>
                      {typeof item.badge === "number" && item.badge > 0 && (
                        <span className={`rounded-full px-1.5 py-0.5 text-[10px] ${tab === item.key ? "bg-white/20" : "bg-slate-200 text-slate-600"}`}>
                          {item.badge}
                        </span>
                      )}
                    </button>
                  ))}
                </nav>

                <button
                  type="button"
                  onClick={() => openManual()}
                  className="w-full rounded-2xl bg-brand-700 px-3 py-3 text-sm font-bold text-white shadow-lg shadow-brand-700/20"
                >
                  ＋ {S.newVisit[language]}
                </button>

                <button
                  type="button"
                  onClick={() => setProfileOpen(true)}
                  className="w-full rounded-2xl border border-slate-200 bg-white p-3 text-left shadow-sm hover:border-brand-300"
                >
                  <p className="text-[10px] font-bold tracking-wide text-slate-400 uppercase">
                    {S.workerProfile[language]}
                  </p>
                  <p className="mt-1 truncate text-sm font-bold text-slate-800">{worker.name}</p>
                  <p className="truncate text-xs text-slate-500">{worker.village}</p>
                  <p className="mt-1 text-[11px] text-slate-400">{formatLongDate(todayIso(), language)}</p>
                </button>
              </div>
            </aside>
          )}

          <main className={showSidebar ? "min-w-0" : "mx-auto min-w-0 max-w-3xl"}>
            {manualOpen ? (
              <ManualScreen
                language={language}
                initial={manualInitial}
                busy={manualBusy}
                onSave={(payload) => void saveManual(payload)}
                onCancel={() => {
                  setManualOpen(false);
                  setManualInitial(null);
                }}
              />
            ) : detailId ? (
              detailLoading || !detail ? (
                <div className="flex items-center justify-center gap-3 py-16 text-sm font-semibold text-slate-500">
                  <span className="h-5 w-5 animate-spin rounded-full border-2 border-brand-200 border-t-brand-700" />
                  {S.processing[language]}
                </div>
              ) : (
                <VisitDetailScreen
                  language={language}
                  visit={detail}
                  onBack={() => {
                    setDetailId(null);
                    setDetail(null);
                    setTab(detailReturnTab);
                  }}
                  onSave={saveVisitEdit}
                  onComplete={completeFollowup}
                />
              )
            ) : phase === "recording" || phase === "finalising" ? (
              <RecordingScreen
                language={language}
                level={level}
                phase={phase}
                transcript={transcript}
                liveText={liveText}
                record={liveRecord}
                danger={danger}
                alarmMessage={alarmMessage}
                onStop={stopVisit}
                onCancel={cancelVisit}
                onManual={() => openManual()}
                onReplayAlarm={replayAlarm}
                onInject={injectText}
              />
            ) : phase === "review" && record ? (
              <ReviewScreen
                language={language}
                record={record}
                missing={missing}
                unclear={unclear}
                danger={danger}
                followups={followups}
                alarmMessage={alarmMessage}
                speaking={speaking || saving}
                level={level}
                onConfirm={confirmVisit}
                onReplay={replayRecord}
                onCancel={cancelVisit}
                onManual={(current) => openManual(current)}
                onReplayAlarm={replayAlarm}
              />
            ) : phase === "saved" && record && savedId ? (
              <SavedScreen
                language={language}
                visitId={savedId}
                record={record}
                followups={followups}
                danger={danger}
                transcript={transcript}
                onNew={startNew}
                onComplete={completeFollowup}
                onOpenVisit={openVisit}
              />
            ) : tab === "home" ? (
              <HomeScreen
                language={language}
                stats={stats}
                history={history}
                pending={pending}
                level={level}
                starting={starting}
                onStart={() => void startVisit()}
                onManual={() => openManual()}
                onOpenLists={(next) => setTab(next)}
                onComplete={completeFollowup}
                onOpenVisit={openVisit}
              />
            ) : tab === "followups" ? (
              <FollowUpsScreen language={language} tasks={pending} onComplete={completeFollowup} />
            ) : (
              <HistoryScreen
                language={language}
                visits={history}
                beneficiaries={beneficiaries}
                onOpenVisit={openVisit}
                onManual={() => openManual()}
              />
            )}
          </main>
        </div>
      </div>

      {phase === "home" && !manualOpen && !detailId && (
        <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-slate-200 bg-white/95 backdrop-blur lg:hidden">
          <div className="pb-safe mx-auto flex max-w-md justify-around px-2 pt-1.5">
            {navItems.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => setTab(item.key)}
                className={`flex flex-1 flex-col items-center gap-0.5 rounded-xl px-2 py-1.5 text-[11px] font-semibold ${
                  tab === item.key ? "text-brand-700" : "text-slate-400"
                }`}
              >
                <span className="text-base leading-none">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </div>
        </nav>
      )}

      <Modal
        open={newVisitOpen}
        title={S.newVisitTitle[language]}
        closeLabel={S.dismiss[language]}
        onClose={() => setNewVisitOpen(false)}
        footer={
          <div className="grid gap-2">
            <button
              type="button"
              onClick={() => void startVisit()}
              disabled={voiceConfigured === false}
              className="w-full rounded-2xl bg-brand-700 px-4 py-3 text-sm font-bold text-white disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500"
            >
              🎙 {S.startVoice[language]}
            </button>
            <button
              type="button"
              onClick={() => openManual()}
              className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm font-bold text-slate-700"
            >
              ⌨ {S.enterManually[language]}
            </button>
          </div>
        }
      >
        <p className="text-sm leading-relaxed text-slate-600">{S.newVisitBody[language]}</p>
        <p
          className={`mt-2 rounded-xl px-3 py-2 text-[11px] ${
            voiceConfigured === false ? "bg-amber-50 text-amber-800" : "bg-slate-50 text-slate-500"
          }`}
        >
          {voiceConfigured === false ? S.voiceNotConfigured[language] : S.voiceNeedsMic[language]}
        </p>
      </Modal>

      <ProfileDialog
        open={profileOpen}
        language={language}
        worker={worker}
        onClose={() => setProfileOpen(false)}
        onSave={(next) => {
          setWorker(next);
          saveWorker(next);
          setProfileOpen(false);
          setToast({ message: S.profileSaved[language], tone: "success" });
        }}
      />

      {toast && (
        <Toast
          message={toast.message}
          tone={toast.tone}
          actionLabel={toast.actionLabel}
          onAction={toast.onAction}
          dismissLabel={S.dismiss[language]}
          onDismiss={() => setToast(null)}
        />
      )}
    </div>
  );
}

function ProfileDialog({
  open,
  language,
  worker,
  onClose,
  onSave,
}: {
  open: boolean;
  language: Language;
  worker: WorkerProfile;
  onClose: () => void;
  onSave: (worker: WorkerProfile) => void;
}) {
  const [name, setName] = useState(worker.name);
  const [village, setVillage] = useState(worker.village);

  useEffect(() => {
    if (open) {
      setName(worker.name);
      setVillage(worker.village);
    }
  }, [open, worker]);

  const inputClass =
    "w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100";

  return (
    <Modal
      open={open}
      title={S.workerProfile[language]}
      closeLabel={S.dismiss[language]}
      onClose={onClose}
      footer={
        <button
          type="button"
          onClick={() => onSave({ name: name.trim() || worker.name, village: village.trim() })}
          className="w-full rounded-2xl bg-brand-700 px-4 py-3 text-sm font-bold text-white"
        >
          {S.saveProfile[language]}
        </button>
      }
    >
      <div className="space-y-3">
        <label className="block">
          <span className="mb-1 block text-xs font-bold tracking-wide text-slate-600 uppercase">{S.workerName[language]}</span>
          <input className={inputClass} value={name} onChange={(event) => setName(event.target.value)} />
        </label>
        <label className="block">
          <span className="mb-1 block text-xs font-bold tracking-wide text-slate-600 uppercase">{S.workerVillage[language]}</span>
          <input className={inputClass} value={village} onChange={(event) => setVillage(event.target.value)} />
        </label>
        <p className="text-[11px] leading-relaxed text-slate-400">{S.profileHint[language]}</p>
      </div>
    </Modal>
  );
}
