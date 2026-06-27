// Display formatters. Backend sends minutes / raw numbers; the UI rounds here.

/** 480 → "8h", 90 → "1h 30m", 45 → "45m". */
export function formatHM(minutes: number): string {
  const total = Math.round(minutes);
  const h = Math.floor(total / 60);
  const m = total % 60;
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

/** 450 → "7.5h" (decimal hours). */
export function formatHours(minutes: number, digits = 1): string {
  return `${(minutes / 60).toFixed(digits)}h`;
}

/** Completion percent; null → em dash (no data). */
export function formatPct(pct: number | null): string {
  return pct === null ? "—" : `${Math.round(pct)}%`;
}

/** Signed duration, e.g. "+1h 30m" / "−45m" (real minus sign). */
export function formatSignedHM(minutes: number): string {
  if (minutes === 0) return "0m";
  const sign = minutes > 0 ? "+" : "−";
  return `${sign}${formatHM(Math.abs(minutes))}`;
}

/** "2026-06-24" → "Wed, Jun 24" (parsed as a local date, no TZ shift). */
export function formatDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

/** ISO datetime → local "09:00" (times are stored as local-naive ISO). */
export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** "2026-06" → "June 2026". */
export function formatMonth(month: string): string {
  const [y, m] = month.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(undefined, {
    month: "long",
    year: "numeric",
  });
}
