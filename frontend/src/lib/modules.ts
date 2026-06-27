// Front-end module registry (mirrors the backend's open-closed design).
//
// Each entry adds a nav destination. A future module (notes, tasks, gitstreak)
// registers itself here — the header iterates this list, no header edits needed.
// Pages for "/worktime" and "/settings" arrive in Phase 6.

export interface NavModule {
  id: string;
  label: string;
  href: string;
}

export const modules: NavModule[] = [
  { id: "dashboard", label: "Dashboard", href: "/" },
  { id: "worktime", label: "Worktime", href: "/worktime" },
  { id: "settings", label: "Settings", href: "/settings" },
];
