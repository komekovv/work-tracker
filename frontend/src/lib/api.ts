// Typed client for the backend API.
//
// Base URL: `NEXT_PUBLIC_API_BASE_URL` wins; otherwise dev builds hit the local
// FastAPI on :8000 and production builds use a relative path (FastAPI serves the
// static export same-origin in Phase 7). NODE_ENV is inlined at build time.

import type {
  Calendar,
  DayTypeIn,
  DayTypeOut,
  Debt,
  Kpi,
  ManualSessionIn,
  PeriodKind,
  SessionEditIn,
  SessionOut,
  Settings,
  Stats,
  TargetIn,
  TargetOut,
  Today,
} from "./types";

const DEV_DEFAULT = "http://localhost:8000";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  (process.env.NODE_ENV === "development" ? DEV_DEFAULT : "");

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type Query = Record<string, string | number | null | undefined>;

function withQuery(path: string, query?: Query): string {
  if (!query) return path;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null) params.set(key, String(value));
  }
  const qs = params.toString();
  return qs ? `${path}?${qs}` : path;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      // non-JSON error body; keep the status text
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// --- worktime: reads ---

export const getToday = () => request<Today>("/api/worktime/today");

export const getStats = (period: PeriodKind, asOf?: string, n?: number) =>
  request<Stats>(
    withQuery("/api/worktime/stats", { period, as_of: asOf, n }),
  );

export const getKpi = (asOf?: string) =>
  request<Kpi>(withQuery("/api/worktime/kpi", { as_of: asOf }));

export const getDebt = (params: {
  period?: PeriodKind;
  from?: string;
  to?: string;
  asOf?: string;
}) =>
  request<Debt>(
    withQuery("/api/worktime/debt", {
      period: params.period,
      from: params.from,
      to: params.to,
      as_of: params.asOf,
    }),
  );

export const getSessions = (from?: string, to?: string) =>
  request<SessionOut[]>(
    withQuery("/api/worktime/sessions", { from, to }),
  );

export const getCalendar = (month?: string) =>
  request<Calendar>(withQuery("/api/worktime/calendar", { month }));

// --- worktime: writes ---

export const createManualSession = (body: ManualSessionIn) =>
  request<SessionOut>("/api/worktime/sessions/manual", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const editSession = (id: number, body: SessionEditIn) =>
  request<SessionOut>(`/api/worktime/sessions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });

export const deleteSession = (id: number) =>
  request<void>(`/api/worktime/sessions/${id}`, { method: "DELETE" });

export const setTarget = (body: TargetIn) =>
  request<TargetOut>("/api/worktime/target", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const getTargets = () =>
  request<TargetOut[]>("/api/worktime/targets");

export const deleteTarget = (id: number) =>
  request<void>(`/api/worktime/target/${id}`, { method: "DELETE" });

// --- core: settings & day types ---

export const getSettings = () => request<Settings>("/api/settings");

export const updateSettings = (values: Settings) =>
  request<Settings>("/api/settings", {
    method: "POST",
    body: JSON.stringify(values),
  });

export const setDayType = (body: DayTypeIn) =>
  request<DayTypeOut>("/api/day-type", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const deleteDayType = (date: string) =>
  request<void>(`/api/day-type/${date}`, { method: "DELETE" });

export const getDayTypes = (from: string, to: string) =>
  request<DayTypeOut[]>(withQuery("/api/day-types", { from, to }));
