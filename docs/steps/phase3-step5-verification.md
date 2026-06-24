# Phase 3 · Step 5 — End-to-end verification

**Status:** Done
**Goal:** Prove calc + KPI together on a realistic scenario with a mid-stream
target change, bonus days, streak, comparison, and trend.

## Scenario

Two weeks (Jun 8–21, 2026) with:
- targets: base 8h, Friday(4)=4h, **base → 6h from 2026-06-15**;
- a worked **holiday** (06-12 Fri, 3h), a worked **leave** (06-18 Thu, 5h), a
  worked **Sunday** (06-14, 2h), and an idle Sunday (06-21);
- a mix of met and missed normal days.

## What was verified (with assertions)

- **Target resolution** — 06-10 → 8h, 06-17 → 6h (A1 change), 06-19 Friday → 4h
  (A4 weekday persists over the newer base).
- **Bonus classification** — holiday worked → bonus 180/target 0/met None (C1);
  leave worked → bonus 300/met None (C2/C3); Sunday worked → bonus 120 (C5
  single-count basis); idle Sunday → excluded, not bonus.
- **`period_stats` matched hand calculations on every field**:
  - Week A: worked 2520, toward 2220, target 2400, bonus 300, o/u −180,
    completion **92.5%**, days_worked 7, counted 5, met 4, avg 360.0.
  - Week B: worked 1860, toward 1560, target 1680, bonus 300, o/u −120,
    completion **92.9%**, days_worked 6, counted 5, met 4, avg 310.0.
  - `worked == toward + bonus` in both.
- **Streak** `streak(06-16) = 4` — counts Tue, Mon, (Sun skip), Sat,
  (Fri holiday skip), Thu, then breaks on the Wed miss.
- **Comparison** week B vs A: diff −660 min, **−26.2%**, completion +0.4 pts,
  `has_prior=True`.
- **Trend** (2 weekly periods) oldest-first `[2520, 1860]`.
- **`month_stats(June)`** runs and stays internally consistent (decomposition
  holds); its lower completion reflects unworked required days outside the two
  weeks — correct behaviour.

## Outcome — Phase 3 done

`calc.py` (target resolution A1–A4, per-day bonus/over-under C1–C5) and `kpi.py`
(period totals, completion %, bonus totals D4, streak D3, trend, comparison D2,
empty-safe D1) compute correct analytics live from recorded data. The `sessions`
calc columns remain NULL by design ([[calc-live-compute]]).

## Next (Phase 4 preview)

`api/main.py` (FastAPI app, registry-driven router mounting) and
`worktime/routes.py` + core routes — exposing today/stats/kpi/sessions/calendar
and settings/day-type/target endpoints for the front-end.
