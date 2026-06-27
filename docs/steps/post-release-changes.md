# Post-release changes (after the initial 7-phase build)

Changes made while deploying and hardening the app on the target Windows
machine. Grouped by area; the detector fix is the most important.

---

## Deployment / configuration

- **Production port → 8765.** The single API process (UI + `/api`) binds `8765`
  instead of `8000`, because `8000`/`3000` are used by other projects on the
  machine. It's the install script's `-Port` parameter (default 8765); dev is
  unchanged (backend `8000`, Next dev `3000`). No code bakes the port in — the
  production UI calls `/api` **relative** (same origin), so the port is only a
  launch flag.
- **API honours `WORKTIME_DB_PATH`.** The module-level `app` in `api/main.py`
  reads the same env override the detector uses, so both can target a specific
  DB. Default stays `backend/data/app.db`.

## API

- **HEAD requests no longer 405.** The static catch-all in `api/main.py` was
  `@app.get(...)`, so Next.js route prefetches (which use **HEAD**) returned
  405. Changed to `@app.api_route(..., methods=["GET", "HEAD"])`. (Starlette
  strips the body for HEAD automatically.)
- **Month-to-date completion.** Current-period completion % is now to-date (see
  `phase6-postscript-month-to-date.md`).

## NSSM install scripts (`deploy/`)

- **Fixed "Can't open service!" abort.** The idempotency check called
  `nssm status` on a missing service, whose stderr — under
  `ErrorActionPreference = "Stop"` — became a terminating error (PS 5.1 quirk).
  Now existence is checked with `Get-Service -ErrorAction SilentlyContinue`, and
  all `nssm` calls go through an `Invoke-Nssm` helper that runs them under
  `Continue` and returns the exit code. Same helper added to the uninstall
  script.

## Detector (`modules/worktime/detector.py`) — the important one

The detector worked on a manual `nssm start`/`stop` but **not on PC boot /
shutdown**. Root cause: at PC boot, `WorkTrackerAPI` and `WorkTrackerDetector`
auto-start **simultaneously and both initialise the same `app.db`**; the
detector could hit a locked DB and **crash on boot**, after which NSSM throttled
it (Paused). A manual start has no such race (the API is already up), which is
why it worked. With no session opened on boot, there was also nothing to close
on shutdown — explaining both symptoms.

Two changes:

1. **Rewrote the lifecycle to a single-threaded, proven pattern** (mirrors the
   user's old working detector): no heartbeat worker thread / event polling. The
   main thread sleeps in 1s ticks and writes a heartbeat each interval; the
   **stop signal handler closes the session and `sys.exit(0)` directly** (with
   an idempotent guard + `atexit` backstop). Verified: closes within ~1s of a
   Ctrl+C/Ctrl+Break, whether or not the signal interrupts `sleep`.
2. **Boot retry.** `boot()` now retries with capped backoff instead of crashing,
   so a startup DB collision can't kill it; signal handlers are installed *before*
   the retry loop so the service can still be stopped mid-retry.

## Features

- **Delete a session.** `DELETE /api/worktime/sessions/{id}` (+
  `models.delete_session`); the UI shows a two-click **Delete** in the edit-session
  modal.
- **Open session / clock-in (no end time).** `create_session` and the manual
  endpoint accept **no `end_time`** → an open session. The Add-session form's
  **End** field is now optional ("leave empty for an open session"); the edit
  prefill was fixed so editing an already-open session keeps it open.
- **Targets/holidays management endpoints** added earlier in Phase 6:
  `GET /api/worktime/targets`, `DELETE /api/worktime/target/{id}`,
  `GET /api/day-types`.

## Data

- **Migrated the old tracker's history.** Imported 115 sessions
  (2026-02-19 → 06-24, 576 h, `source='manual'`) from
  `C:\devtools\TimeTracker\work-hours.log` into the live DB, with targets
  (5h base; 9h from 06-24; Saturday 5h from 06-24). A timestamped backup is
  written to `backend/data/backups/` and the importer refuses to run twice.
  Note: the old tracker counted Sundays toward the target; in this app Sundays
  are bonus, so those 19 Sundays show as bonus (chosen behaviour).

## Cosmetic

- **Favicon** replaced with a branded `src/app/icon.svg` (indigo "W"); removed
  the default `favicon.ico`.
- **Removed** the create-next-app demo assets from `frontend/public`
  (`next.svg`, `vercel.svg`, `window.svg`, `globe.svg`, `file.svg`).

---

## Applying these (production)

- Frontend changes → `cd frontend && npm run build` (the API serves `out/` from
  disk; no API restart needed for static assets).
- Backend changes → `nssm restart WorkTrackerAPI`.
- Detector change → `nssm restart WorkTrackerDetector`.
