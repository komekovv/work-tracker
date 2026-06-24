# Phase 1 · Step 8 — Core verification

**Status:** Done
**Goal:** Prove the whole core works together — "empty but working core, ready
to accept modules."

## What was verified

A single end-to-end smoke pass against the **real default `app.db`** path
(created, then cleaned up afterward since it's a regenerable runtime artifact).
It exercised every core module in one chain:

1. **Assembly** — `load_all()` registered only `core` (the empty `worktime`
   package was discovered and skipped); 3 migrations collected.
2. **Schema build** — `init_db()` created `backend/data/app.db` in **WAL** mode;
   running it twice stayed idempotent.
3. **Tables** — exactly `settings` and `day_types`.
4. **Seeds** — `{theme: system, week_start_day: monday}`.
5. **config** — typed `get_int` round-trip; missing key → default.
6. **day_types / case C4** — planned holiday → manual leave overwrote it → a
   later planned write was skipped; effective marking stayed `leave / manual`.
7. **calendar** — `weekday(Wed)=2`, `week_bounds` honoured the seeded Monday
   start, `month_bounds(June)` correct, Sunday detection correct.
8. **Modularity assertion** — registrations were exactly `["core"]` and tables
   exactly `{settings, day_types}`; no module leakage. Asserted in-run.

All checks passed; the temporary `app.db` (+ WAL/SHM) was deleted, leaving a
clean tree.

## Sanity checks

- `python -m compileall` over `core/`, `api/`, `modules/` — all compile.
- Final core code tree:
  ```
  backend/core/{__init__,db,registry,registration,migrations,config,day_types,calendar}.py
  backend/{api,modules,modules/worktime}/__init__.py
  backend/data/.gitkeep   backend/requirements.txt
  ```
- `.venv` (deps now installed by the user) and the runtime DB are gitignored.

## Phase 1 — Done

The core provides: a WAL SQLite connection + migration runner, a module
registry with auto-discovery, the shared `settings` and `day_types` tables,
typed settings access, day-type logic (incl. case C4), and calendar helpers.
Nothing module-specific has leaked into core. Ready for **Phase 2 — Worktime
detector + data model**.

## Next (Phase 2 preview)

`modules/worktime/`: `detector.py` (boot/heartbeat/shutdown/orphan recovery),
`models.py` (`sessions`, `targets` tables), and the module's `register()` hook
so discovery wires it automatically.
