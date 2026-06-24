# Phase 4 · Step 3 — Worktime read routes

**Status:** Done
**Goal:** Expose the analytics over HTTP — today/stats/kpi/sessions/calendar —
returning minutes-only JSON.

## What was implemented

### `models.get_sessions_between(start, end)`
Ranged session list (inclusive, ordered), backing the `/sessions` endpoint.

### `backend/modules/worktime/schemas.py`
Pydantic response models, most built from the calc/kpi/models dataclasses via
`from_attributes`: `SessionOut`, `DayResultOut`, `PeriodStatsOut`,
`ComparisonOut`, `ActiveSessionOut`, `TodayOut`, `StatsOut`, `KpiOut`,
`CalendarOut`. All durations are **minutes**.

### `backend/modules/worktime/routes.py` (`prefix="/api/worktime"`)
- `GET /today` — `compute_day(today)` plus the in-progress session. Adds the
  open session's **live elapsed** to `worked_minutes_live`, but only if it began
  today (B2); `over_under` is based on the live figure.
- `GET /stats?period=week|month&as_of=&n=` — current `PeriodStats` + an `n`-long
  trend of the same period type.
- `GET /kpi?as_of=` — streak, current month `PeriodStats`, month-over-month
  comparison.
- `GET /sessions?from=&to=` — sessions in range (defaults to current month);
  `from` via `Query(alias="from")` since it's a Python keyword.
- `GET /calendar?month=YYYY-MM` — per-day `DayResultOut` for the month (one
  shared connection across the loop); bad `month` → 422.

### `worktime/registration.py`
Added `_worktime_router_factory` (lazy import) as the registration's
`router_factory`.

## Key decisions

- **`from_attributes` conversion** keeps the API shapes in lock-step with the
  domain dataclasses — no hand-written field copying except `TodayOut` (which
  blends a `DayResult` with live session data).
- **Live `/today`** reflects the in-progress session (unlike `compute_day`,
  which only sums closed sessions), so "worked so far" is accurate.
- **One connection per looping handler** (`/calendar`, `/stats` trend) for
  efficiency; `period_stats`/`trend`/`compare` already reuse their connection.
- **Sensible defaults** — `/sessions` and `/calendar` default to the current
  month; `/stats` `n` is bounded `[1, 52]`.
- **Minutes only** in every response (per the API-units decision); the frontend
  formats hours.

## Verification (venv python, TestClient)

Against a seeded week (base 8h, a holiday, Sunday work):
- Routes mounted with no `main.py` change.
- `/stats` week: worked 1580, target 2400, **completion 52.5%**, trend len 3.
- `/kpi`: streak 0 (today unworked), month worked 1580, bonus 320, no prior.
- `/sessions`: 5 rows, all `auto`.
- `/calendar`: 30 days; 06-25 → holiday, bonus 200, `target_met=None`.
- `/today`: idle → `worked_live=0`, `active=None`; after opening a session →
  `active_session` with elapsed ≥ 0.
- `month=June` → 422.

No new dependencies.

## Next

Step 4 — Worktime write routes: `POST /sessions/manual`, `PATCH /sessions/{id}`,
`POST /target`, with overlap rejection (B6) and 404s.
