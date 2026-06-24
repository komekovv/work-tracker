# Phase 4 · Step 5 — End-to-end verification

**Status:** Done
**Goal:** Prove the whole API works together — configure, record, read, and
error-handle — purely over HTTP.

## What was verified (HTTP only, no direct model calls)

Driven through a `TestClient` against a temp DB:

1. **Configure** — `POST /api/settings`, two `POST /api/worktime/target` (base
   8h + Friday 4h), two `POST /api/day-type` (holiday, manual leave).
2. **Record** — seven `POST /api/worktime/sessions/manual` (a full week),
   all 201.
3. **Read & assert**
   - `/stats?period=week` → worked 2160, target 1920, **completion 90.6%**,
     bonus 420, met 3/4 (matches hand calc).
   - `/kpi` → streak 1, month worked 2160, bonus 420.
   - `/sessions` → 7 rows, all `manual`.
   - `/calendar` → 06-25 holiday bonus 180, 06-26 leave bonus 120.
   - `/today` (real date 2026-06-24) → worked 480, target 480, met `True`,
     no active session.
4. **Errors** — overlap → 409, PATCH unknown → 404, negative target → 422,
   day-type delete → 204 then 404.
5. **Surface** — all 12 expected routes present (`/health`, core settings +
   day-type, worktime read + write).

## Outcome — Phase 4 done

The API exposes the full backend: registry-mounted core + worktime routers,
settings/day-type/target management, manual session entry with overlap
rejection (B6), and the read endpoints (today/stats/kpi/sessions/calendar) — all
minutes-only, all delegating to the verified logic layers. The detector and data
layers remain FastAPI-free thanks to lazy router factories.

## Next (Phase 5 preview)

Front-end: Next.js 16 (`src/`, static export), `lib/api.ts` calling these
endpoints, theme system, and the KPI dashboard (cards + heatmap + trend).
