# Phase 3 · Step 3 — Period aggregation (`kpi.py`)

**Status:** Done
**Goal:** Aggregate per-day results over a range into period totals, completion
%, and averages — with bonus kept separate and empty ranges safe.

## What was implemented (`backend/modules/worktime/kpi.py`)

- **`PeriodStats`** frozen dataclass: `start, end, days, worked_minutes,
  worked_toward_target_minutes, target_minutes, bonus_minutes,
  over_under_minutes, completion_pct, days_worked, days_counted, days_met,
  average_worked_minutes`.
- **`period_stats(start, end)`** — folds `calc.compute_day` over the inclusive
  range on a single shared connection.
- **`month_stats(in_month)`** / **`week_stats(in_week)`** — convenience wrappers
  over `calendar.month_bounds` / `week_bounds` (week honours `week_start_day`).

## Key decisions

- **Bonus kept separate (D4).** The core identity is
  `worked_minutes = worked_toward_target_minutes + bonus_minutes`. Completion is
  computed only from `worked_toward_target` and `target`, so bonus never inflates
  it. Verified: worked 2060 = toward 1740 + bonus 320.
- **Hours-based completion %** = `worked_toward_target / target * 100` (1 dp),
  `None` when no target applies in the range. Allows >100% when overworked.
- **`days_counted` only includes days that actually require work** — non-bonus
  days with `target > 0`. A 0-target day isn't counted or "met", avoiding
  trivially-met inflation. `days_met` is the subset of counted days that hit
  target.
- **Empty/target-less ranges are safe (D1):** zeros throughout,
  `completion_pct=None`, `average_worked_minutes=None`, no exception.
- **Average over worked days** (`worked_minutes / days_worked`), `None` if no
  days worked.
- **Live** — every day recomputed via `compute_day`; nothing cached.

## Verification (throwaway temp DB, no repo test files)

A known week (base 8h; Mon 8h, Tue 5h, Wed idle, Thu holiday+200, Fri 8h,
Sat 8h, Sun bonus 120) matched hand calculations exactly:
- worked 2060, toward 1740, target 2400, bonus 320, over/under −660,
  completion 72.5%, days_worked 6, counted 5, met 3, avg 343.3.
- Decomposition `worked == toward + bonus` held.
- Empty range → zeros, completion `None`, no error.
- `month_stats(June)=30 days`, `week_stats=7 days`.

No new dependencies. Nothing to install for this step.

## Next

Step 4 — `kpi.py` streak (D3, leave/vacation skipped), trend series, and
period-over-period comparison (D2, no-prior-period safe).
