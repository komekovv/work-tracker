# Phase 2 · Step 2 — Session data-access layer

**Status:** Done
**Goal:** The functions that read/write `sessions` — the open→heartbeat→close
lifecycle the detector will drive — with correct duration, day attribution, and
a double-close guard.

## What was implemented (added to `backend/modules/worktime/models.py`)

- **`Session`** frozen dataclass mirroring the table (`is_holiday`/`is_bonus`
  stay `None` until Phase 3; `is_sunday` always set).
- **`open_session(start_time=None, *, source="auto")`** → new id. Sets `date`
  from the **start day** (B2), `is_sunday` from the date, and seeds
  `last_heartbeat = start_time` (so a crash before the first heartbeat still has
  a recovery point — Step 3).
- **`update_heartbeat(session_id, when=None)`** → bool. Advances
  `last_heartbeat` only for **open** sessions (`end_time IS NULL`); returns
  False for unknown/closed.
- **`close_session(session_id, end_time=None)`** → bool. Computes
  `duration_minutes`; returns False if already closed/unknown — a DB-level
  **double-close guard**.
- **`get_session`**, **`get_open_sessions`**, **`get_sessions_by_date`** readers.
- Helpers: `duration_minutes_between`, `_iso` (second-precision ISO),
  `_row_to_session`, `_opt_bool`.

## Key decisions

- **Start-day attribution (B2):** `date` is derived from `start_time`, so a
  session crossing midnight belongs to the day it began (verified: 23:00→01:00
  stays on the start date; the next day gets 0 sessions).
- **Durations in whole minutes, clamped ≥ 0** (`round(seconds/60)`) — avoids
  float artifacts (D5) and guards against minor clock skew.
- **Second-precision ISO timestamps** via `isoformat(timespec="seconds")` for
  clean, parseable storage.
- **Open-only mutations:** both heartbeat and close filter on
  `end_time IS NULL`, so closed sessions are immutable through this layer; the
  double-close guard returns False rather than raising (callers treat it as a
  no-op).
- **Injectable timestamps:** every function accepts an explicit `datetime`
  (defaulting to `now()`), enabling deterministic verification and giving the
  detector/orphan-recovery precise control (e.g. closing at the *last
  heartbeat*).

## Verification (throwaway temp DB, no repo test files)

- Round trip: open 09:00 → heartbeat → close 11:30 ⇒ `duration_minutes=150`.
- Double-close returned `False`; heartbeat on a closed session returned `False`.
- **B1:** three sessions on one day summed to 240 minutes.
- **B2:** 23:00→01:00 attributed to `2026-06-24` (the 25th had 0 sessions).
- Sunday flag set intrinsically for a Sunday start.

No new dependencies. Nothing to install for this step.

## Next

Step 3 — Orphan recovery: `recover_orphans()` closes crash-left sessions using
the **last heartbeat** (not current time), `source='crash-recovered'`.
