# Debt / Hours-owed feature (post-release)

Adds a dashboard answer to the owner's recurring question — **"how many hours do I
still owe?"** — for this week, this month, or a custom date range: the net deficit
(or surplus), *why* it's short, how many work days are left, and the pace needed to
catch up.

Purely additive: no changes to `core/`, `api/main.py`, or any existing
schema/component. It reuses the live, read-only calc layer, so historical targets
and day-types are honored automatically.

---

## What "debt" means here

Debt = Σ (daily targets on **work days**) − hours actually worked, over a range.
Leave/vacation/holiday and Sundays carry **no target** (they become bonus, C1–C5),
so they're excluded from debt entirely; bonus never offsets debt (D4). This is
exactly `worked − target` on non-bonus days — which the KPI layer already computed
as `PeriodStats.over_under_minutes`. The feature builds on that rather than
reinventing it.

## Key decisions

1. **Today counts as "remaining", not debt.** The debt figure covers only
   *completed* days — `[start, as_of − 1]`. Today and future days feed the
   forward-looking projection. This avoids an in-progress day reading as a no-show
   at 9am, and means the number doesn't tick live. (Note this differs slightly from
   the month-to-date completion %, which includes today; debt intentionally stops at
   yesterday.)
2. **The "why short" breakdown reconciles.** Three signed buckets — *didn't come in*
   (no-show), *came in under target*, and *surplus credit* — that **sum exactly** to
   the net. Each counted day's `over_under_minutes` is `−target` (no-show),
   `worked−target` (under), or `+overage` (surplus); a day worked exactly to target
   lands in no bucket. So `no_show + under + surplus == over_under`.
3. **Remaining shows days + target-hours-left + catch-up rate.**
   `catch_up_per_day = outstanding_debt / remaining_work_days`;
   `avg_needed_per_day = (remaining_target + outstanding_debt) / remaining_work_days`.
   When no work days remain but debt is outstanding, the UI says it can't be cleared
   this period.
4. **A dedicated `/api/worktime/debt` endpoint** (period *or* from/to), leaving the
   shared `/stats` schema untouched.

## Pieces and how they fit

**Backend**

- `modules/worktime/kpi.py` — new `DebtStats` dataclass + `debt_stats(start, end,
  *, as_of=...)`. One pass over the completed range collects the totals and the three
  buckets; a second pass over the remaining range counts forward-looking work days
  and target minutes. Both passes go through `calc.compute_day`, so targets (A1–A4)
  and bonus days (C1–C5) resolve live. Empty/target-less ranges return zeros with
  `None` catch-up (D1) — no exceptions.
- `modules/worktime/schemas.py` — `DebtOut`, a `from_attributes` mirror of
  `DebtStats`.
- `modules/worktime/routes.py` — `GET /api/worktime/debt`. Resolves the range from
  `from`/`to` (422 if only one is given, or `from > to`) or from `period=week|month`
  around `as_of` (default today), then returns `debt_stats`. Uses the same single
  per-request connection pattern as `/stats`.

**Frontend** (all durations are minutes from the API; the UI formats hours, D5)

- `lib/types.ts` — `Debt` interface mirroring `DebtOut`.
- `lib/api.ts` — `getDebt({ period?, from?, to?, asOf? })`.
- `components/modules/worktime/debt-card.tsx` — new co-primary card with a
  This week / This month / Custom segmented toggle (custom reveals two date inputs
  and only fetches once both are set). Shows the signed headline (debt vs. ahead),
  the reconciling breakdown (rows render only when their bucket has days), and the
  remaining/catch-up line. Reuses `formatHM`/`formatSignedHM`, `Card`, `Input`,
  `Skeleton`, and the existing `text-target`/muted accent classes.
- `app/page.tsx` — `<DebtCard />` mounted directly under `<KpiCards />`, above the
  heatmap/trend row, so debt and growth/KPI sit at equal importance. It self-fetches
  (like `Heatmap`/`TrendChart`), so the page's existing wiring is unchanged.

## Cases covered (plan §8)

- **A1–A4** historical & per-weekday "short day" targets, and retroactive edits,
  reflect automatically (everything flows through `compute_day`/`resolve_target`).
- **C1–C5 / D4** Sunday/holiday/leave/vacation → target 0 → excluded from both debt
  and remaining; bonus never reduces debt.
- **B2/B4** midnight-crossing / multi-day sessions attributed to the start day
  (inherited from `calc._worked_minutes`).
- **D1** empty/target-less range → "nothing owed", no error. **D5** minutes in the
  API, hours in the UI.
- **Boundaries** a range spanning today splits at today; past-only range → no
  remaining; future-only range → debt 0, all remaining.

## Verification

- Backend math checked with a throwaway script against a temp `WORKTIME_DB_PATH`
  (seeded base 8h + Friday short 5h, a no-show/under/met/surplus week, a leave
  Saturday and worked Sunday): confirmed the three buckets reconcile to
  `over_under`, the completed/remaining split at `as_of`, the catch-up arithmetic,
  and the empty/future-range edge cases.
- API checked via the FastAPI app: `?period=month`, `?period=week`,
  `?from=&to=&as_of=` all 200; partial `from` and `from > to` correctly 422.
- Frontend: `npm run build` (type-checks the static export) passes.

## Applying (production)

Frontend → `cd frontend && npm run build` (API serves `out/` from disk; no restart
for static assets). Backend → `nssm restart WorkTrackerAPI`.
