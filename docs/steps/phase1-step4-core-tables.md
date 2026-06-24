# Phase 1 · Step 4 — Core tables (`settings` + `day_types`)

**Status:** Done
**Goal:** Create the two shared, core-owned tables and wire their migrations
into core's registration so `registry.init_db()` builds the real schema.

## What was implemented

### `backend/core/migrations.py`
- **`DAY_TYPES`** — `("workday", "holiday", "leave", "vacation")`, the single
  source of truth reused by the DB constraint and (Step 6) the day-type logic.
- **`create_settings(conn)`** — `settings(key TEXT PRIMARY KEY, value TEXT NOT NULL)`.
- **`create_day_types(conn)`** — `day_types` with:
  - `date TEXT PRIMARY KEY` (one row per 'YYYY-MM-DD' date),
  - `type TEXT NOT NULL CHECK (type IN (...))` — enum enforced in the DB,
  - `name TEXT`,
  - `planned INTEGER NOT NULL DEFAULT 0 CHECK (planned IN (0,1))` — 1=in advance, 0=manual,
  - `affects_target INTEGER NOT NULL DEFAULT 1 CHECK (affects_target IN (0,1))`.
- **`seed_settings(conn)`** — `INSERT OR IGNORE` of default core settings:
  `theme=system`, `week_start_day=monday`.
- **`CORE_MIGRATIONS`** — `(create_settings, create_day_types, seed_settings)`,
  ordered so tables exist before seeding.

### `backend/core/registration.py`
- Now imports `CORE_MIGRATIONS` and registers core with them (was empty in
  Step 3).

## Key decisions

- **`date` as PRIMARY KEY** gives the plan's required per-date uniqueness
  without a surrogate `id` — natural and enough.
- **DB-level `CHECK` constraints** enforce the type enum and the 0/1 flags, so
  invalid data can't be written even by a buggy caller (verified: bad `type`
  and duplicate `date` both rejected).
- **Only genuinely-core settings are seeded.** Module-specific defaults (e.g.
  the detector's heartbeat interval) belong to that module, keeping core free of
  worktime knowledge (modularity rule).
- **`INSERT OR IGNORE` for seeds** — re-running migrations never clobbers a
  value the user later changed. (Settings *values* are stored as TEXT; typed
  access is Step 5's job.)
- **`affects_target` defaults to 1**; the calc layer (Phase 3) decides how each
  day type uses it.

## Verification (throwaway temp DB, no repo test files)

Assembled via `load_all()` + `init_db()` (run twice — idempotent):
- Tables `settings`, `day_types` created with the expected columns.
- Seeds present: `{theme: system, week_start_day: monday}`.
- `type` CHECK rejected `'nonsense'`; duplicate `date` rejected by the PK.
- A valid `day_types` insert stored correctly with `affects_target=1` default.

No dependencies needed — stdlib only. Nothing to install for this step.

## Next

Step 5 — `core/config.py`: typed read/write access over the `settings` table
(get with default, set, get-all) so config changes never touch code.
