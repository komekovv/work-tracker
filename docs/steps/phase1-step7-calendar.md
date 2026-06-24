# Phase 1 · Step 7 — `core/calendar.py` (date/calendar helpers)

**Status:** Done
**Goal:** One canonical set of date helpers (weekday, week/month boundaries,
day ranges) for the KPI, stats, and calendar layers to build on.

## What was implemented (`backend/core/calendar.py`)

- **`to_date(value)`** — coerce ISO string or `date` → `date`.
- **`weekday(value)`** — Monday = 0 … Sunday = 6.
- **`is_sunday(value)`** — for the Sunday-bonus rule (plan §5).
- **`resolve_week_start(week_start=None, conn=, db_path=)`** — resolve the
  week-start index. Precedence: explicit arg (int 0–6 or day name) → the
  `week_start_day` setting (if a DB is available) → Monday (0).
- **`week_bounds(value, week_start=, conn=, db_path=)`** → `(start, end)` of the
  7-day week containing the date.
- **`month_bounds(value)`** → `(first, last)` of the month.
- **`iter_days(start, end)`** — generator over the inclusive range.
- **`days_in_range(start, end)`** — materialised inclusive list.
- Constant **`SUNDAY = 6`**.

## Key decisions

- **Weekday convention fixed app-wide: Monday = 0 … Sunday = 6**, matching
  Python's `date.weekday()` and the plan's `targets.weekday` column. Documented
  in the module so Phase 2/3 per-weekday targets align with no off-by-one risk.
- **Week start is dynamic but optional.** `week_bounds` honours the
  `week_start_day` setting when a DB is supplied, yet the module works as pure
  date math (defaults to Monday) when called without one — keeps it cheap to use
  and unit-reasoned without a database.
- **Offset math** `(d.weekday() - ws) % 7` handles any week-start cleanly
  (Monday- and Sunday-start both verified).
- **`bool` guard in `resolve_week_start`** — since `bool` subclasses `int`,
  passing `True/False` raises `TypeError` rather than being read as 1/0.
- **Inclusive ranges, empty when reversed** — `iter_days` yields nothing if
  `end < start` (no exception), which keeps downstream loops simple.
- **No DB writes here** — only an optional settings *read*; calendar is pure
  computation over dates.

## Verification (throwaway temp DB, no repo test files)

- `2026-06-24` (a Wednesday) → `weekday=2`; Sunday detection correct.
- Week (Monday default) = `06-22 … 06-28`; with `week_start_day=sunday`
  setting = `06-21 … 06-27`; explicit `week_start="monday"` overrides setting.
- Month bounds correct for June, December (year rollover), and Feb 2028
  (leap year → 29).
- Inclusive range = 30 days; reversed range = `[]`; single-day range works.
- `date` objects accepted; bad week-start inputs (`"party"`, `9`, `True`)
  rejected with `ValueError`/`ValueError`/`TypeError`.

No dependencies needed — stdlib only. Nothing to install for this step.

## Next

Step 8 — Phase 1 verification: a smoke run of the whole core chain (init →
migrate → settings → day types → calendar), confirming "empty but working core,
ready to accept modules."
