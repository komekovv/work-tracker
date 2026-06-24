# Phase 2 · Step 5 — `detector.py` (the service)

**Status:** Done
**Goal:** A runnable, long-lived service that opens a session on boot,
heartbeats while running, and closes cleanly on shutdown — the piece NSSM will
run in Phase 7.

## What was implemented (`backend/modules/worktime/detector.py`)

- **`Detector`** class:
  - **`boot()`** — fresh `Registry()` → `load_all` → `init_db`, then
    `recover_orphans()` **before** `open_session()` (so the new session is never
    swept up as an orphan). Returns the new session id.
  - **`heartbeat_seconds`** — from the constructor override, else the dynamic
    `worktime.heartbeat_seconds` setting (guarded against non-positive values,
    default 60).
  - **`_heartbeat_loop()`** — runs in a daemon thread; stamps `last_heartbeat`
    each interval; a transient DB error is logged, not fatal.
  - **`run()`** — boots, installs signal handlers, starts the heartbeat thread,
    and blocks the main thread polling the stop event in short (0.5s) slices so
    signals are serviced promptly; on stop, joins the worker and closes.
  - **`close()`** — idempotent: a `Lock` + `_closed` flag plus the DB-level
    double-close guard mean the signal handler, the loop `finally`, and the
    `atexit` backstop can all call it safely.
  - **Signals** — installs SIGINT, SIGTERM, and SIGBREAK (Windows-only, guarded)
    handlers that just set the stop event.
- **`main()`** — configures logging, honours an optional `WORKTIME_DB_PATH` env
  override, and runs the detector. Entrypoint: `python -m
  backend.modules.worktime.detector`.

## Key decisions

- **Worker-thread heartbeat + short-poll main loop.** This keeps shutdown
  responsive on Windows, where a handler that sets a flag won't interrupt a long
  blocking `wait`. The main thread waking every 0.5s lets Python run the pending
  signal handler and notice the stop quickly, independent of the heartbeat
  interval.
- **Idempotent close, three ways in.** Signal, normal loop exit, and `atexit`
  can each trigger `close()`; the lock+flag+DB-guard make extra calls no-ops —
  no double-close, no error.
- **Fresh registry per boot** avoids the singleton's duplicate-registration
  error if a detector is booted more than once in a process.
- **Boot order is load-bearing:** recover orphans, *then* open — verified.
- **`WORKTIME_DB_PATH` env override** lets NSSM (and verification) target a
  specific DB without code changes; the heartbeat interval stays a DB setting.

## Verification (throwaway temp DB, no repo test files)

**In-process logic:** pre-seeded an orphan, then `boot()` recovered it
(`source=crash-recovered`, closed at its last heartbeat) and opened a new
session; only the new session stayed open; `close()` worked and a second
`close()` was a safe no-op.

**Real subprocess run:** launched `python -m backend.modules.worktime.detector`
against a temp DB with a 1s heartbeat in a new process group; after ~3.5s the
session's `last_heartbeat` had advanced past `start_time` (~3 beats); sent
`CTRL_BREAK_EVENT`; the process logged "Received signal 21; shutting down",
closed the session (`source=auto`), left nothing open, and exited **0**.

No new dependencies. Nothing to install for this step.

## Next

Step 6 — Phase 2 end-to-end verification: power-on/off cycles, multiple
sessions/day, crash→recovery, midnight attribution, targets present.
