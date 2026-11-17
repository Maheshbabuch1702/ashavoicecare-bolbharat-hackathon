import type { Language } from "./types";

const MONTHS: Record<string, string[]> = {
  "en-IN": ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
  "ta-IN": ["", "ஜனவரி", "பிப்ரவரி", "மார்ச்", "ஏப்ரல்", "மே", "ஜூன்", "ஜூலை", "ஆகஸ்ட்", "செப்டம்பர்", "அக்டோபர்", "நவம்பர்", "டிசம்பர்"],
  "hi-IN": ["", "जनवरी", "फरवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"],
};

const WEEKDAYS: Record<string, string[]> = {
  "en-IN": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
  "ta-IN": ["ஞாயிறு", "திங்கள்", "செவ்வாய்", "புதன்", "வியாழன்", "வெள்ளி", "சனி"],
  "hi-IN": ["रविवार", "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार"],
};

export function formatDate(iso: string | null | undefined, language: Language): string {
  if (!iso) return "";
  const parts = iso.split("-").map(Number);
  if (parts.length !== 3 || parts.some(Number.isNaN)) return iso;
  const [year, month, day] = parts;
  const names = MONTHS[language] ?? MONTHS["en-IN"];
  if (language === "hi-IN") return `${day} ${names[month]} ${year}`;
  return `${names[month]} ${day}, ${year}`;
}

export function formatLongDate(iso: string, language: Language): string {
  const parsed = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return iso;
  const weekday = (WEEKDAYS[language] ?? WEEKDAYS["en-IN"])[parsed.getDay()];
  return `${weekday}, ${formatDate(iso, language)}`;
}

export function todayIso(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

export function formatWeight(value: number | null | undefined, language: Language = "en-IN"): string {
  if (value === null || value === undefined) return "";
  const unit = { "en-IN": "kg", "ta-IN": "கிலோ", "hi-IN": "किलो" }[language];
  return `${Number(value.toFixed(2))} ${unit}`;
}

function dayDiff(iso: string): number | null {
  const target = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(target.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - today.getTime()) / 86_400_000);
}

export function relativeDays(iso: string | null | undefined, language: Language = "en-IN"): string {
  if (!iso) return "";
  const days = dayDiff(iso);
  if (days === null) return "";
  if (days === 0) return { "en-IN": "Today", "ta-IN": "இன்று", "hi-IN": "आज" }[language];
  if (days === 1) return { "en-IN": "Tomorrow", "ta-IN": "நாளை", "hi-IN": "कल" }[language];
  if (days === -1) return { "en-IN": "Yesterday", "ta-IN": "நேற்று", "hi-IN": "कल (बीता)" }[language];
  if (days < 0) {
    return language === "ta-IN"
      ? `${Math.abs(days)} நாட்கள் தாமதம்`
      : language === "hi-IN"
        ? `${Math.abs(days)} दिन देर`
        : `${Math.abs(days)} days overdue`;
  }
  return language === "ta-IN"
    ? `${days} நாட்களில்`
    : language === "hi-IN"
      ? `${days} दिनों में`
      : `in ${days} days`;
}

export function timeAgo(iso: string, language: Language = "en-IN"): string {
  const then = new Date(iso);
  if (Number.isNaN(then.getTime())) return "";
  const minutes = Math.round((Date.now() - then.getTime()) / 60_000);
  if (minutes < 1) {
    return { "en-IN": "just now", "ta-IN": "இப்போது", "hi-IN": "अभी" }[language];
  }
  if (minutes < 60) {
    return language === "ta-IN" ? `${minutes} நிமிடம் முன்` : language === "hi-IN" ? `${minutes} मिनट पहले` : `${minutes}m ago`;
  }
  const hours = Math.round(minutes / 60);
  if (hours < 24) {
    return language === "ta-IN" ? `${hours} மணி முன்` : language === "hi-IN" ? `${hours} घंटे पहले` : `${hours}h ago`;
  }
  const days = Math.round(hours / 24);
  return language === "ta-IN" ? `${days} நாள் முன்` : language === "hi-IN" ? `${days} दिन पहले` : `${days}d ago`;
}
