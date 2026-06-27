"use client";

import { useState } from "react";

import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { getDebt } from "@/lib/api";
import { formatHM, formatSignedHM } from "@/lib/format";
import type { Debt } from "@/lib/types";
import { useApi } from "@/lib/use-api";
import { cn } from "@/lib/utils";

type Mode = "week" | "month" | "custom";

const MODES: { value: Mode; label: string }[] = [
  { value: "week", label: "This week" },
  { value: "month", label: "This month" },
  { value: "custom", label: "Custom" },
];

function ModeToggle({
  mode,
  onChange,
}: {
  mode: Mode;
  onChange: (m: Mode) => void;
}) {
  return (
    <div className="inline-flex rounded-md border border-border p-0.5">
      {MODES.map((m) => (
        <button
          key={m.value}
          onClick={() => onChange(m.value)}
          aria-pressed={mode === m.value}
          className={cn(
            "rounded px-2.5 py-1 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            mode === m.value
              ? "bg-muted text-foreground"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
}

// One reconciling breakdown row (only rendered when the bucket has days).
function BreakdownRow({
  icon,
  iconClass,
  label,
  minutes,
  days,
}: {
  icon: string;
  iconClass: string;
  label: string;
  minutes: number;
  days: number;
}) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="flex items-center gap-2 text-muted-foreground">
        <span className={cn("tabular-nums", iconClass)} aria-hidden>
          {icon}
        </span>
        {label}
        <span className="text-xs text-muted-foreground">
          ({days} {days === 1 ? "day" : "days"})
        </span>
      </span>
      <span
        className={cn(
          "tabular-nums",
          minutes >= 0 ? "text-target" : "text-foreground",
        )}
      >
        {formatSignedHM(minutes)}
      </span>
    </div>
  );
}

function DebtBody({ debt }: { debt: Debt }) {
  const net = debt.over_under_minutes;
  const isDebt = net < 0;
  const isSurplus = net > 0;
  const hasBreakdown =
    debt.no_show_days > 0 || debt.under_days > 0 || debt.surplus_days > 0;

  // Remaining / catch-up line.
  let remaining: React.ReactNode;
  if (debt.outstanding_minutes > 0 && debt.remaining_work_days > 0) {
    remaining = (
      <>
        <span className="font-medium text-foreground">
          {debt.remaining_work_days}
        </span>{" "}
        work {debt.remaining_work_days === 1 ? "day" : "days"} left ·{" "}
        {formatHM(debt.remaining_target_minutes)} target · to clear: avg{" "}
        <span className="font-medium text-foreground">
          {formatHM(debt.avg_needed_per_day_minutes ?? 0)}
        </span>
        /day
      </>
    );
  } else if (debt.outstanding_minutes > 0 && debt.remaining_work_days === 0) {
    remaining = "No work days left this period to clear it.";
  } else if (debt.remaining_work_days > 0) {
    remaining = (
      <>
        <span className="font-medium text-foreground">
          {debt.remaining_work_days}
        </span>{" "}
        work {debt.remaining_work_days === 1 ? "day" : "days"} left ·{" "}
        {formatHM(debt.remaining_target_minutes)} target ahead
      </>
    );
  } else {
    remaining = "Nothing left in this period.";
  }

  return (
    <div className="mt-4 space-y-4">
      {/* Headline */}
      <div>
        <div
          className={cn(
            "text-3xl font-semibold tabular-nums",
            isDebt ? "text-foreground" : isSurplus ? "text-target" : "",
          )}
        >
          {net === 0 ? "0m" : formatSignedHM(net)}
        </div>
        <div className="mt-0.5 text-sm text-muted-foreground">
          {isDebt
            ? "owed"
            : isSurplus
              ? "ahead"
              : debt.days_counted === 0
                ? "nothing owed for this period"
                : "exactly on target"}
        </div>
      </div>

      {/* Why am I short */}
      {hasBreakdown && (
        <div className="space-y-1.5 border-t border-border pt-3">
          {debt.no_show_days > 0 && (
            <BreakdownRow
              icon="✗"
              iconClass="text-foreground"
              label="Didn't come in"
              minutes={debt.no_show_minutes}
              days={debt.no_show_days}
            />
          )}
          {debt.under_days > 0 && (
            <BreakdownRow
              icon="▼"
              iconClass="text-muted-foreground"
              label="Came in, under target"
              minutes={debt.under_minutes}
              days={debt.under_days}
            />
          )}
          {debt.surplus_days > 0 && (
            <BreakdownRow
              icon="▲"
              iconClass="text-target"
              label="Surplus credit"
              minutes={debt.surplus_minutes}
              days={debt.surplus_days}
            />
          )}
        </div>
      )}

      {/* Remaining / catch-up */}
      <div className="border-t border-border pt-3 text-sm text-muted-foreground">
        {remaining}
      </div>
    </div>
  );
}

export function DebtCard() {
  const [mode, setMode] = useState<Mode>("month");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  const customReady = mode === "custom" && from !== "" && to !== "";
  const period = mode === "custom" ? undefined : mode;

  const { data, loading, error } = useApi<Debt | null>(
    () =>
      mode === "custom"
        ? customReady
          ? getDebt({ from, to })
          : Promise.resolve(null)
        : getDebt({ period }),
    [mode, from, to],
  );

  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Hours owed
        </h2>
        <ModeToggle mode={mode} onChange={setMode} />
      </div>

      {mode === "custom" && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Input
            type="date"
            aria-label="From date"
            value={from}
            max={to || undefined}
            onChange={(e) => setFrom(e.target.value)}
            className="w-auto"
          />
          <span className="text-sm text-muted-foreground">to</span>
          <Input
            type="date"
            aria-label="To date"
            value={to}
            min={from || undefined}
            onChange={(e) => setTo(e.target.value)}
            className="w-auto"
          />
        </div>
      )}

      {mode === "custom" && !customReady ? (
        <p className="mt-4 text-sm text-muted-foreground">
          Pick a start and end date.
        </p>
      ) : loading ? (
        <Skeleton className="mt-4 h-32 w-full" />
      ) : error || !data ? (
        <p className="mt-4 text-sm text-muted-foreground">{error ?? "No data"}</p>
      ) : (
        <DebtBody debt={data} />
      )}
    </Card>
  );
}
