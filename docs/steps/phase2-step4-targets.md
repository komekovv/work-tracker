# Phase 2 · Step 4 — Targets data-access

**Status:** Done
**Goal:** Store and list historical target rules. Resolution (which rule applies
to a day) is deferred to the calc layer (Phase 3).

## What was implemented (added to `backend/modules/worktime/models.py`)

- **`Target`** frozen dataclass: `id, effective_from, period, weekday, daily_hours`.
- **`set_target(effective_from, daily_hours, *, period="daily", weekday=None)`**
  → id. Validates `period`, `weekday` (None or 0–6, with a `bool` guard), and
  `daily_hours >= 0`; normalises `effective_from` via `cal.to_date`.
  **Replace-on-same-key**: deletes any existing rule with the same
  `(effective_from, period, weekday)` before inserting.
- **`list_targets()`** → all rules ordered by `effective_from`, then `weekday`
  (NULL/base first), then `id`.
- **`delete_target(id)`** → bool.

## Key decisions

- **Append-by-date history, replace-on-correction.** A *new* `effective_from`
  adds a row (case A1 — past days keep their old target); re-setting the *same*
  `(effective_from, period, weekday)` replaces it, so fixing a typo doesn't leave
  two conflicting rules for the same key. NULL weekday is matched explicitly
  (`weekday IS NULL`) since `NULL != NULL` in SQL.
- **Storage only.** Picking the effective rule for a date — most recent
  `effective_from` on/before the day, weekday override beating the base
  (A1–A4) — is intentionally left to Phase 3 so the data layer stays dumb.
- **Validation here too**, on top of the DB CHECKs, for friendly errors
  (`bool` weekday → `TypeError`, others → `ValueError`).
- **Ordering puts the base rule first** per date (SQLite sorts NULLs first
  ascending), which is the natural reading order for a settings UI.

## Verification (throwaway temp DB, no repo test files)

- **A2:** base 9h + Friday(4) 5h override coexist.
- Replace-on-same-key: correcting base → 8h kept the row count at 2 (no dup).
- **A1:** adding `2026-07-01` accumulated as history; ordering correct; earlier
  row preserved.
- `date` object accepted.
- Rejected: bad `period`, out-of-range `weekday`, `bool` weekday, impossible
  date, negative hours.
- `delete_target` returned `True` (hit) then `False` (miss).

No new dependencies. Nothing to install for this step.

## Next

Step 5 — `detector.py`: the runnable service (boot → recover_orphans →
open_session, heartbeat loop, signal/atexit shutdown with double-close guard).
