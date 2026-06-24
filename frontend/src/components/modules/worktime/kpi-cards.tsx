import type { Kpi } from "@/lib/types";
import { formatHours, formatPct } from "@/lib/format";
import { StatCard } from "./stat-card";

function MonthDelta({ kpi }: { kpi: Kpi }) {
  const { comparison } = kpi;
  if (!comparison.has_prior || comparison.pct_change === null) {
    return <span>no prior month</span>;
  }
  const up = comparison.pct_change >= 0;
  return (
    <span className={up ? "text-target" : "text-muted-foreground"}>
      {up ? "▲" : "▼"} {Math.abs(comparison.pct_change)}% vs last month
    </span>
  );
}

export function KpiCards({ kpi }: { kpi: Kpi }) {
  const m = kpi.month;
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        label="Month total"
        value={formatHours(m.worked_minutes)}
        sub={<MonthDelta kpi={kpi} />}
      />
      <StatCard
        label="Target"
        value={formatPct(m.completion_pct)}
        sub={`${m.days_met}/${m.days_counted} days met`}
        accentClass="bg-target"
      />
      <StatCard
        label="Streak"
        value={kpi.streak}
        sub={kpi.streak === 1 ? "day" : "days"}
      />
      <StatCard
        label="Bonus"
        value={formatHours(m.bonus_minutes)}
        sub="this month"
        accentClass="bg-bonus"
      />
    </div>
  );
}
