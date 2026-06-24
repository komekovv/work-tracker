# Phase 1 · Step 5 — `core/config.py` (dynamic settings access)

**Status:** Done
**Goal:** A typed front door over the `settings` table so config can change
without touching code.

## What was implemented (`backend/core/config.py`)

- **`get(key, default=None)`** → raw `str` value, or `default` if unset.
- **`get_bool(key, default=False)`** — parses `1/true/yes/on` and `0/false/no/off`
  (case-insensitive).
- **`get_int(key, default=None)`** / **`get_float(key, default=None)`**.
- **`set(key, value)`** — upsert (`INSERT ... ON CONFLICT(key) DO UPDATE`);
  booleans normalised to `'true'`/`'false'` text.
- **`get_all()`** → `{key: value}` dict, ordered by key.
- **`delete(key)`** → `True` if a row was removed, else `False`.

Every function takes optional `conn` and `db_path` keyword args.

## Key decisions

- **Missing vs malformed.** A *missing* key returns the caller's `default`; a
  key that is *present but unparseable* for the requested type raises
  `ValueError`. Genuine misconfiguration surfaces loudly instead of being masked
  by a silent fallback.
- **Connection composition.** If a `conn` is passed, the function uses it and
  leaves commit/close to the caller (so several `set`s can share one
  transaction). If omitted, it opens a self-managed connection via
  `db.connection` (commit + close handled). Implemented with a small
  `_conn_ctx` helper.
- **Bool serialisation.** `set(key, True)` stores `'true'`; `_to_text` checks
  `bool` before `int` (since `bool` subclasses `int`).
- **`set` upsert via `ON CONFLICT`** keeps the existing row's identity and only
  updates `value` (SQLite 3.24+, well within Python 3.12's bundled SQLite).

## Verification (throwaway temp DB, no repo test files)

- Missing key → default; seeded `theme=system` read back.
- `set` overwrote `theme=dark`.
- Typed round-trips: `get_int→60 (int)`, `get_float→1.5`, `get_bool→True/False`,
  missing bool → supplied default.
- Malformed int (`'sixty'`) → `ValueError` raised.
- `get_all` returned all keys ordered; `delete` returned `True` then `False`.
- Two `set`s sharing one caller-owned connection committed together.

No dependencies needed — stdlib only. Nothing to install for this step.

## Next

Step 6 — `core/day_types.py`: get/set day type for a date, the type enum, the
manual-wins-over-planned rule (case C4), and `affects_target`.
