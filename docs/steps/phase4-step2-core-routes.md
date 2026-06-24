# Phase 4 · Step 2 — Core routes (settings + day-type)

**Status:** Done
**Goal:** Expose the core logic over HTTP — dynamic settings and day-type
markings — mounted via the registry with no change to `main.py`.

## What was implemented

### `backend/core/schemas.py`
- `DayTypeName = Literal["workday","holiday","leave","vacation"]`.
- `DayTypeIn` (date, type, name?, planned=False, affects_target?) and
  `DayTypeOut`. `date` fields use `datetime.date` so FastAPI validates the
  format (bad date → 422).

### `backend/core/routes.py` (`APIRouter(prefix="/api")`)
- `GET /api/settings` → full key→value map.
- `POST /api/settings` → bulk upsert (one shared transaction), returns the
  updated map.
- `POST /api/day-type` → set a marking, returns the effective `DayTypeOut`
  (honours case C4 in the logic layer).
- `DELETE /api/day-type/{day}` → 204, or **404** if the date wasn't marked.

### `backend/core/registration.py`
- Added `_core_router_factory` (lazy `from backend.core.routes import router`)
  and set it as the registration's `router_factory`.

## Key decisions

- **Handlers stay thin** — they validate via Pydantic, then delegate to
  `config` / `day_types`, which already own the rules (C4, date validation).
  No business logic duplicated in the API layer.
- **Lazy router factory** keeps importing `core.registration` (and thus the
  detector's `load_all`) FastAPI-free; the route module is imported only when
  `main.py` mounts.
- **`date`-typed fields** give automatic 422s for malformed dates without
  hand-written checks.
- **Bulk settings POST** in a single transaction so a multi-field settings save
  is atomic.

## Verification (venv python, TestClient)

- Core router **mounted with no edit to `main.py`**: `/api/settings`,
  `/api/day-type`, `/api/day-type/{day}`.
- Settings GET → seeds; POST `{theme:dark, custom:42}` → merged & persisted.
- Day-type **C4 over HTTP**: planned holiday → manual leave overwrites →
  replanned holiday skipped, manual leave preserved.
- DELETE → 204, repeat → 404.
- `type:"party"` → 422; `date:"2026-13-40"` → 422.

No new dependencies.

## Next

Step 3 — Worktime read routes: `today`, `stats`, `kpi`, `sessions` (GET),
`calendar`, with response schemas (minutes-only per the API-units decision).
