# Phase 7 · Step 3 — README + final verification

**Status:** Done
**Goal:** Complete setup/run documentation and a final end-to-end smoke of the
production single-process app.

## What was implemented

- **`README.md`** (repo root): overview, architecture, prerequisites
  (Python 3.12, Node 20+, NSSM), project layout, setup (backend venv + deps,
  frontend install + build), running in three modes:
  - **Production single process** — `uvicorn ... --port 8765`, app at
    `http://127.0.0.1:8765`.
  - **Production services** — `deploy/install-services.ps1 -Port 8765` (elevated),
    table of the two services, rebuild/restart notes, uninstall.
  - **Development** — backend `:8000` (`--reload`) + `npm run dev` `:3000`.
  - Plus verify, logs, configuration (env vars + dynamic settings), and a short
    "how it works".

## Final end-to-end verification (production origin :8765)

A single FastAPI process serving both UI and API was driven through the whole
app via **client-side navigation**:
- `/` → dashboard: KPI cards with real data (Step 1).
- Clicked **Worktime** → routed to `/worktime`; calendar rendered "June 2026"
  with real data (Friday short-days "of 4h", holiday "3h", etc.), fetched
  same-origin.
- Clicked **Settings** → routed to `/settings`; theme control (Light/Dark/System)
  + `week_start_day` editor rendered.

All from `http://127.0.0.1:8765` — no separate Next process, no CORS, one origin.

## Phase 7 — Done

- FastAPI serves the static frontend (Step 1).
- NSSM scripts register the detector + API as auto-starting services (Step 2).
- README documents the full setup; the production single-process app is verified
  end-to-end (Step 3).

## Project complete

All 7 phases are built and verified:
1. Core (DB/migrations/registry/settings/day-types/calendar)
2. Worktime detector + data (sessions/targets, orphan recovery)
3. Calc + KPI (targets A1–A4, bonus C1–C5, streak/trend/comparison, month-to-date)
4. API (registry-wired routers, full endpoints)
5. Frontend core + dashboard (theme, KPI cards, heatmap, trend)
6. Frontend calendar + settings (calendar, session add/edit, targets/holidays,
   general settings, responsive)
7. NSSM + integration (FastAPI serves static, services, README)

Remaining real-world step the user performs: install Python deps, build the
frontend, and run `deploy/install-services.ps1` as Administrator (needs the NSSM
binary) to have everything start at boot.
