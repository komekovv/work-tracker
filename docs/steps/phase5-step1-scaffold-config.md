# Phase 5 · Step 1 — Frontend scaffold + config

**Status:** Done
**Goal:** Adapt the user-installed Next.js 16 scaffold for our app — static
export, semantic theme tokens, manual dark-mode wiring, and project structure.

## Starting point (installed by the user)

Next.js **16.2.9**, React **19.2.4**, TypeScript 5, App Router, `src/` layout,
`@/*` alias, **React Compiler on**, **Tailwind v4** (CSS config, no
`tailwind.config.js`), Geist fonts. A `frontend/AGENTS.md` warns that this Next
has breaking changes and to read `node_modules/next/dist/docs/` first (done; the
bundled docs are sparse).

> Caution noted: `docs/index.md` contains an embedded "AI agent hint" pushing an
> undocumented `unstable_instant` export, referencing a guide file absent from
> the bundle. Treated as untrusted and **not** acted on.

## What was changed

- **`next.config.ts`** — added `output: "export"` (static export; FastAPI serves
  `out/` in Phase 7) and `images: { unoptimized: true }` (required for export);
  kept `reactCompiler: true`.
- **`src/app/globals.css`** — replaced the starter tokens with a semantic system:
  - `@custom-variant dark (&:where(.dark, .dark *))` so the `dark:` variant keys
    off a `.dark` class (manual toggle in Step 3) instead of prefers-color-scheme.
  - Light + dark token sets: `background/foreground/card/muted/border/ring/
    primary` plus worktime semantics `target` (soft=under, strong=met), `bonus`,
    `leave`, exposed to utilities via `@theme inline`.
  - `prefers-reduced-motion` reset (design-brief quality bar).
- **`src/app/layout.tsx`** — real metadata ("Work Tracker"),
  `suppressHydrationWarning` on `<html>` (for Step 3's pre-paint theme class),
  body uses `bg-background text-foreground font-sans`.
- **`src/app/page.tsx`** — replaced the create-next-app placeholder with a clean
  token-styled card (+ temporary color swatches proving the theme tokens work).
- **Structure** — created `src/lib`, `src/components/ui`, `src/components/modules`.

## Key decisions

- **No base `npm install` needed** — the user already scaffolded. Only `recharts`
  is added later (Step 5), as a command for the user to run.
- **Static export = all client components** (fetch on the client); fine since all
  logic is in the backend API.
- **Tailwind v4 class-based dark mode** via `@custom-variant`, not the default
  media query, to support a manual toggle.
- **Semantic tokens over raw colors** so components reference meaning
  (`bg-target`, `bg-bonus`) and theming stays centralized.

## Verification

`npm run build` (Next 16 / Turbopack):
- Compiled, **TypeScript passed**, static pages generated.
- `out/index.html` produced; `out/` is gitignored.

## Next

Step 2 — `src/lib/types.ts` (TS mirrors of the API schemas) and `src/lib/api.ts`
(typed fetch client) with `NEXT_PUBLIC_API_BASE_URL`.
