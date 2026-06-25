# Phase 6 · Step 5 — General settings page

**Status:** Done
**Goal:** Theme control (light/dark/system) and a dynamic-settings editor.

## What was implemented

### Theme system extended (`components/ui/theme-provider.tsx`)
- Now tracks a **preference** (`light` / `dark` / `system`) plus the **resolved**
  theme. `system` follows `prefers-color-scheme` and updates live on OS change.
- `setPreference`, `toggle` (flips resolved light↔dark), persisted to
  `localStorage`. `NO_FLASH_SCRIPT` updated to honour explicit light/dark and
  fall back to OS for `system`/unset.
- `theme-toggle.tsx` updated to use `resolved`.

### New components
- **`components/settings/theme-control.tsx`** — segmented Light/Dark/System
  control bound to the provider.
- **`components/settings/general-settings.tsx`** — fetches `getSettings`, renders
  an editable field per key (a Select for `week_start_day`, Input otherwise),
  saves all via `updateSettings`, shows "Saved.". Hides `theme` (controlled
  client-side by the Theme card).
- **`app/settings/page.tsx`** — composes both.

## Key decisions

- **Theme preference lives in `localStorage`, not the backend `theme` setting.**
  Instant, no fetch, no flash. The backend `theme` row is therefore hidden from
  the dynamic editor to avoid a dead/confusing field.
- **`system` mode** added (the plan's "prefers-color-scheme + manual toggle"),
  with a live OS-change listener.
- **`week_start_day` gets a Select** (the one setting with a known enum); other
  settings stay free-text key/value, keeping the editor generic and future-proof.
- **One Save for all settings** (bulk `updateSettings`), matching the backend's
  bulk upsert.

## Verification (live)

- `/settings` rendered the Theme control and the dynamic editor
  (`week_start_day` select = Monday, `worktime.heartbeat_seconds` input);
  `theme` hidden.
- Clicking **Dark** applied dark mode — the header toggle label flipped to
  "Switch to light theme" (theme control and header toggle share the provider).
- Clicking **Save settings** showed **"Saved."** (the `updateSettings` POST
  succeeded).
- `npm run build` passes.

## Next

Step 6 — Responsive polish (mobile nav, reflowing grids, touch targets) + a
final cross-page smoke pass to close Phase 6.
