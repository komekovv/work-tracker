# Work-Time & KPI Tracker

A personal, local work dashboard. The computer's power state *is* the time
clock: power-on starts a work session, power-off ends it. From those sessions it
computes daily/weekly/monthly KPIs — target completion, streaks, trends, bonus
hours — against historical, per-weekday targets.

Single user, runs entirely on your machine. No cloud, no accounts.

- **Backend:** Python 3.12 · FastAPI · SQLite (WAL) — a modular monolith
  (`core` + feature `modules`, wired by a registry).
- **Frontend:** Next.js 16 · React 19 · TypeScript · Tailwind v4 — static export,
  served by the backend in production.
- **Services:** NSSM runs the detector and the API as auto-starting Windows
  services.

See [`docs/PROJECT_PLAN_EN.md`](docs/PROJECT_PLAN_EN.md) for the design and
[`docs/steps/`](docs/steps/) for a per-step build log.

---

## Prerequisites

- **Python 3.12** (3.13 also fine)
- **Node.js 20+** (for building the frontend)
- **[NSSM](https://nssm.cc)** — only for running as Windows services; put
  `nssm.exe` on your `PATH`.

## Project layout

```
backend/    FastAPI app, core, worktime module, detector   (data: backend/data/app.db)
frontend/   Next.js app (static export → frontend/out)
deploy/     NSSM install/uninstall scripts
docs/       plan + per-step build log
```

---

## Setup

### 1. Backend (Python venv + deps)

From the repo root:

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

### 2. Frontend (install + build)

```powershell
cd frontend
npm install
npm run build      # produces frontend/out (the static export)
cd ..
```

---

## Running

### Production — single process (manual)

The API serves both the UI and the API on **one port (8765)**:

```powershell
backend\.venv\Scripts\python.exe -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8765
```

Open **http://127.0.0.1:8765**. (Run the detector separately if you want
automatic session tracking — see services below.)

### Production — Windows services (recommended)

From an **elevated** PowerShell (run as Administrator):

```powershell
.\deploy\install-services.ps1 -Port 8765
```

This registers and starts two auto-starting services:

| Service | What it does |
| --- | --- |
| `WorkTrackerAPI` | Serves the UI + API at http://127.0.0.1:8765 |
| `WorkTrackerDetector` | Records work sessions from power on/off |

They start at boot and restart on crash. To remove them:

```powershell
.\deploy\uninstall-services.ps1
```

> Rebuild the frontend (`npm run build`) after changing UI code; the services
> serve `frontend/out` as-is. Restart `WorkTrackerAPI` to pick up backend changes.

### Development (two processes, hot reload)

```powershell
# Terminal 1 — backend on :8000
backend\.venv\Scripts\python.exe -m uvicorn backend.api.main:app --reload --port 8000

# Terminal 2 — frontend dev server on :3000
cd frontend
npm run dev
```

Open **http://localhost:3000**. In dev the UI calls the API on `:8000` (CORS is
preconfigured); in production it calls `/api` on the same origin.

---

## Verify

```powershell
# API health
curl http://127.0.0.1:8765/health        # {"status":"ok"}

# Today's status
curl http://127.0.0.1:8765/api/worktime/today
```

Then open the app and check the dashboard, the **Worktime** calendar, and
**Settings** (theme + targets/holidays).

## Logs

Service logs (when run via NSSM) are written to `logs/`:

```
logs/api.out.log        logs/api.err.log
logs/detector.out.log   logs/detector.err.log
```

---

## Configuration

| Env var | Default | Purpose |
| --- | --- | --- |
| `WORKTIME_DB_PATH` | `backend/data/app.db` | SQLite database location |
| `WORKTIME_STATIC_DIR` | `frontend/out` | Built frontend to serve |

- The API **port** is a launch flag (`--port`) / the install script's `-Port`
  (default **8765**). Dev uses 8000 (backend) and 3000 (Next dev).
- Dynamic settings (theme default, `week_start_day`, detector
  `worktime.heartbeat_seconds`) live in the `settings` table and are editable in
  the app's **Settings** page — no code changes needed.

## How it works (short version)

- The **detector** opens a session on boot, writes a heartbeat each interval, and
  closes the session on shutdown. After a crash/power-loss it recovers the
  orphaned session at its **last heartbeat** (≈1-minute error cap). Its boot is
  retried if the database is briefly busy (the API may be initialising it at the
  same moment on startup).
- **Targets** are historical: a daily target effective from a date, with optional
  per-weekday "short day" overrides; past days keep their old target.
- **Day types** (holiday / leave / vacation) and Sundays turn worked hours into
  **bonus** (counted separately from target completion). Current-month
  completion is **month-to-date**.

## Managing sessions and settings (in the app)

- **Worktime page → calendar:** click a day to see its sessions.
  - **Add session** (manual): set a Start and End. Leave **End empty** to create
    an **open session** (clock-in) with no end yet.
  - **Edit / Delete:** the ✎ on a session opens a form to change its times or
    **Delete** it (two-click confirm). Overlapping sessions are rejected.
- **Worktime → Targets & holidays:** add/remove target rules (daily, per-weekday)
  and mark holidays / leave / vacation.
- **Settings:** theme (light / dark / system) and the dynamic settings stored in
  the database.

Note: in production the detector is the source of automatic sessions; manual
add/edit/delete is for fixing gaps (e.g. a crash day or a forgotten clock-out).
