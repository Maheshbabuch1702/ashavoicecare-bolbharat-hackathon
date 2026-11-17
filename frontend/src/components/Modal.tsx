import { useEffect, type ReactNode } from "react";
import { CheckIcon } from "./ui";

export function Modal({
  open,
  title,
  onClose,
  children,
  footer,
  wide = false,
  closeLabel = "Close",
}: {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  wide?: boolean;
  closeLabel?: string;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = previous;
    };
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/45 p-0 backdrop-blur-sm sm:items-center sm:p-4">
      <button
        type="button"
        aria-label={closeLabel}
        onClick={onClose}
        className="absolute inset-0 cursor-default"
        tabIndex={-1}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`rise relative w-full ${wide ? "sm:max-w-2xl" : "sm:max-w-md"} max-h-[92vh] overflow-y-auto rounded-t-3xl bg-white p-5 shadow-2xl sm:rounded-3xl`}
      >
        <div className="mb-3 flex items-start justify-between gap-3">
          <h2 className="text-lg font-black text-slate-900">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label={closeLabel}
            className="rounded-full bg-slate-100 px-2.5 py-1 text-sm font-bold text-slate-500 active:bg-slate-200"
          >
            ✕
          </button>
        </div>
        {children}
        {footer && <div className="mt-5">{footer}</div>}
      </div>
    </div>
  );
}

export function Toast({
  message,
  tone = "success",
  actionLabel,
  onAction,
  onDismiss,
  dismissLabel = "Dismiss",
}: {
  message: string;
  tone?: "success" | "error" | "info";
  actionLabel?: string;
  onAction?: () => void;
  onDismiss?: () => void;
  dismissLabel?: string;
}) {
  const tones = {
    success: "bg-slate-900 text-white",
    error: "bg-red-700 text-white",
    info: "bg-brand-800 text-white",
  } as const;
  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-20 z-40 flex justify-center px-4 lg:bottom-6">
      <div
        role="status"
        className={`pointer-events-auto flex w-full max-w-md items-center gap-3 rounded-2xl px-4 py-3 shadow-2xl ${tones[tone]}`}
      >
        {tone === "success" && (
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/15">
            <CheckIcon className="h-4 w-4" />
          </span>
        )}
        <p className="min-w-0 flex-1 text-sm font-semibold">{message}</p>
        {actionLabel && onAction && (
          <button
            type="button"
            onClick={onAction}
            className="shrink-0 rounded-full bg-white/15 px-3 py-1 text-xs font-bold text-white active:bg-white/25"
          >
            {actionLabel}
          </button>
        )}
        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            aria-label={dismissLabel}
            className="shrink-0 text-lg leading-none text-white/60 hover:text-white"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}
