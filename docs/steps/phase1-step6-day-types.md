# Phase 1 · Step 6 — `core/day_types.py` (shared day-type logic)

**Status:** Done
**Goal:** The single place that reads/writes day-type markings and enforces
their rules, so every module (and the calc layer) shares one source of truth.

## What was implemented (`backend/core/day_types.py`)

- **Constants** `WORKDAY / HOLIDAY / LEAVE / VACATION` (enum values; the source
  of truth remains `migrations.DAY_TYPES`).
- **`DayType`** frozen dataclass: `date, type, name, planned, affects_target`
  (with `planned`/`affects_target` as real `bool`s).
- **`default_affects_target(type)`** — holiday/leave/vacation → `True`,
  workday → `False`. Centralises "is this a target-overriding day?".
- **`get_day_type(date)`** → `DayType | None`.
- **`set_day_type(date, type, *, name, planned=False, affects_target=None)`** →
  effective `DayType`. Validates the type, normalises the date, derives
  `affects_target` when not given, and enforces **case C4**.
- **`delete_day_type(date)`** → bool (hit/miss).
- **`list_day_types(start, end)`** → inclusive, date-ordered list.

## Key decisions

- **Case C4 (manual wins) lives here.** On a *planned* write
  (`planned=True`) when a *manual* row already exists, the write is **skipped**
  and the existing row returned — the user's manual decision is preserved. Every
  other combination upserts; in particular a manual write overwrites a planned
  one. (This is the one genuinely rule-bearing piece of the module.)
- **`affects_target` default derived from type** so callers normally don't think
  about it, but can override explicitly.
- **Date normalisation/validation** via `datetime.date.fromisoformat`, which
  also rejects impossible dates (e.g. `2026-13-40`). Accepts both `date` objects
  and ISO strings; always stores zero-padded `YYYY-MM-DD`.
- **Lexicographic range works** because dates are zero-padded ISO strings, so
  `BETWEEN` ordering == chronological ordering (no date parsing in SQL).
- **Type validated in Python first** for a friendly error, in addition to the
  DB `CHECK` constraint as a backstop.

## Incidental refactor

Added **`db.optional_connection(conn, db_path)`** (the "use caller's connection
or open my own" context manager) to `core/db.py` and switched `core/config.py`
to import it, removing config's private duplicate. `day_types.py` uses the same
helper, so all core helpers compose transactions identically.

## Verification (throwaway temp DB, no repo test files)

- Per-type `affects_target` defaults correct.
- set/get round-trip; `date` object accepted.
- Bad date (`2026-13-40`) and bad type (`party`) both rejected with clear errors.
- **C4 sequence:** planned holiday → manual leave overwrites it → a later
  planned holiday write is skipped (manual leave preserved). Planned→planned
  re-plan still updates.
- Range query inclusive & ordered; delete returned `True` then `False`.

No dependencies needed — stdlib only. Nothing to install for this step.

## Next

Step 7 — `core/calendar.py`: week/month boundaries, weekday, Sunday detection,
day-range iteration (honouring the `week_start_day` setting where relevant).
