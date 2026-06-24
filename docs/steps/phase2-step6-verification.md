# Phase 2 · Step 6 — End-to-end verification

**Status:** Done
**Goal:** Prove the whole worktime data + detector stack: sessions are written
when the computer powers on/off, and a crash is recovered at the last heartbeat.

## What was verified

### Real detector power cycles (live subprocesses, 1s heartbeat)
1. **Power-on #1** — detector booted, opened session 1, heartbeated.
2. **Power-loss** — the process was **hard-killed** (`TerminateProcess`, no
   graceful shutdown), leaving session 1 open (an orphan), heartbeat frozen at
   `15:29:12`.
3. **Power-on #2** — a second detector booted, **recovered orphan 1** at its
   last heartbeat (`end_time == 15:29:12`, `source='crash-recovered'`) — proven
   to be **neither the kill time nor the reboot time** (`end < session2.start`) —
   and opened session 2 (B3 in the real flow).
4. **Power-off #2** — `CTRL_BREAK` → session 2 closed cleanly (`source='auto'`);
   no sessions left open.

### Cases re-confirmed together (data layer)
- **B1** — two sessions on one day summed to 270 minutes.
- **B2** — a 23:00→01:00 session stayed on its start day (`2026-03-03`,
  120 min); the next day had 0 sessions.
- **Targets A1/A2** — base 9h + Friday(4) 5h override, plus a later
  `effective_from` (8h) coexisting as history.

### Structural assertions
- Registrations exactly `['core', 'worktime']`.
- Tables exactly `{day_types, sessions, settings, targets}`.

## Outcome — Phase 2 done

The worktime module records real sessions from the detector's power-on/off
lifecycle, recovers crash-orphaned sessions at the last heartbeat, stores
historical targets, and remains cleanly modular. Calc fields on `sessions`
(`daily_target_hours`, `is_holiday`, `is_bonus`) remain NULL by design — they
are Phase 3's job.

## Next (Phase 3 preview)

`modules/worktime/calc.py` (target resolution A1–A4, bonus rules C1–C5,
over/under) and `kpi.py` (streak, trend, comparison, completion %), reading the
sessions/targets/day_types recorded here.
