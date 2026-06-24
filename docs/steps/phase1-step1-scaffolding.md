# Phase 1 · Step 1 — Backend Scaffolding

**Status:** Done
**Goal:** Create an empty but importable backend package skeleton matching the
plan's modular-monolith layout, plus the dependency manifest. No logic yet.

## What was created

```
backend/
├── __init__.py            # backend package docstring
├── core/__init__.py       # shared infrastructure (empty for now)
├── modules/
│   ├── __init__.py
│   └── worktime/__init__.py   # first feature module (empty for now)
├── api/__init__.py        # FastAPI app layer (empty for now)
├── data/.gitkeep          # holds runtime app.db (DB itself is gitignored)
└── requirements.txt       # backend dependencies
```

`docs/steps/` was also created to hold these per-step docs.

## Key decisions

- **Everything is a Python package** (`__init__.py` in each folder) so modules
  can be imported as `backend.core`, `backend.modules.worktime`, etc. Imports
  are run from the **repo root** (not from inside `backend/`).
- **`data/` is tracked via `.gitkeep`**, but the runtime SQLite DB is not.
  Added to `.gitignore`: `backend/data/app.db`, plus the `-wal` and `-shm`
  sidecar files that WAL mode produces (relevant from Step 2 onward).
- **`requirements.txt` lists only `fastapi[standard]>=0.136.1,<0.137.0`.**
  The narrow pin is mandatory because FastAPI is 0.x (minor releases can
  break). `[standard]` brings Uvicorn; Pydantic v2 comes with FastAPI;
  SQLite is the stdlib `sqlite3`, so neither is listed separately.

## Verification

- `python -c "import backend.core, backend.modules.worktime, backend.api"`
  → `imports OK` (run from repo root).
- Python 3.12.3 confirmed (plan targets 3.12).
- File tree matches the plan's structure.

## Install command for the user (not run by me)

Dependencies are **not** installed yet. When ready, from `backend/`:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

(Not strictly required until the API in Phase 4 / Step 2's DB work uses only
the stdlib — but installing now sets up the environment early.)

## Next

Step 2 — `core/db.py`: SQLite connection (WAL + busy timeout) and the
`CREATE TABLE IF NOT EXISTS` migration runner.
