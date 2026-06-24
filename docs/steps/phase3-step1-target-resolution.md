# Phase 3 · Step 1 — Target resolution (`calc.py`)

**Status:** Done
**Goal:** Given a date, return the daily target hours that apply — honouring
historical and per-weekday target rules (cases A1–A4).

## What was implemented (`backend/modules/worktime/calc.py`)

- **`resolve_target(target_date) -> float | None`** — the daily target hours in
  effect for a date, or `None` if none is defined on/before it.

Implemented as two ordered lookups:
1. Most recent **weekday-specific** rule (`weekday = <date's weekday>`,
   `effective_from <= date`).
2. If none, most recent **base** rule (`weekday IS NULL`).

Each query orders by `effective_from DESC, id DESC LIMIT 1`.

## Key decisions

- **Precedence = specificity first, then recency.** A weekday rule beats the
  base rule even when the base is newer (A4) — a "short day" persists until the
  weekday rule itself is changed. Within one specificity, the latest
  `effective_from` on/before the date wins (A1), ties broken by id.
- **Live / read-only (A3).** Resolution reads the current `targets` table every
  call, so a retroactive edit simply changes what comes back — there is no
  stored value to keep in sync. Verified: correcting a past base from 9→7
  immediately changes the resolved value for earlier dates.
- **`None` for "no target".** The function doesn't invent a default; Step 2
  decides how to treat an unset target (it will use 0).
- **Period scoped to `'daily'`.** Weekly-period targets are a period-level
  concern handled in the KPI step, not here.
- **Direct SQL** (not `list_targets`) so resolution is a cheap indexed lookup.

## Verification (throwaway temp DB, no repo test files)

- No target → `None`; date before any `effective_from` → `None`.
- **A2:** Monday → base 9h; Friday → override 5h.
- **A1:** after base→8h (June), February still resolves 9h, July resolves 8h.
- **A4:** a July Friday stays 5h despite the newer 8h base.
- Recency within weekday: a new June Friday(6h) → July Fridays = 6h, February
  Fridays = 5h.
- **A3:** correcting the Jan base to 7h → February resolves 7h live.

No new dependencies. Nothing to install for this step.

## Next

Step 2 — Per-day calculation: `compute_day(date)` → worked vs target,
over/under, and the bonus classification (cases C1–C5), in minutes (D5).
