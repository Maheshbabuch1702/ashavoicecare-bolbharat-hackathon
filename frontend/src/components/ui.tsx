import type { ReactNode } from "react";
import type { Language } from "../types";
import { S } from "../strings";

export function MicIcon({ className = "h-14 w-14" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className={className}
      strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <rect x="9" y="2" width="6" height="12" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0" />
      <path d="M12 18v3" />
    </svg>
  );
}

export function StopIcon({ className = "h-12 w-12" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden>
      <rect x="6" y="6" width="12" height="12" rx="2.5" />
    </svg>
  );
}

export function AlertIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={className}
      strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
      <path d="M12 9v4" />
      <path d="M12 17h.01" />
    </svg>
  );
}

export function CheckIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.4} className={className}
      strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="m20 6-11 11-5-5" />
    </svg>
  );
}

export function PlusIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} className={className}
      strokeLinecap="round" aria-hidden>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function SearchIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={className}
      strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  );
}

export function SettingsIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className={className}
      strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.88-.34 1.7 1.7 0 0 0-1 1.55V21a2 2 0 1 1-4 0v-.09a1.7 1.7 0 0 0-1.11-1.55 1.7 1.7 0 0 0-1.88.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.55-1H3a2 2 0 1 1 0-4h.09A1.7 1.7 0 0 0 4.64 8.9a1.7 1.7 0 0 0-.34-1.88l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.55V3a2 2 0 1 1 4 0v.09a1.7 1.7 0 0 0 1 1.55 1.7 1.7 0 0 0 1.88-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 9v.09a1.7 1.7 0 0 0 1.55 1H21a2 2 0 1 1 0 4h-.09a1.7 1.7 0 0 0-1.55 1Z" />
    </svg>
  );
}

export function ArrowLeftIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={className}
      strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="m15 18-6-6 6-6" />
    </svg>
  );
}

export function ChevronRightIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={className}
      strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="m9 18 6-6-6-6" />
    </svg>
  );
}

export function Spinner({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <span
      className={`inline-block animate-spin rounded-full border-2 border-current border-t-transparent ${className}`}
      aria-hidden
    />
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-2xl border border-slate-200 bg-white shadow-sm ${className}`}>{children}</div>
  );
}

export function SectionTitle({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div className="mb-2 flex items-center justify-between px-1">
      <h2 className="text-sm font-semibold tracking-wide text-slate-500 uppercase">{children}</h2>
      {action}
    </div>
  );
}

export function Badge({
  children,
  tone = "slate",
}: {
  children: ReactNode;
  tone?: "slate" | "amber" | "red" | "green" | "teal";
}) {
  const tones: Record<string, string> = {
    slate: "bg-slate-100 text-slate-600",
    amber: "bg-amber-100 text-amber-800",
    red: "bg-red-100 text-red-700",
    green: "bg-emerald-100 text-emerald-700",
    teal: "bg-brand-100 text-brand-700",
  };
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold ${tones[tone]}`}>
      {children}
    </span>
  );
}

export function LanguageTabs({
  value,
  onChange,
  disabled,
}: {
  value: Language;
  onChange: (language: Language) => void;
  disabled?: boolean;
}) {
  const options: { code: Language; label: string }[] = [
    { code: "ta-IN", label: "தமிழ்" },
    { code: "en-IN", label: "English" },
    { code: "hi-IN", label: "हिन्दी" },
  ];
  return (
    <div className="flex rounded-full bg-white/15 p-1 backdrop-blur">
      {options.map((option) => (
        <button
          key={option.code}
          type="button"
          disabled={disabled}
          onClick={() => onChange(option.code)}
          className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
            value === option.code ? "bg-white text-brand-800 shadow" : "text-white/80"
          } ${disabled ? "opacity-50" : ""}`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

export function VoiceOrb({
  active,
  level,
  onClick,
  label,
  hint,
  language,
}: {
  active: boolean;
  level: number;
  onClick: () => void;
  label: string;
  hint?: string;
  language: Language;
}) {
  const scale = 1 + Math.min(level, 1) * 0.08;
  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative flex h-44 w-44 items-center justify-center">
        {active && <span className="ring-pulse absolute inset-5 rounded-full text-brand-500/50" />}
        <span className={`absolute inset-0 rounded-full ${active ? "bg-brand-500/10" : "bg-brand-50"}`} />
        <button
          type="button"
          onClick={onClick}
          aria-label={label}
          style={{ transform: `scale(${scale})` }}
          className={`relative z-10 flex h-36 w-36 items-center justify-center rounded-full text-white shadow-lg transition-transform duration-100 active:scale-95 ${
            active ? "bg-red-500 shadow-red-500/30" : "bg-brand-700 shadow-brand-700/30"
          }`}
        >
          {active ? <StopIcon /> : <MicIcon />}
        </button>
      </div>
      <div className="text-center">
        <p className="text-base font-semibold text-slate-800">{label}</p>
        {hint && <p className="mt-1 text-sm text-slate-500">{hint}</p>}
        {active && (
          <p className="mt-1 text-xs font-medium text-brand-700">{S.listening[language]}</p>
        )}
      </div>
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white/60 px-4 py-8 text-center text-sm text-slate-500">
      {children}
    </div>
  );
}
