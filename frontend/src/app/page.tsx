"use client";

import { DebtCard } from "@/components/modules/worktime/debt-card";
import { Heatmap } from "@/components/modules/worktime/heatmap";
import { KpiCards } from "@/components/modules/worktime/kpi-cards";
import { TodayCard } from "@/components/modules/worktime/today-card";
import { TrendChart } from "@/components/modules/worktime/trend-chart";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { getKpi, getToday } from "@/lib/api";
import { useApi } from "@/lib/use-api";

function DashboardSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-28 w-full" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full" />
        ))}
      </div>
    </div>
  );
}

export default function Home() {
  const kpi = useApi(getKpi);
  const today = useApi(getToday);

  const loading = kpi.loading || today.loading;
  const error = kpi.error ?? today.error;

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your work-time and KPI overview.
        </p>
      </div>

      {loading ? (
        <DashboardSkeleton />
      ) : error ? (
        <ErrorState
          message={error}
          onRetry={() => {
            kpi.reload();
            today.reload();
          }}
        />
      ) : (
        <div className="space-y-4">
          {today.data && <TodayCard today={today.data} />}
          {kpi.data && <KpiCards kpi={kpi.data} />}
          <DebtCard />
          <div className="grid gap-4 lg:grid-cols-2">
            <Heatmap />
            <TrendChart />
          </div>
        </div>
      )}
    </section>
  );
}
