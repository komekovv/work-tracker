"use client";

import { useState } from "react";
import Link from "next/link";

import { CalendarGrid } from "@/components/modules/worktime/calendar-grid";
import { DayPanel } from "@/components/modules/worktime/day-panel";
import { PeriodSummaryPanel } from "@/components/modules/worktime/period-summary-panel";
import {
  SessionFormModal,
  type SessionFormState,
} from "@/components/modules/worktime/session-form-modal";
import {
  SidePanelTabs,
  type SidePanelTab,
} from "@/components/modules/worktime/side-panel-tabs";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ErrorState } from "@/components/ui/error-state";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { getCalendar, getSessions } from "@/lib/api";
import { formatMonth } from "@/lib/format";
import type { SessionOut } from "@/lib/types";
import { useApi } from "@/lib/use-api";

function pad(n: number): string {
  return String(n).padStart(2, "0");
}
function currentMonth(): string {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}`;
}
function shiftMonth(month: string, delta: number): string {
  const [y, m] = month.split("-").map(Number);
  const d = new Date(y, m - 1 + delta, 1);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}`;
}
function monthBounds(month: string): [string, string] {
  const [y, m] = month.split("-").map(Number);
  const last = new Date(y, m, 0).getDate();
  return [`${month}-01`, `${month}-${pad(last)}`];
}
function todayISO(): string {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export default function WorktimePage() {
  const [month, setMonth] = useState(currentMonth());
  const [selected, setSelected] = useState<string | null>(null);
  const [from, to] = monthBounds(month);

  const cal = useApi(() => getCalendar(month), [month]);
  const sess = useApi(() => getSessions(from, to), [month]);

  // Right-panel view: per-day (calendar-driven) or a range summary.
  const [tab, setTab] = useState<SidePanelTab>("day");
  const [cFrom, setCFrom] = useState("");
  const [cTo, setCTo] = useState("");
  // Bumped on session add/edit so the summary panel re-fetches too.
  const [reloadToken, setReloadToken] = useState(0);

  const [form, setForm] = useState<SessionFormState>({
    open: false,
    mode: "add",
    start: "",
    end: "",
  });

  const goMonth = (delta: number) => {
    setMonth((m) => shiftMonth(m, delta));
    setSelected(null);
  };

  const selectedDay =
    cal.data?.days.find((d) => d.date === selected) ?? null;
  const selectedSessions =
    sess.data?.filter((s) => s.date === selected) ?? [];

  const openAdd = () => {
    const date = selected ?? todayISO();
    setForm({
      open: true,
      mode: "add",
      start: `${date}T09:00`,
      end: `${date}T17:00`,
    });
  };
  const openEdit = (s: SessionOut) => {
    setForm({
      open: true,
      mode: "edit",
      sessionId: s.id,
      start: s.start_time.slice(0, 16),
      // Open sessions keep an empty end field (so saving leaves them open).
      end: s.end_time ? s.end_time.slice(0, 16) : "",
    });
  };
  const refresh = () => {
    cal.reload();
    sess.reload();
    setReloadToken((n) => n + 1);
  };

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Worktime</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Monthly calendar and session history.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/worktime/settings"
            className="rounded-md px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Targets &amp; holidays
          </Link>
          <Button onClick={openAdd}>Add session</Button>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold tabular-nums">
          {formatMonth(month)}
        </h2>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => goMonth(-1)} aria-label="Previous month">
            ‹
          </Button>
          <Button
            variant="ghost"
            onClick={() => {
              setMonth(currentMonth());
              setSelected(null);
            }}
          >
            Today
          </Button>
          <Button variant="outline" onClick={() => goMonth(1)} aria-label="Next month">
            ›
          </Button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_20rem]">
        <Card className="p-4">
          {cal.loading ? (
            <Skeleton className="h-80 w-full" />
          ) : cal.error || !cal.data ? (
            <ErrorState message={cal.error ?? "No data"} onRetry={cal.reload} />
          ) : (
            <CalendarGrid
              calendar={cal.data}
              selected={selected}
              today={todayISO()}
              onSelect={setSelected}
            />
          )}
        </Card>

        <div className="space-y-3 lg:sticky lg:top-20 lg:self-start">
          <SidePanelTabs value={tab} onChange={setTab} />

          {tab === "custom" && (
            <div className="flex flex-wrap items-center gap-2">
              <Input
                type="date"
                aria-label="From date"
                value={cFrom}
                max={cTo || undefined}
                onChange={(e) => setCFrom(e.target.value)}
                className="w-auto"
              />
              <span className="text-sm text-muted-foreground">to</span>
              <Input
                type="date"
                aria-label="To date"
                value={cTo}
                min={cFrom || undefined}
                onChange={(e) => setCTo(e.target.value)}
                className="w-auto"
              />
            </div>
          )}

          {tab === "day" ? (
            <DayPanel
              day={selectedDay}
              sessions={selectedSessions}
              onEdit={openEdit}
            />
          ) : tab === "week" ? (
            <PeriodSummaryPanel
              period="week"
              anchor={selected ?? todayISO()}
              reloadToken={reloadToken}
            />
          ) : tab === "month" ? (
            <PeriodSummaryPanel
              period="month"
              anchor={`${month}-01`}
              reloadToken={reloadToken}
            />
          ) : (
            <PeriodSummaryPanel
              from={cFrom}
              to={cTo}
              reloadToken={reloadToken}
            />
          )}
        </div>
      </div>

      <SessionFormModal
        state={form}
        onClose={() => setForm((f) => ({ ...f, open: false }))}
        onSaved={refresh}
      />
    </section>
  );
}
