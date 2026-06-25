# Phase 6 · Step 6 — Responsive polish + verification

**Status:** Done
**Goal:** Mobile navigation and responsive layout, then a final cross-page pass
to close Phase 6.

## What was implemented

- **`src/components/mobile-tab-bar.tsx`** — a fixed bottom tab bar (`sm:hidden`)
  with icon + label links for Dashboard / Worktime / Settings, active state via
  `usePathname`, inset focus rings.
- **`header.tsx`** — inline nav now `hidden ... sm:flex` (hidden on mobile, where
  the tab bar takes over).
- **`layout.tsx`** — renders `<MobileTabBar />`; content container gets
  `pb-24 sm:pb-6` so it clears the bottom bar on mobile.

## Existing responsiveness (already in place from earlier steps)

- KPI cards: `sm:grid-cols-2 lg:grid-cols-4`; heatmap/trend `lg:grid-cols-2`.
- Calendar: `lg:grid-cols-[1fr_20rem]` (stacks on mobile); day cells use
  `aspect-square` so they shrink cleanly.
- Settings/forms: `sm:grid-cols-*` that collapse to a single column on mobile.
- Header wraps; reduced-motion + focus rings handled globally (Phase 5 Step 1).

## Key decisions

- **Bottom tab bar over a hamburger** — only three destinations, and a tab bar is
  more touch-friendly and discoverable than a hidden menu.
- **Pure CSS breakpoints** (`sm:hidden` / `hidden sm:flex`) — no JS viewport
  detection, so it works under static export with no hydration cost.

## Verification

- `npm run build` passes.
- **Responsive markup confirmed in built `out/index.html`:** the tab bar
  (`fixed ... bottom-0 ... sm:hidden`) and the header nav (`hidden ... sm:flex`)
  are both present — below 640px the tab bar shows and the inline nav hides;
  above, vice-versa. (A live mobile-width screenshot was inconclusive — the
  window resize didn't shrink the rendered viewport — so this was verified from
  the output markup instead.)
- **Cross-page smoke:** `/`, `/worktime`, `/worktime/settings`, `/settings` all
  return 200; the backend endpoints the pages call (`kpi`, `today`, `calendar`,
  `targets`, `settings`, `day-types`) all return 200.
- Dashboard still renders all four KPI cards after the layout change (no
  regression).

## Phase 6 — Done

Full interface: monthly calendar with a day panel, manual session add/edit (with
overlap handling), target + holiday management, general settings + theme, and a
responsive shell with mobile navigation.

## Next

Discuss the parked open question — month completion: whole calendar month vs
month-to-date ([[open-question-month-completion]]) — then Phase 7 (NSSM services
+ serving the static build).
