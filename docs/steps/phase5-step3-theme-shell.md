# Phase 5 · Step 3 — Theme system + UI primitives + app shell

**Status:** Done
**Goal:** A dark/light theme with no flash, base UI components, the app-shell
header, and the front-end module registry.

## What was implemented

- **`src/lib/modules.ts`** — `NavModule` type + `modules` array (front-end
  registry; future modules add a nav entry, header iterates it). Currently
  `Dashboard`; `/worktime` + `/settings` join in Phase 6.
- **`src/lib/utils.ts`** — `cn()` className joiner (no clsx dep).
- **`src/components/ui/theme-provider.tsx`** — `ThemeProvider` (context;
  resolves light/dark, persists to `localStorage`, toggles the `.dark` class),
  `useTheme()`, and `NO_FLASH_SCRIPT` (inline pre-paint theme setter).
- **`src/components/ui/theme-toggle.tsx`** — accessible sun/moon toggle button
  (aria-label reflects the action, focus ring).
- **`src/components/ui/{card,button,skeleton}.tsx`** — base primitives using the
  semantic tokens (Button variants: primary/outline/ghost).
- **`src/components/header.tsx`** — sticky, blurred header: logo mark, nav (from
  `modules`, active state via `usePathname`), theme toggle.
- **`layout.tsx`** — injects `NO_FLASH_SCRIPT`, wraps content in
  `ThemeProvider` + `Header` + a max-width container.
- **`page.tsx`** — dashboard placeholder inside the shell.

## Key decisions

- **No-flash via inline script** in the layout: sets `.dark` from
  `localStorage` (fallback OS preference) **before paint**; `ThemeProvider`'s
  effect then syncs React state. `<html suppressHydrationWarning>` covers the
  intentional class mismatch.
- **Class-based dark mode** (Tailwind v4 `@custom-variant`, Step 1) so the
  toggle is a real manual override, not just OS-driven.
- **Semantic tokens, not raw colors** — components reference `bg-card`,
  `bg-target`, `text-muted-foreground`, etc., so theming stays centralized.
- **Accessibility** — visible `focus-visible` rings on all interactive elements,
  aria-labels on the icon button, reduced-motion handled globally (Step 1).
- **Module registry mirrors the backend** — nav is data-driven; adding a module
  is one array entry, no header edits.

## Verification

- `npm run build` → compiles, TypeScript passes, static export OK.
- Prerendered `out/index.html` contains the no-flash script, header, dashboard
  heading, and semantic token classes.
- **Live DOM (dev server + `read_page`)**: header rendered the logo link,
  `Dashboard` nav, and the theme toggle; the toggle label read "Switch to light
  theme", i.e. the no-flash script applied **dark** mode from the OS preference.

> Note: image screenshots require the Claude Chrome extension to be connected;
> it wasn't during this step, so no visual was captured. Structure was verified
> via the accessibility tree instead.

## Next

Step 4 — Dashboard KPI cards: fetch `kpi`/`stats`/`today`, render the cards
(month total, target %, streak, bonus) with loading + empty states (D1).
