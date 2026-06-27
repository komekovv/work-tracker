# Worktime page — Week / Month / Custom summary tabs (post-release)

The Worktime page showed a monthly calendar with a **single-day** detail panel on
the right (`DayPanel`). The only place to see aggregates was the dashboard. This adds
a **Day / Week / Month / Custom** toggle to that right-side panel: *Day* keeps the
per-day view; *Week / Month / Custom* swap it to a summary of the range.

Purely additive — no `kpi.py`/`calc.py`, `core/`, or `api/main.py` changes, and **no
new schema** (it reuses `PeriodStatsOut`).

---

## What each tab shows

A summary panel with the range's aggregates, all from the existing live calc layer
(`kpi.PeriodStats`): worked, target, over/under, completion %, bonus, days met /
counted, days worked, average/day. Bonus days (Sunday/holiday/leave/vacation) are
excluded from target/completion but counted as bonus (C1–C5), inherited from
`period_stats`.

- **Day** — the existing `DayPanel`, driven by the calendar selection (unchanged).
- **Week** — the week containing the selected day (or today if none selected).
- **Month** — the calendar's currently-viewed month (follows the ‹/› nav).
- **Custom** — two date inputs; fetches once both are set.

## Why a new endpoint instead of reusing `/stats`

`/stats` uses `as_of` as **both** the period anchor and the to-date cap, so asking it
for a *past* month would truncate the month at `as_of`. The new endpoint separates
the two: the range is chosen by `period`+`anchor` (or explicit `from`/`to`), while
`as_of` (default today) only caps the *current* period to-date. A past month/week
therefore returns its full range; the current one is month-/week-to-date (consistent
with the dashboard). Week bounds also depend on the dynamic `week_start_day` setting,
which the backend resolves — so the range is computed server-side, not in the client.

## Pieces and how they fit

**Backend**

- `modules/worktime/routes.py` — new `GET /api/worktime/summary` returning the
  existing `PeriodStatsOut`. Resolves the range and delegates to the existing
  `kpi.week_stats` / `month_stats` / `period_stats`:
  - `from`/`to` given → `period_stats(from, to, as_of=today)` (422 if only one, or
    `from > to`);
  - `period=week` → `week_stats(anchor or today, as_of=today)`;
  - else → `month_stats(anchor or today, as_of=today)`.

**Frontend**

- `lib/api.ts` — `getSummary({ period?, anchor?, from?, to?, asOf? })` → `PeriodStats`
  (the `PeriodStats` type already existed).
- `components/modules/worktime/period-summary-panel.tsx` — fetches and renders the
  summary (range header from the response `start`/`end`, with a "to date" hint when
  the range ends today; stats grid styled like `DayPanel`). Custom mode waits until
  both dates are set (same pattern as `debt-card.tsx`). Handles empty ranges (D1) and
  loading/error states.
- `components/modules/worktime/side-panel-tabs.tsx` — the Day/Week/Month/Custom
  segmented control (visual pattern from the debt card's mode toggle).
- `app/worktime/page.tsx` — `tab` state + custom-range inputs; renders the tabs and
  the matching panel. A `reloadToken` (bumped in the existing `refresh()`) makes the
  summary re-fetch after a session add/edit. Calendar, month nav, "Today", and the
  session modal are unchanged.

## Verification

- **API** (FastAPI app against a temp `WORKTIME_DB_PATH`, base 8h target, April
  sessions): `?period=month&anchor=2026-04-15` returned the **full** April
  (2026-04-01 → 04-30, not truncated at the 15th) — the key reason for the endpoint;
  `?period=week&anchor=…` and `?from=&to=` worked; `from > to` and a lone `from`
  correctly 422'd.
- **Frontend:** `npm run build` (type-checks the static export) passes.

## Applying (production)

Frontend → `cd frontend && npm run build` (API serves `out/` from disk; no restart
for static assets). Backend → `nssm restart WorkTrackerAPI`.
