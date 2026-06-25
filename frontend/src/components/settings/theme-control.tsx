"use client";

import { Card } from "@/components/ui/card";
import { useTheme } from "@/components/ui/theme-provider";
import { cn } from "@/lib/utils";

const OPTIONS = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "system", label: "System" },
] as const;

export function ThemeControl() {
  const { preference, setPreference } = useTheme();

  return (
    <Card className="p-6">
      <h2 className="text-base font-semibold">Theme</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Choose light, dark, or follow your system.
      </p>
      <div className="mt-4 inline-flex rounded-lg border border-border p-1">
        {OPTIONS.map((o) => (
          <button
            key={o.value}
            type="button"
            onClick={() => setPreference(o.value)}
            aria-pressed={preference === o.value}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              preference === o.value
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {o.label}
          </button>
        ))}
      </div>
    </Card>
  );
}
