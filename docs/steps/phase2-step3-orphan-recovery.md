# Phase 2 · Step 3 — Orphan recovery

**Status:** Done
**Goal:** Recover sessions left open by a crash / power-loss, capping the timing
error at ~one heartbeat (case B3).

## What was implemented (added to `backend/modules/worktime/models.py`)

- **`recover_orphans(*, conn=None, db_path=None) -> list[int]`**
  - Selects sessions with `end_time IS NULL`.
  - Closes each at its **`last_heartbeat`** (defensively falling back to
    `start_time` if somehow NULL), computes `duration_minutes`, and sets
    `source='crash-recovered'`.
  - Returns the list of recovered session ids (for the detector to log).

## Key decisions

- **End at the last heartbeat, never `now`.** This is the whole point of B3: on
  an unclean shutdown no SIGTERM fires, so the row is stuck open. Using the last
  heartbeat bounds the error to the heartbeat interval instead of counting all
  the powered-off time. Verified: a 09:00 session heartbeating to 09:47 recovers
  with `end_time=09:47` and `duration=47`, not the wall-clock time.
- **Must run before opening the new session.** Documented in the docstring; the
  detector (Step 5) calls `recover_orphans()` then `open_session()` so the fresh
  session isn't itself swept up.
- **Crash-before-first-heartbeat edge.** `open_session` seeds
  `last_heartbeat = start_time`, so this path yields `end == start`,
  `duration = 0` — verified.
- **Idempotent / scoped.** Only currently-open rows are touched; a second call
  with no orphans returns `[]`, and already-closed sessions keep their original
  `source` and duration.
- **Batch-safe.** All orphans are recovered within one transaction; multiple
  orphans handled in a single call.

## Verification (throwaway temp DB, no repo test files)

- Orphan (heartbeats to 09:47, never closed) → `end_time == last_heartbeat`
  (≠ now), `duration=47`, `source='crash-recovered'`, no longer open.
- Crash before first heartbeat → `duration=0`, `end==start`, crash-recovered.
- No orphans → `[]`; a normally-closed session stayed `source='auto'`/120 min.
- Two orphans recovered together in one call.

No new dependencies. Nothing to install for this step.

## Next

Step 4 — Targets data-access: `set_target`, `list_targets` (storage only;
resolution of which target applies is Phase 3).
