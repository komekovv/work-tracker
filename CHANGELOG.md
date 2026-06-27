# Changelog

Notable changes to the Work-Time & KPI Tracker. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/). Per-step build notes live in
[`docs/steps/`](docs/steps/).

## 2026-06-27 — Worktime page: Week / Month / Custom summary tabs

Full details: [`docs/steps/post-release-worktime-summary-tabs.md`](docs/steps/post-release-worktime-summary-tabs.md).

### Added
- **Day / Week / Month / Custom tabs** on the Worktime page's side panel. *Day*
  keeps the per-day view; *Week / Month / Custom* show aggregate stats (worked,
  target, over/under, completion %, bonus, days met) for the range. Month follows
  the calendar's viewed month; Week follows the selected day; Custom takes a date range.
- **`GET /api/worktime/summary`** (`period=week|month&anchor=` or `from`/`to`,
  optional `as_of`) returning `PeriodStatsOut`. Unlike `/stats`, it picks the range
  independently of the to-date cap, so a **past** month/week returns its full range
  while the current one stays to-date.

## 2026-06-27 — Debt / hours-owed dashboard card

Full details: [`docs/steps/post-release-debt-feature.md`](docs/steps/post-release-debt-feature.md).

### Added
- **"Hours owed" dashboard card** answering how far behind/ahead you are for this
  week, this month, or a custom date range — with a reconciling *why-short*
  breakdown (didn't come in / came in under / surplus credit), work days left, and
  the daily pace needed to catch up.
- **`GET /api/worktime/debt`** (`period=week|month` or `from`/`to`, plus `as_of`) —
  net debt/surplus, breakdown, and remaining projection. Debt counts completed days
  only; today and beyond feed the projection. Built on the existing live calc layer,
  so historical targets and bonus days (leave/vacation/holiday/Sunday) are honored.

## 2026-06-25 — Post-release hardening & features

Full details: [`docs/steps/post-release-changes.md`](docs/steps/post-release-changes.md).

### Added
- **Delete a session** — `DELETE /api/worktime/sessions/{id}` and a two-click
  Delete in the edit-session modal.
- **Open session / clock-in** — manual sessions can be created with **no end
  time** (the Add-session form's *End* is now optional).

### Changed
- **Production port → 8765** (configurable via the install script's `-Port`;
  dev unchanged on 8000/3000). See [`prod-port`](docs/steps/).
- **Detector rewritten** to a single-threaded, signal-handler-closes pattern,
  **plus boot-retry** — fixes the detector not recording on **PC boot/shutdown**
  (it raced the API to initialise the DB at startup and could crash).
- **Current-month completion is month-to-date**
  ([`phase6-postscript-month-to-date.md`](docs/steps/phase6-postscript-month-to-date.md)).

### Fixed
- **HEAD requests returned 405** on the static routes (Next.js prefetch) — the
  catch-all now accepts `GET` and `HEAD`.
- **NSSM install script aborted** with "Can't open service!" — existence is now
  checked via `Get-Service` and `nssm` calls run through a tolerant helper.

### Data
- **Migrated** the previous tracker's log (115 sessions, ~576 h) and targets into
  the database; a timestamped backup is kept under `backend/data/backups/`.

### Cosmetic
- Branded **favicon** (`src/app/icon.svg`); removed create-next-app demo assets
  from `frontend/public`.

## 2026-06-24 — Initial build (Phases 1–7)

The full application, built and verified phase by phase
([`docs/PROJECT_PLAN_EN.md`](docs/PROJECT_PLAN_EN.md),
per-step logs in [`docs/steps/`](docs/steps/)):

1. **Core** — SQLite (WAL) + migrations, module registry, settings, day-types,
   calendar helpers.
2. **Worktime detector + data** — `sessions`/`targets`, heartbeat, crash
   (orphan) recovery at last heartbeat.
3. **Calc + KPI** — historical targets, bonus rules, streak, trend, comparison.
4. **API** — FastAPI app with registry-driven routers; full endpoints.
5. **Frontend core + dashboard** — Next.js static export, theme, KPI cards,
   heatmap, trend chart.
6. **Frontend calendar + settings** — calendar with session add/edit, target &
   holiday management, general settings, responsive.
7. **Integration** — FastAPI serves the static build; NSSM services for the
   detector + API; README.
