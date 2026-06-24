# Phase 5 · Step 4 — Dashboard KPI cards

**Status:** Done
**Goal:** The main dashboard fetches live data and renders the KPI cards (today,
month total, target %, streak, bonus) with loading/empty/error states.

## What was implemented

- **`src/lib/format.ts`** — `formatHM`, `formatHours`, `formatPct` (null → "—"),
  `formatSignedHM`, `formatDate` (local, no TZ shift).
- **`src/lib/use-api.ts`** — `useApi(fetcher, deps)` hook (native fetch; loading/
  error/data + `reload`; cancels stale results). No SWR.
- **`src/components/ui/error-state.tsx`** — error card with Retry.
- **`src/components/modules/worktime/stat-card.tsx`** — labelled stat with
  optional accent dot.
- **`src/components/modules/worktime/kpi-cards.tsx`** — 4 cards from `Kpi`:
  Month total (+ vs-last-month delta), Target % (days met), Streak, Bonus.
- **`src/components/modules/worktime/today-card.tsx`** — today's worked-vs-target
  with a progress bar, signed over/under, bonus-day handling, and a live
  "Working" pulse when a session is open.
- **`src/app/page.tsx`** — now a client component: fetches `getKpi` + `getToday`,
  shows a skeleton while loading, an `ErrorState` on failure, else the cards.

## Key decisions

- **Empty data is the zero state (D1)** — the backend returns zeros/`null` for an
  empty month, so cards naturally show `0h` / `—`; no special-casing or crash.
- **Minutes formatted at the edge** — components receive minutes and call the
  formatters; matches the minutes-only API contract.
- **Error state is actionable** — names the failure and asks "is the backend
  running?", with Retry (covers the API-down case).
- **Today card is live** — uses `worked_minutes_live` (includes the open
  session) and shows a pulse when `active_session` is set.

## Verification

- `npm run build` → compiles, TS passes, static export OK.
- **Live, real data:** seeded a backend DB (June 2026) on `:8000`; dashboard on
  `:3000` fetched and rendered (confirmed via `read_page`):
  - Today 8h / 8h, 100%, +0m.
  - Month total 69.0h ("no prior month"), Target 32% (8/25 met), Streak 8,
    Bonus 5.0h — all matching the API exactly.

## Open question (flagged to user)

Month "Target %" counts the **whole calendar month**, so future/unworked days
drag it down mid-month. Consider month-to-date completion (up to today) in a
later step. Recorded, not yet changed.

## Next

Step 5 — Daily heatmap + weekly trend chart (Recharts) with a target reference
line; integrate into the dashboard.
