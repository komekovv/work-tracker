"use client";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getSummary } from "@/lib/api";
import {
  formatDate,
  formatHM,
  formatPct,
  formatSignedHM,
} from "@/lib/format";
import type { PeriodKind, PeriodStats } from "@/lib/types";
import { useApi } from "@/lib/use-api";

function todayISO(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function Row({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className={`text-right tabular-nums ${className ?? ""}`}>{children}</dd>
    </>
  );
}

function SummaryBody({ stats }: { stats: PeriodStats }) {
  // The response's end is capped at today for the current period; flag that.
  const toDate = stats.end === todayISO();
  return (
    <>
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold">
          {formatDate(stats.start)} – {formatDate(stats.end)}
        </h2>
        {toDate && (
          <span className="text-xs text-muted-foreground">to date</span>
        )}
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-y-2 text-sm">
        <Row label="Worked">{formatHM(stats.worked_minutes)}</Row>
        <Row label="Target">{formatHM(stats.target_minutes)}</Row>
        <Row label="Over / under">
          {formatSignedHM(stats.over_under_minutes)}
        </Row>
        <Row label="Completion">{formatPct(stats.completion_pct)}</Row>
        <Row label="Bonus" className="text-bonus">
          {formatHM(stats.bonus_minutes)}
        </Row>
        <Row label="Days met">
          {stats.days_met}/{stats.days_counted}
        </Row>
        <Row label="Days worked">{stats.days_worked}</Row>
        <Row label="Avg / day">
          {stats.average_worked_minutes === null
            ? "—"
            : formatHM(stats.average_worked_minutes)}
        </Row>
      </dl>
    </>
  );
}

export function PeriodSummaryPanel({
  period,
  anchor,
  from,
  to,
  reloadToken,
}: {
  period?: PeriodKind;
  anchor?: string;
  from?: string;
  to?: string;
  reloadToken: number;
}) {
  const isCustom = period === undefined;
  const customReady = !isCustom || (from !== "" && to !== "");

  const { data, loading, error } = useApi<PeriodStats | null>(
    () =>
      isCustom
        ? customReady
          ? getSummary({ from, to })
          : Promise.resolve(null)
        : getSummary({ period, anchor }),
    [period, anchor, from, to, reloadToken],
  );

  return (
    <Card className="p-5">
      {isCustom && !customReady ? (
        <p className="text-sm text-muted-foreground">
          Pick a start and end date.
        </p>
      ) : loading ? (
        <Skeleton className="h-48 w-full" />
      ) : error || !data ? (
        <p className="text-sm text-muted-foreground">{error ?? "No data"}</p>
      ) : (
        <SummaryBody stats={data} />
      )}
    </Card>
  );
}
