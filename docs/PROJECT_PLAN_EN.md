# Work-Time & KPI Tracker — Project Plan

> This plan is written for Claude Code. It is high-level (phases + goals), not file-by-file.
> Claude Code fills in the per-file detail; this document provides direction, principles,
> and order. **Execute phase by phase, not all at once** — verify each phase before moving on.

---

## 1. Goal & Purpose

A personal work dashboard: automatically tracks daily work hours based on when the computer
is turned on/off, and surfaces personal KPIs / work growth over time. Single user (the owner),
runs locally.

**Core requirements:**
- Computer power-on = session start, power-off = session end. Multiple sessions per day are supported.
- Closed (powered-off) periods are NOT counted — only the sum of open sessions.
- Dynamic targets: daily/weekly/monthly, with per-weekday overrides ("short days"), changeable over time (historical).
- Bonus: on Sundays or holidays that are worked, **all hours** count as bonus.
- Day types: workday, leave, vacation, holiday — settable both manually and in advance (calendar).
- KPI / growth: target completion %, weekly/monthly trend, streak, bonus totals, period-over-period comparison.
- Extensible: adding future modules (notes, tasks, git streak/commits) must be easy — without touching core code.
- Settings must be changeable without touching code (everything stored in DB).

---

## 2. Tech Stack (June 2026 — latest stable versions)

**Backend**
- Python 3.12 (3.13 also fine)
- FastAPI `>=0.136.1,<0.137.0` (0.x semver — pinned range is mandatory, minor releases may break)
- Uvicorn (comes with FastAPI[standard])
- SQLite (Python built-in `sqlite3` — single file, ideal)
- Pydantic v2 (comes with FastAPI)

**Front-end**
- Next.js 16 (latest stable 16.2.x; requires Node.js 20+)
- React 19
- TypeScript
- `src/` folder structure (keeps root clean)
- `output: 'export'` — static export (no server-side needed, all logic lives in backend)
- Tailwind CSS (styling)
- Recharts or Chart.js (charts)

**Service / runtime**
- NSSM — run the detector and the API as Windows services
- Next.js: built statically and served by FastAPI itself (no separate process — the "simplest" path)

---

## 3. Architecture: Modular Monolith

One application (simple deploy), internally split into independent modules. Adding a future
module = adding a new folder, without touching old code (open-closed principle).

```
backend/
├── core/                  # shared core — used by all modules
│   ├── db.py              # SQLite connection, migrations, shared helpers
│   ├── config.py          # read settings (from DB, dynamic)
│   ├── registry.py        # module registration system (routes + tables)
│   ├── day_types.py       # shared day-type logic (leave/vacation/holiday)
│   └── calendar.py        # shared date/calendar helpers
│
├── modules/
│   └── worktime/          # ← FIRST (and currently only) MODULE
│       ├── detector.py    # NSSM service: boot/heartbeat/shutdown, orphan recovery
│       ├── models.py      # sessions, targets tables + schema
│       ├── calc.py        # target, bonus, over/under calculations
│       ├── kpi.py         # trend, comparison, streak, % — analytics
│       └── routes.py      # /api/worktime/... endpoints
│
├── api/
│   └── main.py            # FastAPI app — wires modules automatically via registry
├── requirements.txt
└── data/
    └── app.db             # SQLite (shared by detector + API)

frontend/
├── public/                # static files (stays at root, outside src)
├── next.config.js         # output: 'export'
├── tsconfig.json
├── package.json
└── src/
    ├── app/
    │   ├── page.tsx        # KPI dashboard (main page)
    │   ├── worktime/
    │   │   ├── page.tsx    # calendar + session list
    │   │   └── settings/page.tsx   # target, holiday settings
    │   └── settings/page.tsx       # general settings
    ├── lib/
    │   ├── api.ts          # functions that call the backend API
    │   └── modules.ts      # module registry (easy to add new module UI)
    └── components/
        ├── ui/             # shared components (card, button, theme toggle)
        └── modules/
            └── worktime/   # KPI cards, heatmap, trend chart
```

**Registry principle:** each module registers itself (routes, tables). `api/main.py` only
iterates modules and wires them. Adding a new module must NOT require editing `main.py`.

**What core shares:** day types (leave/vacation — affect all modules), settings (dynamic
key-value), calendar/date system.

---

## 4. Data Model (SQLite tables)

> Migration: `CREATE TABLE IF NOT EXISTS` + seed. Each table belongs to its module/core.

**core**
- `settings` — key-value dynamic settings (for changing config without touching code)
- `day_types` — `date` (UNIQUE), `type` ('workday'|'holiday'|'leave'|'vacation'), `name`, `planned` (1=in advance, 0=manual), `affects_target`

**worktime module**
- `sessions` — `id`, `date`, `start_time`, `end_time`, `duration_minutes`, `daily_target_hours`, `is_sunday`, `is_holiday`, `is_bonus`, `last_heartbeat`, `source` ('auto'|'manual'|'crash-recovered')
- `targets` — `id`, `effective_from` (date), `period` ('daily'|'weekly'), `weekday` (0–6 for a specific day, NULL=all days), `daily_hours` — **historical** (change without affecting past days), supports per-weekday targets (short days)

> Future modules (tasks, notes, gitstreak) add their own tables themselves — out of scope for this plan.

---

## 5. Core Logic Principles

**Detector (worktime/detector.py)**
- Boot: `init_db` → recover orphan sessions → open new session
- Loop: write `last_heartbeat` every ~60 seconds
- Shutdown (SIGTERM/SIGINT/atexit): close the open session (use a flag to prevent double-close)
- **Orphan recovery (important):** on crash/power-loss SIGTERM does not arrive. On next boot,
  find sessions with `end_time IS NULL` and set `end_time` = **last heartbeat** (NOT current time),
  `source='crash-recovered'`. This caps error at ~1 minute.

**Calculation (worktime/calc.py)**
- Day type is read from `day_types`
- `vacation`/`leave` → target requirement 0, excluded from completion. **BUT if worked that day
  (a session exists) → all hours count as bonus** (see cases below)
- `holiday`/Sunday + worked → **all hours = bonus**, target 0
- normal day → target read from `targets` (historical, per-weekday)
- over/under = worked − target (target 0 on bonus days)

**KPI (worktime/kpi.py)**
- Target completion % (per period)
- Weekly/monthly totals and trend
- Period-over-period comparison (this month vs last month: +/− hours, % change)
- Streak (consecutive days target met)
- Bonus hour totals
- Average daily hours

---

## 6. API Endpoints (worktime module)

> All under `/api/worktime/` prefix. Registry wires them automatically.

- `GET  /api/worktime/today` — today's status
- `GET  /api/worktime/stats?period=week|month` — totals + trend
- `GET  /api/worktime/kpi` — KPI metrics (%, streak, comparison, bonus)
- `GET  /api/worktime/sessions?from=&to=` — session list
- `GET  /api/worktime/calendar?month=` — calendar (day type + color info)
- `POST /api/worktime/sessions/manual` — manual session (clock-in/out)
- `PATCH /api/worktime/sessions/{id}` — edit session (fix a crash day)
- `POST /api/day-type` — set day type (core: leave/vacation/holiday)
- `DELETE /api/day-type/{date}` — remove a day-type marking
- `POST /api/worktime/target` — change target (with `effective_from`, `weekday`)
- `GET/POST /api/settings` — dynamic settings

---

## 7. Front-end (Next.js, src/, static)

**Design direction:** hybrid — calm calendar-heatmap (core) + clear KPI cards.
Dark/light theme toggle (`prefers-color-scheme` + manual toggle). Color carries meaning:
green tones = target (light=under, dark=met), blue = bonus, gray = leave/vacation.
Primary focus on desktop, but fully responsive (mobile: tab bar / hamburger, touch-friendly,
KPI cards auto-fit grid, heatmap cells shrink via `aspect-ratio`).
Quality bar: visible keyboard focus, reduced-motion respected.

**Pages / components:**
- Dashboard (main): KPI cards (month total, target %, streak, bonus) + daily heatmap + weekly trend (with target reference line)
- Worktime page: monthly calendar (each day colored, click to open sessions), session list, manual add/edit
- Worktime settings: target pattern (daily/weekly, short days, historical), add holidays
- General settings: theme, dynamic settings
- Module registry (`lib/modules.ts`): future module card/page is easy to add

---

## 8. Cases / Scenarios — Claude Code MUST handle these

> This is one of the most important sections. Each case must be handled explicitly,
> otherwise edge cases will behave incorrectly.

### A. Target / work-time changes
- **A1.** Last month 5h/day, this month 9h/day → new target applies only to days **on/after**
  `effective_from`. Past days' calculations don't change (historical data preserved).
- **A2.** "Short day" — a specific weekday (e.g. Friday) is 5h, other days 9h → in `targets`
  use `weekday` for that day's override. NULL `weekday` = base target for all days.
- **A3.** Target edited retroactively (effective from an earlier date) → only days on/after
  that date are recomputed; KPI/trend refreshes.
- **A4.** If multiple target rules match a day (base + weekday) → the more specific (weekday) rule wins.

### B. Session / detector
- **B1.** Turning on/off 2-3 times in one day → each power-on is a separate session (row).
  Daily total = sum of `duration_minutes` of all that day's sessions.
- **B2.** Session crossing midnight (on at 23:00, off at 01:00) → the whole session belongs to
  the **start day** (not split — chosen decision for simplicity).
- **B3.** Crash / power-loss → no SIGTERM, session stays `end_time IS NULL`. On next boot the
  orphan is found, `end_time` = **last heartbeat** (NOT current time), `source='crash-recovered'`.
  Error capped at ~1 min.
- **B4.** Computer left on for several days (very long session) → kept as one session; when KPI
  splits by day it may distribute by heartbeats or attribute to start day (Claude Code: pick the
  simplest — attribute to start day).
- **B5.** Heartbeat interrupted mid-session (PC sleeps then wakes) → sleep period stays as open
  session; if gap between last heartbeat and wake is large it could be marked "open but not worked"
  (for now: keep it simple, count as open).
- **B6.** Two sessions overlapping in time (from a manual-entry mistake) → API should warn or reject.

### C. Day types
- **C1.** Worked on a holiday → all hours bonus, target 0.
- **C2.** Computer turned on and worked on a leave/vacation day → **all hours bonus** (like
  Sunday/holiday). No target required.
- **C3.** Leave set manually but a session also exists → treat like C2 (bonus); day type is kept,
  but worked hours add to bonus.
- **C4.** Pre-planned holiday (`planned=1`) vs manually set (`planned=0`) conflict → the manual
  one wins (the user is the final decision-maker).
- **C5.** A day that is both Sunday and holiday → bonus counted once (no double counting).

### D. KPI / calculation
- **D1.** A month with no data (fresh start) → KPI shows "no data", 0 or "—", does not error.
- **D2.** No prior period to compare against (first month) → trend/comparison shows "no prior
  period", does not crash.
- **D3.** Streak breaking → if a day misses target (and is not leave/vacation), streak resets to 0.
  Leave/vacation days do not break the streak (they are skipped over).
- **D4.** Bonus hours are NOT added to regular target completion — they are totaled separately.
- **D5.** Fractional hours (e.g. 4.5h) → stored in minutes, rounded when displayed (to avoid float artifacts).

---

## 9. Build Order (phases for Claude Code)

**Phase 1 — Core**
Goal: DB connection, migration system, settings, day_types, registry, calendar helper.
Result: empty but working core, ready to accept modules.

**Phase 2 — Worktime module: detector + data**
Goal: detector.py (boot/heartbeat/shutdown/orphan recovery), models.py (sessions, targets), real DB writes.
Result: sessions are written to DB when the computer powers on/off.

**Phase 3 — Worktime module: calculation + KPI**
Goal: calc.py (target, bonus, over/under), kpi.py (trend, streak, comparison).
Result: KPI computed from recorded data.

**Phase 4 — API**
Goal: FastAPI app, registry wiring, worktime + core endpoints.
Result: working API the front-end can call.

**Phase 5 — Front-end: core + dashboard**
Goal: Next.js (src/, static export), api.ts, theme system, KPI dashboard (cards + heatmap + trend).
Result: main dashboard works and shows real data.

**Phase 6 — Front-end: calendar + settings**
Goal: worktime calendar page, session editing, target/holiday settings, responsive polish.
Result: full interface, manual control.

**Phase 7 — NSSM setup + integration**
Goal: detector service, API service, serve Next.js static build, setup instructions (README).
Result: everything runs automatically when the computer starts.

---

## 10. Important Technical Notes (Claude Code take care)

- FastAPI 0.x — pin the version in a narrow range (`>=0.136.1,<0.137.0`).
- Next.js 16: Turbopack is default, Node.js 20+; static export has no SSR/API routes — all logic in backend.
- With Next.js `src/`, `public/` stays at root.
- SQLite is opened by both detector and API — use `WAL` mode + timeout to avoid write contention.
- In orphan recovery, use the **last heartbeat**, not current time.
- Targets and day types are historical/dynamic — must not alter past calculations.
- Round numbers in the UI (avoid float artifacts).
- Keep modularity strict: nothing belonging to a non-worktime module should leak into core or worktime.
