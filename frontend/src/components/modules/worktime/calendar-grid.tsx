"use client";

import type { Calendar, DayResult } from "@/lib/types";
import { formatDate, formatHM, formatHours } from "@/lib/format";
import { cn } from "@/lib/utils";

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

// Mon=0 … Sun=6 from a 'YYYY-MM-DD' string.
function weekdayIndex(iso: string): number {
  const [y, m, d] = iso.split("-").map(Number);
  return (new Date(y, m - 1, d).getDay() + 6) % 7;
}

type Tone = { bg: string; dot: string };

function tone(day: DayResult): Tone | null {
  if (day.is_bonus) return { bg: "bg-bonus/10", dot: "bg-bonus" };
  if (day.target_minutes === 0) {
    return day.day_type !== "workday"
      ? { bg: "bg-leave/10", dot: "bg-leave" }
      : null;
  }
  if (day.worked_minutes === 0) return null;
  if (day.target_met) return { bg: "bg-target/15", dot: "bg-target" };
  return { bg: "bg-target/8", dot: "bg-target/60" };
}

export function CalendarGrid({
  calendar,
  selected,
  today,
  onSelect,
}: {
  calendar: Calendar;
  selected: string | null;
  today: string;
  onSelect: (date: string) => void;
}) {
  const lead = calendar.days.length ? weekdayIndex(calendar.days[0].date) : 0;

  return (
    <div>
      <div className="grid grid-cols-7 gap-1.5">
        {WEEKDAYS.map((w) => (
          <div
            key={w}
            className="pb-1 text-center text-xs font-medium text-muted-foreground"
          >
            {w}
          </div>
        ))}

        {Array.from({ length: lead }).map((_, i) => (
          <div key={`pad-${i}`} />
        ))}

        {calendar.days.map((day) => {
          const t = tone(day);
          const dayNum = Number(day.date.slice(-2));
          const isSelected = day.date === selected;
          const isToday = day.date === today;
          return (
            <button
              key={day.date}
              type="button"
              onClick={() => onSelect(day.date)}
              aria-pressed={isSelected}
              aria-label={`${formatDate(day.date)}, worked ${formatHM(
                day.worked_minutes,
              )}${day.target_minutes ? ` of ${formatHM(day.target_minutes)}` : ""}`}
              className={cn(
                "flex aspect-square flex-col items-start justify-between rounded-lg border p-1.5 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                t?.bg ?? "bg-transparent",
                isSelected
                  ? "border-primary ring-1 ring-primary"
                  : "border-border hover:border-muted-foreground/40",
              )}
            >
              <span
                className={cn(
                  "text-xs tabular-nums",
                  isToday
                    ? "flex h-5 w-5 items-center justify-center rounded-full bg-primary font-semibold text-primary-foreground"
                    : "text-foreground",
                )}
              >
                {dayNum}
              </span>
              <span className="flex w-full items-center justify-between">
                {day.worked_minutes > 0 ? (
                  <span className="text-[10px] tabular-nums text-muted-foreground">
                    {formatHours(day.worked_minutes)}
                  </span>
                ) : (
                  <span />
                )}
                {t && (
                  <span className={cn("h-1.5 w-1.5 rounded-full", t.dot)} />
                )}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
