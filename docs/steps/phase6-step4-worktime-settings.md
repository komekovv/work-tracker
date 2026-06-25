# Phase 6 · Step 4 — Worktime settings (targets + holidays)

**Status:** Done
**Goal:** Manage targets and day-type markings from the UI.

## Backend additions

- **`GET /api/worktime/targets`** → `list[TargetOut]` (wraps `models.list_targets`).
- **`DELETE /api/worktime/target/{id}`** → 204, or 404 if missing.
- **`GET /api/day-types?from=&to=`** (core) → `list[DayTypeOut]` (wraps
  `core.day_types.list_day_types`). Also refactored the `DayTypeOut` mapping into
  a shared `_to_out` helper in `core/routes.py`.

## Frontend

- **`src/lib/api.ts`** — `getTargets`, `deleteTarget`, `getDayTypes`.
- **`src/components/modules/worktime/target-settings.tsx`** — add-target form
  (effective-from, hours, "Applies to" = All days / weekday) + list with Remove.
- **`src/components/modules/worktime/holiday-settings.tsx`** — mark-day form
  (date, type holiday/leave/vacation, optional name) + list (current year) with
  Remove.
- **`src/app/worktime/settings/page.tsx`** — composes both sections.

## Key decisions

- **Reused existing data-layer functions** (`list_targets`/`delete_target`/
  `list_day_types`) — the endpoints are thin wrappers; no new logic.
- **`GET /day-types` added** (not in the original §6 list) because the
  management UI needs to show existing markings; scoped by `from`/`to`.
- **UI exposes only `daily` targets** (weekday override for short days); weekly-
  period targets aren't surfaced since the calc layer resolves dailies. Historical
  behaviour is explained inline ("past days keep their old target").
- **Errors surfaced via `ApiError`** in each form's alert, same pattern as the
  session modal.

## Verification

- **Backend (curl, after restart):** `/targets` → both rules (base 8h, Friday 4h);
  `/day-types` (year) → the 06-18 holiday; `DELETE /target/99999` → 404.
- **Frontend (live):** settings page rendered both target rows and the holiday
  list with their forms. Clicking **Mark day** added a holiday for "today"
  (2026-06-25 — the clock rolled over mid-session) and the list reloaded to show
  it. Delete buttons call the verified delete endpoints.
- `npm run build` passes; routes `/worktime/settings` prerendered.

## Next

Step 5 — General settings page: theme control + dynamic settings editor
(`getSettings`/`updateSettings`, incl. `week_start_day`).
