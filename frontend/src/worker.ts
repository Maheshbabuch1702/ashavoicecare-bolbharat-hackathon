export interface WorkerProfile {
  name: string;
  village: string;
}

const PROFILE_KEY = "asha.voicecare.worker";

// Synthetic demo profile. No real worker or beneficiary data is stored.
export const DEFAULT_WORKER: WorkerProfile = {
  name: "Sunita Devi",
  village: "Rampur",
};

export function loadWorker(): WorkerProfile {
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    if (!raw) return DEFAULT_WORKER;
    const parsed = JSON.parse(raw) as Partial<WorkerProfile>;
    return {
      name: (parsed.name || DEFAULT_WORKER.name).trim(),
      village: (parsed.village || DEFAULT_WORKER.village).trim(),
    };
  } catch {
    return DEFAULT_WORKER;
  }
}

export function saveWorker(profile: WorkerProfile): void {
  try {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
  } catch {
    // storage can be blocked in private preview frames
  }
}

export function greetingKey(now = new Date()): "greetingMorning" | "greetingAfternoon" | "greetingEvening" {
  const hour = now.getHours();
  if (hour < 12) return "greetingMorning";
  if (hour < 17) return "greetingAfternoon";
  return "greetingEvening";
}
