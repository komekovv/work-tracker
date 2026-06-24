# Phase 6 · Step 1 — Routing, nav, form primitives

**Status:** Done
**Goal:** Add the calendar/settings routes to the nav and build the form UI
primitives the next steps need.

## What was implemented

- **`src/lib/modules.ts`** — added `Worktime` (`/worktime`) and `Settings`
  (`/settings`) to the nav registry.
- **`src/components/header.tsx`** — active-state now uses `startsWith` for
  non-root hrefs, so `/worktime/settings` keeps "Worktime" highlighted.
- **Form primitives** (`src/components/ui/`):
  - `input.tsx`, `select.tsx`, `label.tsx` — token-styled with focus rings.
  - `badge.tsx` — pill with tones (default/target/bonus/leave) for day-type tags.
  - `modal.tsx` — accessible dialog (`role="dialog" aria-modal`, Escape to close,
    backdrop click, focuses the panel on open).
- **Page shells**:
  - `app/worktime/page.tsx` — Worktime heading + link to targets/holidays.
  - `app/worktime/settings/page.tsx` — "Targets & holidays" shell with back link.
  - `app/settings/page.tsx` — general Settings shell.

## Key decisions

- **`startsWith` active logic** so a parent nav item stays active on its
  sub-routes (root `/` stays exact-match).
- **Native form elements styled with tokens** (Input/Select) — no form library;
  lightweight and accessible by default.
- **Custom Modal, not native `<dialog>`** — full control over styling/animation;
  Escape + backdrop close + initial focus. (Full focus-trap polish is Step 6.)
- **Worktime settings under `/worktime/settings`** (linked from the worktime
  page), keeping the top nav to three items.

## Verification

- `npm run build` → compiles, TypeScript passes; routes `/`, `/settings`,
  `/worktime`, `/worktime/settings` all prerender as static.
- **Live (`read_page`)**: header shows Dashboard/Worktime/Settings; `/worktime`
  renders its shell + the "Targets & holidays" link; client-side nav works.

No new dependencies.

## Next

Step 2 — Worktime calendar page: monthly grid (colored days, day-type badges),
month navigation, and a day panel showing that day's sessions.
