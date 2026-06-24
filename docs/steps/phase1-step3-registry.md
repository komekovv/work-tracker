# Phase 1 · Step 3 — `core/registry.py` (module registration)

**Status:** Done
**Goal:** The registration system that makes the monolith modular — so the API
app and detector can wire everything by *iterating the registry*, and adding a
module is purely additive (no edits to core or `main.py`).

## What was implemented

### `backend/core/registry.py`
- **`ModuleRegistration`** (frozen dataclass): `name`, `migrations`
  (tuple of `Migration`), `router` (loosely-typed, `None` for table-only units).
- **`Registry`** class:
  - `register(reg)` — adds a registration; raises on duplicate name.
  - `registrations` — all, in registration order.
  - `migrations()` — every registered migration flattened, in order.
  - `routers()` — `(name, router)` only for units that have a router.
  - `init_db(db_path=None)` — runs all registered migrations via
    `db.run_migrations`.
  - `clear()` — reset (for re-discovery within one process).
- **`registry`** — process-wide singleton.
- **`discover_modules(reg)`** — `pkgutil.iter_modules` over `backend.modules`,
  imports each subpackage, and calls its `register(registry)` hook **if present**
  (modules without one are skipped).
- **`load_all(reg=None)`** — the single assembly entry point: registers core
  first, then discovers modules. Used by both the API app and the detector.

### `backend/core/registration.py`
- Core's own `register(registry)` hook. Registers `name="core"` with **empty
  migrations for now** (the `settings`/`day_types` tables are appended in Step 4)
  and `router=None` (core routes come in Phase 4).

## Key decisions

- **Registry imports with stdlib only.** The `router` is typed `Any` instead of
  importing `fastapi`, so the data/registry layer is fully usable before the web
  stack is installed. FastAPI router types are validated later, at mount time
  (Phase 4).
- **Core is treated like a module** for wiring, and registered **first**, so its
  shared tables underpin feature modules.
- **Discovery is additive & tolerant.** A module opts in via a `register(registry)`
  hook; a package without one (like the currently-empty `worktime`) is silently
  skipped. This is what delivers the open-closed promise: new module = new folder
  with a hook, nothing else touched.
- **Order matters and is preserved** — `dict` insertion order drives both
  migration order and router-mount order.
- **Lazy imports in `load_all`** avoid an import cycle (`registration` imports
  back into `registry`).

## Verification (throwaway temp DB, no repo test files)

- Two registrations → `migrations()` flattened to 2; `routers()` returned only
  the one with a router.
- Duplicate name → `ValueError` raised.
- `init_db()` created both tables, migrations called in registration order.
- `load_all()` on the real packages → registered `['core']` and skipped the
  empty `worktime` package without error.

No dependencies needed — stdlib only. Nothing to install for this step.

## Next

Step 4 — Core tables: add `settings` + `day_types` migrations (and seed) and
append them to core's registration so `init_db()` actually creates the shared
schema.
