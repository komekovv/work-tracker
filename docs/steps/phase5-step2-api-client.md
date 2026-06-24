# Phase 5 · Step 2 — API client + types

**Status:** Done
**Goal:** A typed TS client mirroring the backend schemas, so pages call the API
with full type safety.

## What was implemented

### `src/lib/types.ts`
TS mirrors of the backend Pydantic schemas (minutes-only, ISO strings):
`DayTypeName`, `SessionSource`, `PeriodKind`, `TargetPeriod`; `DayTypeIn/Out`,
`Settings`; `SessionOut`, `ManualSessionIn`, `SessionEditIn`, `TargetIn/Out`;
`DayResult`, `PeriodStats`, `Comparison`, `ActiveSession`, `Today`, `Stats`,
`Kpi`, `Calendar`.

### `src/lib/api.ts`
- `API_BASE` = `NEXT_PUBLIC_API_BASE_URL` if set, else `http://localhost:8000`
  in dev / `""` (relative, same-origin) in production builds (NODE_ENV inlined at
  build time).
- `ApiError` (status + detail), a `request<T>` helper (JSON, 204 handling,
  pulls FastAPI's `detail` on errors), and `withQuery` for query strings.
- Typed functions: `getToday`, `getStats`, `getKpi`, `getSessions`,
  `getCalendar`, `createManualSession`, `editSession`, `setTarget`,
  `getSettings`, `updateSettings`, `setDayType`, `deleteDayType`.

### `backend/api/main.py` (small addition)
- The module-level `app` now honours `WORKTIME_DB_PATH` (same override the
  detector uses), so the API server can target a specific DB — handy for Phase 7
  and for verification without touching the real `app.db`.

## Key decisions

- **Base URL resolves itself** for dev vs prod via `NODE_ENV`, with an env
  override — no `.env` file needed to run `next dev` against the local backend.
- **Thin client, typed end-to-end** — one `request` helper; each endpoint is a
  one-liner returning a typed promise. Errors surface as `ApiError` with the
  backend's `detail`.
- **Types mirror the backend exactly** (minutes, nullable `target_met`/
  `completion_pct`, ISO strings) so the dashboard can't drift from the API.

## Verification

- `npm run build` → TypeScript passed (Next type-checks all included files).
- **Live server check:** ran `uvicorn backend.api.main:app` against a temp DB and
  curled the client's paths — `/health`, `/api/settings`,
  `/api/worktime/today` returned JSON matching the TS interfaces; **CORS
  preflight from `http://localhost:3000` → 200**.

No new dependencies.

## Next

Step 3 — Theme system (dark/light toggle, no-flash), `lib/modules.ts`, base UI
primitives (Card/Button), and the app-shell header.
