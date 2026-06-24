"use client";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getCalendar } from "@/lib/api";
import { formatDate, formatHM } from "@/lib/format";
import type { DayResult } from "@/lib/types";
import { useApi } from "@/lib/use-api";

const WEEKDAYS = ["M", "T", "W", "T", "F", "S", "S"];

// Mon=0 … Sun=6 (matches the backend convention), from a 'YYYY-MM-DD' string.
function weekdayIndex(iso: string): number {
  const [y, m, d] = iso.split("-").map(Number);
  return (new Date(y, m - 1, d).getDay() + 6) % 7;
}

function cellStyle(day: DayResult): React.CSSProperties {
  if (day.is_bonus) return { backgroundColor: "var(--bonus)" };
  // No target required (Sunday/holiday/leave/vacation idle, or unset target).
  if (day.target_minutes === 0) {
    return day.day_type !== "workday"
      ? { backgroundColor: "var(--leave)", opacity: 0.4 } // marked day off
      : { backgroundColor: "var(--muted)" };
  }
  if (day.worked_minutes === 0) return { backgroundColor: "var(--muted)" };
  if (day.target_met) return { backgroundColor: "var(--target)" };
  // Under target: green scaled by how close it got.
  const ratio = Math.min(1, day.worked_minutes / day.target_minutes);
  return { backgroundColor: "var(--target)", opacity: 0.3 + 0.5 * ratio };
}

function LegendDot({ style, label }: { style: React.CSSProperties; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="h-3 w-3 rounded-sm" style={style} />
      {label}
    </span>
  );
}

export function Heatmap() {
  const { data, loading, error } = useApi(() => getCalendar());

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold">Daily activity</h2>
        {data && (
          <span className="text-xs text-muted-foreground">{data.month}</span>
        )}
      </div>

      {loading ? (
        <Skeleton className="mt-4 h-40 w-full" />
      ) : error || !data ? (
        <p className="mt-4 text-sm text-muted-foreground">
          {error ?? "No data"}
        </p>
      ) : (
        <>
          <div className="mt-4 grid grid-cols-7 gap-1">
            {WEEKDAYS.map((w, i) => (
              <div
                key={i}
                className="text-center text-[10px] font-medium text-muted-foreground"
              >
                {w}
              </div>
            ))}
            {/* leading blanks so the 1st lands under its weekday */}
            {Array.from({ length: weekdayIndex(data.days[0]?.date ?? "") }).map(
              (_, i) => (
                <div key={`pad-${i}`} />
              ),
            )}
            {data.days.map((day) => (
              <div
                key={day.date}
                title={`${formatDate(day.date)} — ${formatHM(day.worked_minutes)}${
                  day.target_minutes ? ` / ${formatHM(day.target_minutes)}` : " · bonus"
                }`}
                style={cellStyle(day)}
                className="aspect-square rounded-sm border border-border/40"
              />
            ))}
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-muted-foreground">
            <LegendDot style={{ backgroundColor: "var(--target)" }} label="met" />
            <LegendDot
              style={{ backgroundColor: "var(--target)", opacity: 0.45 }}
              label="under"
            />
            <LegendDot style={{ backgroundColor: "var(--bonus)" }} label="bonus" />
            <LegendDot
              style={{ backgroundColor: "var(--leave)", opacity: 0.4 }}
              label="leave"
            />
            <LegendDot style={{ backgroundColor: "var(--muted)" }} label="none" />
          </div>
        </>
      )}
    </Card>
  );
}
