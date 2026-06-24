# Phase 4 · Step 1 — App skeleton + registry router wiring

**Status:** Done
**Goal:** A FastAPI app that mounts module routers by iterating the registry and
runs migrations on startup — without forcing FastAPI onto the detector.

## What was implemented

### Registry change → lazy router factories (`core/registry.py`)
- `ModuleRegistration.router` (an instance) → **`router_factory`** (a
  `Callable[[], APIRouter]`).
- `Registry.routers()` now **calls each factory** at iteration time.
- Updated `core/registration.py` and `worktime/registration.py` to drop the old
  `router=None`.

**Why:** importing a module / running `load_all` no longer touches FastAPI; only
the API layer (which iterates `routers()`) does. The detector and data/calc/kpi
layers stay standard-library-only.

### `backend/api/deps.py`
- `get_db_path(request)` — reads `app.state.db_path` (defaults to real `DB_PATH`),
  so the app can be pointed at any DB (tests, NSSM).

### `backend/api/main.py`
- `create_app(db_path=None)` — sets `app.state.db_path`, assembles
  `load_all(Registry())`, mounts every `registry.routers()` entry via
  `include_router`, adds dev CORS, and defines `GET /health`.
- `_lifespan` runs `registry.init_db` **on startup** (not at import), so
  importing the module doesn't write to the DB.
- Module-level `app = create_app()` for `uvicorn backend.api.main:app`.

## Key decisions

- **Lazy router factories** (above) — the load-bearing decision; verified the
  detector imports with no FastAPI present.
- **Migrations on startup via lifespan**, so `import backend.api.main` has no DB
  side effects; the real `app.db` is created only when the server actually runs.
- **`db_path` on `app.state`** + a dependency, giving clean per-app DB injection
  for verification without globals.
- **Dev CORS** for `localhost:3000` only; production serves the static export
  same-origin (Phase 7).

## Verification

Using `backend/.venv/Scripts/python.exe` (see [[venv-python]]):
- `create_app(db_path=tmp)` → DB absent before startup; after `TestClient`
  enters (triggers lifespan) the 4 tables exist → migrations ran on startup.
- `GET /health` → `200 {"status":"ok"}`.
- Only `/health` mounted (no module routers yet) — wiring present and empty.

Using **system** Python (no FastAPI installed):
- `import backend.modules.worktime.detector` + `load_all()` succeeded with
  `fastapi` never imported — the detector is confirmed FastAPI-free.

No new dependencies (FastAPI already in `.venv`).

## Next

Step 2 — Core routes: `GET/POST /api/settings`, `POST /api/day-type`,
`DELETE /api/day-type/{date}`, wired via core's `router_factory` (should mount
with no edit to `main.py`).
