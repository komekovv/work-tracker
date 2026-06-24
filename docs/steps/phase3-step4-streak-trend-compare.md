# Phase 3 · Step 4 — Streak, trend, comparison (`kpi.py`)

**Status:** Done
**Goal:** The remaining KPI analytics — current streak (D3), a per-period trend
series, and period-over-period comparison (D2).

## What was implemented (added to `backend/modules/worktime/kpi.py`)

- **`streak(as_of=None) -> int`** — consecutive target-met days ending at
  `as_of` (default today), walking backwards.
- **`trend(period='week', n=6, as_of=None) -> list[PeriodStats]`** — the last
  `n` consecutive weeks/months up to `as_of`, **oldest first**.
- **`Comparison`** dataclass + **`compare(period='month', as_of=None)`** —
  current vs previous period.
- **`_period_bounds(period, anchor)`** helper (week honours `week_start_day`).

## Key decisions

- **Streak skip rule (D3).** Walking back, a day with **no requirement** is
  skipped (neither counts nor breaks): this is any bonus day
  (Sunday/holiday/leave/vacation, `target_met is None`) **and** any day whose
  resolved target is 0. A met day (>0 target) increments; the first real miss
  breaks. Skipping target-0 days also stops pre-target history from inflating
  the streak.
- **Bounded scan.** The backward walk stops at the earliest recorded session, so
  it always terminates; no sessions → streak 0.
- **Trend returns full `PeriodStats`** per period (not just a number), so a chart
  can show worked/target/completion/bonus; ordered oldest→newest for plotting.
- **Comparison is no-prior-safe (D2).** `pct_change` is `None` and `has_prior`
  is `False` when the previous period had no work, instead of dividing by zero.
  `completion_diff_pct` is `None` if either side lacks a completion %.
- **Single connection** reused across the many `period_stats`/`compute_day`
  calls inside trend/compare.

## Verification (throwaway temp DB, no repo test files)

- **Streak:** Fri (Fri met, Thu *leave* skipped, Wed met, Tue miss) → **2**; the
  miss day itself → **0**; a longer run spanning a skipped Sunday *and* a leave
  → **4**; empty DB → **0**.
- **Trend:** 3 weekly periods returned oldest-first; latest week worked 2220.
- **Compare (month):** empty May → June gave `pct_change=None`,
  `has_prior=False`; after adding May data, diff 1740 min, **+181.2%**,
  `has_prior=True`.

No new dependencies. Nothing to install for this step.

## Next

Step 5 — Phase 3 end-to-end verification: a realistic multi-week scenario
(target change, holiday/leave/Sunday) asserting calc + all KPI outputs together.
