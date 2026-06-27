// TypeScript mirrors of the backend Pydantic schemas (backend/.../schemas.py).
// All durations are minutes; all dates/times are ISO strings.

export type DayTypeName = "workday" | "holiday" | "leave" | "vacation";
export type SessionSource = "auto" | "manual" | "crash-recovered";
export type PeriodKind = "week" | "month";
export type TargetPeriod = "daily" | "weekly";

// --- core ---

export interface DayTypeIn {
  date: string; // YYYY-MM-DD
  type: DayTypeName;
  name?: string | null;
  planned?: boolean;
  affects_target?: boolean | null;
}

export interface DayTypeOut {
  date: string;
  type: DayTypeName;
  name: string | null;
  planned: boolean;
  affects_target: boolean;
}

export type Settings = Record<string, string>;

// --- worktime: sessions & targets ---

export interface SessionOut {
  id: number;
  date: string;
  start_time: string;
  end_time: string | null;
  duration_minutes: number | null;
  is_sunday: boolean;
  last_heartbeat: string | null;
  source: SessionSource;
}

export interface ManualSessionIn {
  start_time: string; // ISO datetime
  end_time?: string | null; // omit/null for an open session (clock-in)
}

export interface SessionEditIn {
  start_time?: string | null;
  end_time?: string | null;
}

export interface TargetIn {
  effective_from: string; // YYYY-MM-DD
  daily_hours: number;
  period?: TargetPeriod;
  weekday?: number | null; // 0=Mon … 6=Sun
}

export interface TargetOut {
  id: number;
  effective_from: string;
  period: TargetPeriod;
  weekday: number | null;
  daily_hours: number;
}

// --- worktime: analytics ---

export interface DayResult {
  date: string;
  day_type: DayTypeName;
  is_sunday: boolean;
  worked_minutes: number;
  target_minutes: number;
  over_under_minutes: number;
  is_bonus: boolean;
  bonus_minutes: number;
  target_met: boolean | null; // null = excluded/skipped (bonus day)
}

export interface PeriodStats {
  start: string;
  end: string;
  days: number;
  worked_minutes: number;
  worked_toward_target_minutes: number;
  target_minutes: number;
  bonus_minutes: number;
  over_under_minutes: number;
  completion_pct: number | null;
  days_worked: number;
  days_counted: number;
  days_met: number;
  average_worked_minutes: number | null;
}

export interface Debt {
  start: string;
  end: string;
  as_of: string;
  debt_end: string;
  remaining_start: string;
  target_minutes: number;
  worked_minutes: number;
  over_under_minutes: number; // negative = debt, positive = surplus
  days_counted: number;
  days_met: number;
  no_show_minutes: number;
  no_show_days: number;
  under_minutes: number;
  under_days: number;
  surplus_minutes: number;
  surplus_days: number;
  remaining_work_days: number;
  remaining_target_minutes: number;
  outstanding_minutes: number;
  catch_up_per_day_minutes: number | null;
  avg_needed_per_day_minutes: number | null;
}

export interface Comparison {
  period: string;
  current: PeriodStats;
  previous: PeriodStats;
  worked_diff_minutes: number;
  completion_diff_pct: number | null;
  pct_change: number | null;
  has_prior: boolean;
}

export interface ActiveSession {
  id: number;
  start_time: string;
  last_heartbeat: string | null;
  elapsed_minutes: number;
}

export interface Today {
  date: string;
  day_type: DayTypeName;
  is_sunday: boolean;
  target_minutes: number;
  worked_minutes: number;
  worked_minutes_live: number;
  over_under_minutes: number;
  is_bonus: boolean;
  bonus_minutes: number;
  target_met: boolean | null;
  active_session: ActiveSession | null;
}

export interface Stats {
  period: PeriodKind;
  as_of: string;
  stats: PeriodStats;
  trend: PeriodStats[];
}

export interface Kpi {
  as_of: string;
  streak: number;
  month: PeriodStats;
  comparison: Comparison;
}

export interface Calendar {
  month: string; // YYYY-MM
  days: DayResult[];
}
