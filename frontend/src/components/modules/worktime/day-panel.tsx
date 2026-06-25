"use client";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  formatDate,
  formatHM,
  formatSignedHM,
  formatTime,
} from "@/lib/format";
import type { DayResult, SessionOut } from "@/lib/types";

const DAY_TYPE_LABEL: Record<string, string> = {
  holiday: "Holiday",
  leave: "Leave",
  vacation: "Vacation",
};

export function DayPanel({
  day,
  sessions,
  onEdit,
}: {
  day: DayResult | null;
  sessions: SessionOut[];
  onEdit: (session: SessionOut) => void;
}) {
  if (!day) {
    return (
      <Card className="p-5 text-sm text-muted-foreground">
        Select a day to see its sessions.
      </Card>
    );
  }

  const marked = day.day_type !== "workday";

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold">{formatDate(day.date)}</h2>
        {marked && (
          <Badge tone={day.is_bonus ? "bonus" : "leave"}>
            {DAY_TYPE_LABEL[day.day_type] ?? day.day_type}
          </Badge>
        )}
        {!marked && day.is_sunday && <Badge tone="bonus">Sunday</Badge>}
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-y-2 text-sm">
        <dt className="text-muted-foreground">Worked</dt>
        <dd className="text-right tabular-nums">
          {formatHM(day.worked_minutes)}
        </dd>
        {day.target_minutes > 0 ? (
          <>
            <dt className="text-muted-foreground">Target</dt>
            <dd className="text-right tabular-nums">
              {formatHM(day.target_minutes)}
            </dd>
            <dt className="text-muted-foreground">Over / under</dt>
            <dd className="text-right tabular-nums">
              {formatSignedHM(day.over_under_minutes)}
            </dd>
          </>
        ) : (
          <>
            <dt className="text-muted-foreground">Bonus</dt>
            <dd className="text-right tabular-nums text-bonus">
              {formatHM(day.bonus_minutes)}
            </dd>
          </>
        )}
      </dl>

      <div className="mt-5">
        <h3 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Sessions
        </h3>
        {sessions.length === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">No sessions.</p>
        ) : (
          <ul className="mt-2 space-y-2">
            {sessions.map((s) => (
              <li
                key={s.id}
                className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm"
              >
                <span className="tabular-nums">
                  {formatTime(s.start_time)}
                  {" – "}
                  {s.end_time ? formatTime(s.end_time) : "open"}
                </span>
                <span className="flex items-center gap-2">
                  {s.duration_minutes !== null && (
                    <span className="tabular-nums text-muted-foreground">
                      {formatHM(s.duration_minutes)}
                    </span>
                  )}
                  <Badge>{s.source}</Badge>
                  <button
                    type="button"
                    onClick={() => onEdit(s)}
                    aria-label={`Edit session ${formatTime(s.start_time)}`}
                    className="rounded p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M12 20h9" />
                      <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
                    </svg>
                  </button>
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Card>
  );
}
