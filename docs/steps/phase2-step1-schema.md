# Phase 2 · Step 1 — Worktime schema + module registration

**Status:** Done
**Goal:** Create the worktime-owned `sessions` and `targets` tables and register
the module so discovery wires it automatically — proving the modular pattern
with the first real module.

## What was implemented

### `backend/modules/worktime/models.py`
- **`create_sessions`** — `sessions` table:
  - intrinsic (detector-written): `date`, `start_time`, `end_time`,
    `duration_minutes`, `is_sunday`, `last_heartbeat`, `source`.
  - calc-owned/NULLable (Phase 3): `daily_target_hours`, `is_holiday`, `is_bonus`.
  - `source` CHECK ∈ `('auto','manual','crash-recovered')`; the boolean flags
    CHECK ∈ (0,1).
  - indexes: `idx_sessions_date`, and a **partial** `idx_sessions_open`
    (`WHERE end_time IS NULL`) for cheap orphan lookup.
- **`create_targets`** — `targets` table: `effective_from`, `period`
  (CHECK ∈ `('daily','weekly')`), `weekday` (CHECK NULL or 0–6), `daily_hours`;
  index `idx_targets_effective` on `effective_from`.
- **`seed_settings`** — `INSERT OR IGNORE` of `worktime.heartbeat_seconds=60`
  into the shared `settings` table.
- **`WORKTIME_MIGRATIONS`** = `(create_sessions, create_targets, seed_settings)`.
- Constants `SESSION_SOURCES`, `TARGET_PERIODS` as the single source of truth
  for the CHECK lists.

### `backend/modules/worktime/registration.py`
- `register(registry)` → registers `name="worktime"`, `WORKTIME_MIGRATIONS`,
  `router=None` (routes are Phase 4).

### `backend/modules/worktime/__init__.py`
- Re-exports `register` so `core.registry.discover_modules` finds it when it
  imports the package.

## Key decisions

- **Calc columns created but left NULL.** `daily_target_hours`/`is_holiday`/
  `is_bonus` depend on targets & day-types that can change retroactively (case
  A3), so they are owned by the calc layer (Phase 3), not snapshotted at write
  time. `is_sunday` is intrinsic to the date and *is* written by the detector.
- **Durations in minutes (integers)** to avoid float artifacts (case D5).
- **Module settings namespaced** (`worktime.*`) in the shared settings table;
  the heartbeat interval lives with the module, not core (modularity).
- **Partial index for orphans** — `WHERE end_time IS NULL` keeps recovery scans
  cheap as the table grows.
- **`targets.weekday`**: NULL = base (all days), 0–6 = per-weekday override,
  Mon=0…Sun=6 to match `core.calendar`.

## Verification (throwaway temp DB, no repo test files)

- **Discovery picked up `worktime` automatically** — registrations went from
  `['core']` to `['core', 'worktime']` with **no edits to core/`load_all`**
  (open-closed confirmed). 6 migrations total.
- `init_db` (run twice, idempotent) created `sessions` + `targets` with the
  expected columns and 3 `idx_*` indexes.
- Seed `worktime.heartbeat_seconds=60` present.
- CHECK constraints rejected bad `source`, bad `period`, and out-of-range
  `weekday`; a base (NULL) + Friday (4) target coexisted.
- Core's migration set unchanged (still 3) — no leakage.

No new dependencies. Nothing to install for this step.

## Next

Step 2 — Session data-access layer: `open_session`, `update_heartbeat`,
`close_session`, `get_open_sessions`, `get_session`; duration in minutes,
`is_sunday`, and start-day attribution for midnight-crossing sessions (B2).
