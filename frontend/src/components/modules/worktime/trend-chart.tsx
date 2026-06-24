"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getStats } from "@/lib/api";
import type { PeriodStats } from "@/lib/types";
import { useApi } from "@/lib/use-api";

interface Point {
  label: string;
  worked: number; // hours
  target: number; // hours
}

// Short, locale-friendly week label without the weekday, e.g. "Jun 8" / "8 Jun".
function weekLabel(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

function toPoints(trend: PeriodStats[]): Point[] {
  return trend.map((p) => ({
    label: weekLabel(p.start),
    worked: +(p.worked_minutes / 60).toFixed(1),
    target: +(p.target_minutes / 60).toFixed(1),
  }));
}

export function TrendChart() {
  const { data, loading, error } = useApi(() => getStats("week", undefined, 8));

  // Recharts needs the DOM; only render the chart after mount so the static
  // export prerender doesn't try to size a container with no dimensions.
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const points = data ? toPoints(data.trend) : [];

  return (
    <Card className="p-5">
      <h2 className="text-sm font-semibold">Weekly trend</h2>
      <p className="text-xs text-muted-foreground">
        Hours worked per week vs. target
      </p>

      {loading || !mounted ? (
        <Skeleton className="mt-4 h-56 w-full" />
      ) : error || !data ? (
        <p className="mt-4 text-sm text-muted-foreground">{error ?? "No data"}</p>
      ) : (
        <div className="mt-4 h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={points}
              margin={{ top: 8, right: 8, bottom: 0, left: -16 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--border)"
                vertical={false}
              />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                tickLine={false}
                axisLine={{ stroke: "var(--border)" }}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                tickLine={false}
                axisLine={false}
                width={36}
              />
              <Tooltip
                contentStyle={{
                  background: "var(--card)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  fontSize: 12,
                  color: "var(--foreground)",
                }}
                labelStyle={{ color: "var(--muted-foreground)" }}
                formatter={(value, name) => [`${value}h`, name]}
              />
              <Bar
                dataKey="worked"
                name="Worked"
                fill="var(--target)"
                radius={[4, 4, 0, 0]}
                maxBarSize={36}
              />
              <Line
                dataKey="target"
                name="Target"
                stroke="var(--muted-foreground)"
                strokeDasharray="4 4"
                strokeWidth={2}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  );
}
