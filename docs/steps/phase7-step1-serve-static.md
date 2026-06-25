# Phase 7 · Step 1 — FastAPI serves the static frontend

**Status:** Done
**Goal:** Serve the built Next.js export from FastAPI so the app is a single
origin (no separate Next process in production).

## What was implemented (`backend/api/main.py`)

- **`_mount_static(app, static_dir)`** — a catch-all `GET /{full_path:path}`
  (registered **last**, `include_in_schema=False`) that resolves clean routes to
  the export's files:
  1. `/` → `index.html`;
  2. an existing file → served as-is (`_next/...`, `favicon.ico`, `*.svg`);
  3. `/<route>` → `<route>.html` (e.g. `/worktime` → `worktime.html`,
     `/worktime/settings` → `worktime/settings.html`);
  4. directory `index.html` if present;
  5. otherwise `404.html` with status 404.
  Includes a path-traversal guard (target must stay under the static root).
- **`create_app`** mounts it **only if the static dir exists**, after the routers
  and `/health`, so `/api/*` always wins and dev (no `out/`) is unaffected.
- Static dir = `frontend/out` relative to the repo, overridable via
  `WORKTIME_STATIC_DIR`.

## Key decisions

- **Custom resolver over `StaticFiles(html=True)`** — the export writes flat
  `<route>.html` files (not `<route>/index.html`), which `StaticFiles` wouldn't
  map for `/worktime`. The resolver keeps clean (no-trailing-slash) URLs.
- **Mounted last + `include_in_schema=False`** so it never shadows the API,
  `/health`, `/docs`, or `/openapi.json`.
- **Conditional mount** keeps one codebase working in both dev (Next dev serves
  UI) and prod (FastAPI serves `out/`).
- The frontend's production build already uses a **relative API base**
  (`NEXT_PUBLIC_API_BASE_URL` empty in prod), so the served UI calls `/api/*` on
  the same origin — no CORS needed in production.

## Verification

Ran **only** the API process (`uvicorn backend.api.main:app`) against `out/`:
- `/`, `/worktime`, `/settings`, `/worktime/settings` → 200 text/html;
  `/favicon.ico` → 200 image/x-icon; unknown route → 404 (`404.html`).
- `/_next/static/...js` → 200 application/javascript.
- `/api/worktime/today` → 200 application/json (API not shadowed); root HTML
  contains "Work Tracker".
- **Browser loaded `http://127.0.0.1:8000/`** (the API origin) and the dashboard
  rendered real data fetched same-origin — Month total 75.0h, Target 42% (MTD),
  Bonus 13.0h.

No new dependencies.

## Next

Step 2 — NSSM service scripts for the detector and the API (install/uninstall).
