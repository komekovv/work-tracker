"use client";

import { cn } from "@/lib/utils";

export type SidePanelTab = "day" | "week" | "month" | "custom";

const TABS: { value: SidePanelTab; label: string }[] = [
  { value: "day", label: "Day" },
  { value: "week", label: "Week" },
  { value: "month", label: "Month" },
  { value: "custom", label: "Custom" },
];

export function SidePanelTabs({
  value,
  onChange,
}: {
  value: SidePanelTab;
  onChange: (tab: SidePanelTab) => void;
}) {
  return (
    <div className="inline-flex w-full rounded-md border border-border p-0.5">
      {TABS.map((t) => (
        <button
          key={t.value}
          onClick={() => onChange(t.value)}
          aria-pressed={value === t.value}
          className={cn(
            "flex-1 rounded px-2.5 py-1 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            value === t.value
              ? "bg-muted text-foreground"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
