import { Card } from "@/components/ui/card";
import type { Today } from "@/lib/types";
import { formatDate, formatHM, formatSignedHM } from "@/lib/format";

export function TodayCard({ today }: { today: Today }) {
  const isBonusDay = today.target_minutes === 0;
  const pct = isBonusDay
    ? null
    : Math.min(
        100,
        Math.round((today.worked_minutes_live / today.target_minutes) * 100),
      );

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Today · {formatDate(today.date)}
          </div>
          <div className="mt-1 text-2xl font-semibold tabular-nums">
            {formatHM(today.worked_minutes_live)}
            <span className="ml-1 text-base font-normal text-muted-foreground">
              {isBonusDay ? "· bonus day" : `/ ${formatHM(today.target_minutes)}`}
            </span>
          </div>
        </div>

        {today.active_session && (
          <span className="flex items-center gap-1.5 rounded-full bg-target/10 px-2.5 py-1 text-xs font-medium text-target">
            <span className="h-2 w-2 animate-pulse rounded-full bg-target" />
            Working
          </span>
        )}
      </div>

      {pct !== null && (
        <>
          <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-target transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>
          <div className="mt-1.5 text-xs text-muted-foreground">
            {pct}% of target ·{" "}
            {formatSignedHM(today.worked_minutes_live - today.target_minutes)}
          </div>
        </>
      )}

      {isBonusDay && today.bonus_minutes > 0 && (
        <div className="mt-3 text-sm text-bonus">
          {formatHM(today.bonus_minutes)} bonus earned
        </div>
      )}
    </Card>
  );
}
