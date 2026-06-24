# Phase 3 · Step 2 — Per-day calculation (`calc.py`)

**Status:** Done
**Goal:** Turn a date into a complete `DayResult` — worked vs target, over/under,
and the bonus classification (cases C1–C5) — all in minutes (D5).

## What was implemented (added to `backend/modules/worktime/calc.py`)

- **`DayResult`** frozen dataclass: `date, day_type, is_sunday, worked_minutes,
  target_minutes, over_under_minutes, is_bonus, bonus_minutes, target_met`.
- **`compute_day(date)`** → `DayResult`, computed live from sessions + day_types
  + targets on one shared connection.
- **`_worked_minutes`** helper — `SUM(duration_minutes)` for the day; open
  sessions (NULL duration) count 0.

## Key decisions / rules

- **Bonus day = Sunday OR (holiday/leave/vacation with `affects_target`).** On a
  bonus day: `target=0`, all worked minutes become `bonus_minutes`,
  `is_bonus = worked>0`, `over_under=0`, and **`target_met=None`** — excluded
  from completion and *skipped* by the streak (D3), neither pass nor fail.
  - C1 holiday worked, C2 leave/vacation worked, C3 manual-leave worked → all
    fall out of this single rule (all bonus).
  - **C5** Sunday *and* holiday → still one bonus day; `bonus_minutes == worked`
    (counted once, verified).
- **C4 is already settled upstream** — `day_types` enforces manual-wins, so
  `compute_day` just reads the effective marking.
- **Normal day:** `target_minutes = round(resolve_target*60)`,
  `over_under = worked - target`, `target_met = worked >= target`.
- **`affects_target` gate:** a special day-type only zeroes the target when its
  `affects_target` flag is set (default true for holiday/leave/vacation), so an
  explicit override is respected.
- **Minutes everywhere (D5):** fractional targets like 4.5h → 270 minutes;
  durations already stored as integer minutes.
- **Live, day-level** (per [[calc-live-compute]] decision): no session calc
  columns are written.

## Verification (throwaway temp DB, no repo test files)

- Normal: 8h/8h → met, +0; 5h/8h → missed, −180; not worked → missed, −480.
- **C1** holiday worked → bonus 200, target 0, met None.
- **C2/C3** leave worked → bonus 90, met None.
- Vacation not worked → excluded (not bonus, met None).
- Sunday worked → bonus 120, met None; Sunday idle → excluded.
- **C5** Sunday+holiday → `worked == bonus == 120` (no double count).
- **D5** Wednesday 4.5h override → 270 minutes.

No new dependencies. Nothing to install for this step.

## Next

Step 3 — `kpi.py` period aggregation: totals, completion % (bonus excluded, D4),
average daily, with empty ranges degrading safely (D1).
