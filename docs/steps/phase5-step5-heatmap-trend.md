# Phase 5 · Step 5 — Heatmap + trend chart

**Status:** Done
**Goal:** Add the daily heatmap and the weekly trend chart (Recharts) to the
dashboard, completing the Phase 5 main view.

## What was implemented

- **`src/components/modules/worktime/heatmap.tsx`** — calendar-style month grid
  (self-fetches `getCalendar`). 7 columns (Mon→Sun), leading blanks so the 1st
  lands under its weekday. Cell color (semantic tokens, inline styles):
  met → `--target`; under → `--target` scaled by ratio; bonus → `--bonus`;
  marked day-off → faint `--leave`; nothing → `--muted`. Per-cell `title`
  tooltip (date — worked / target); legend.
- **`src/components/modules/worktime/trend-chart.tsx`** — Recharts
  `ComposedChart` (self-fetches `getStats("week", n=8)`): worked-hours bars +
  dashed target line, theme-aware colors via CSS vars, custom tooltip. A
  `mounted` guard defers render to the client so the static-export prerender
  doesn't size an empty container.
- **`src/app/page.tsx`** — heatmap + trend added below the KPI cards in a
  responsive 2-column grid.
- **Dependency:** `recharts` 3.9.0 (installed by the user; React 19 compatible).

## Key decisions

- **Hand-rolled heatmap, Recharts only for the line/bar chart** — the heatmap is
  a simple grid; a chart lib would be overkill and harder to theme.
- **CSS-variable colors in the chart** (`var(--target)` etc.) so it re-themes
  with light/dark automatically.
- **`mounted` guard** instead of `next/dynamic ssr:false` — simplest way to keep
  Recharts off the prerender path under `output: export`.
- **Locale-safe labels** — week labels use `toLocaleDateString({month, day})`
  (no fragile weekday-strip regex; fixed a label bug found in verification).

## Verification

- `npm run build` → compiles, TypeScript passes, static export OK (one Recharts
  formatter type fix + one label fix along the way).
- **Live, real data** (backend `:8000` seeded June 2026, dev `:3000`, via
  `read_page`):
  - Heatmap rendered all 30 day cells with correct tooltips (e.g. `Mon 15 Jun —
    8h / 8h`, `Thu 18 Jun — 3h · bonus`, `Sun 7 Jun — 2h · bonus`) + legend.
  - Trend chart rendered 8 weekly points with clean axis labels
    (`4 May … 22 Jun`).

> Visual screenshots still unavailable (Chrome extension not connected);
> verified via the accessibility tree, which reflects the rendered values.

## Phase 5 — Done

Static-export Next.js app: theme system, typed API client, app shell, and a
working KPI dashboard (today + 4 KPI cards + heatmap + weekly trend) showing
real backend data. Open question on month-to-date completion still pending
([[open-question-month-completion]]).

## Next (Phase 6 preview)

Front-end calendar + settings pages: monthly calendar with session editing,
manual add, target/holiday settings, responsive polish; add `/worktime` +
`/settings` to the module registry.
