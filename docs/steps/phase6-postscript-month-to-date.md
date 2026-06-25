# Phase 6 · Postscript — Month-to-date completion

**Status:** Done (resolves the open question raised in Step 4)
**Decision:** The current period's completion % is **month-/week-to-date** —
only days up through today count. Past periods stay whole-period.

## What changed (`backend/modules/worktime/kpi.py`, `routes.py`)

- **`period_stats(..., as_of=None)`** — when `as_of` falls before `end`, the
  range is capped at it. Because the cap only shrinks (never extends), passing
  "today" affects only the current period; any period that already ended before
  today is untouched.
- **`month_stats` / `week_stats`** gained an `as_of` passthrough.
- **`trend`** caps each period at the anchor, so only the latest (current)
  period becomes to-date; older bars are unaffected.
- **`compare`** caps the *current* period at the anchor but leaves the *previous*
  (complete) period uncapped.
- **Routes** `/kpi` and `/stats` pass `as_of = anchor` for the current period.

## Why this shape

- Worked/bonus totals are unchanged (future days have no sessions); only the
  completion **denominator** (target/counted days) shrinks to elapsed days, so
  "Target %" reflects pace-so-far instead of being dragged down by future days.
- A single, safe rule (cap-if-before-end) means the same `as_of=today` is
  correct everywhere — current period adjusts, history doesn't.

## Verification

- Unit check (temp DB): full June = 38.5% over 26 counted days; to-the-15th =
  **76.9%** over 13 counted days; worked totals equal; a past month (May) with
  `as_of` in June is unaffected.
- Live: `/kpi` returned `month.end=2026-06-25` (capped), **completion 41.9%**
  (was 32% whole-month), days_counted 25→20. Dashboard "Target" card shows
  **42% · 8/20 days met**.

## Phase 6 fully closed — ready for Phase 7 (NSSM + serve static build).
