"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, deleteTarget, getTargets, setTarget } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { useApi } from "@/lib/use-api";

const WEEKDAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

function todayISO(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

export function TargetSettings() {
  const targets = useApi(getTargets);

  const [effectiveFrom, setEffectiveFrom] = useState(todayISO());
  const [hours, setHours] = useState("8");
  const [weekday, setWeekday] = useState(""); // "" = all days
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const value = Number(hours);
    if (!effectiveFrom || Number.isNaN(value) || value < 0) {
      setError("Enter a valid date and non-negative hours.");
      return;
    }
    setSaving(true);
    try {
      await setTarget({
        effective_from: effectiveFrom,
        daily_hours: value,
        weekday: weekday === "" ? null : Number(weekday),
      });
      targets.reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save target.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    await deleteTarget(id);
    targets.reload();
  }

  return (
    <Card className="p-6">
      <h2 className="text-base font-semibold">Targets</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Daily hours, effective from a date. Add a weekday rule for short days.
        Past days keep their old target.
      </p>

      <form
        onSubmit={handleAdd}
        className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto_1fr_auto] sm:items-end"
      >
        <div className="space-y-1.5">
          <Label htmlFor="t-from">Effective from</Label>
          <Input
            id="t-from"
            type="date"
            value={effectiveFrom}
            onChange={(e) => setEffectiveFrom(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="t-hours">Hours</Label>
          <Input
            id="t-hours"
            type="number"
            min="0"
            step="0.5"
            className="sm:w-24"
            value={hours}
            onChange={(e) => setHours(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="t-weekday">Applies to</Label>
          <Select
            id="t-weekday"
            value={weekday}
            onChange={(e) => setWeekday(e.target.value)}
          >
            <option value="">All days</option>
            {WEEKDAYS.map((w, i) => (
              <option key={i} value={i}>
                {w}
              </option>
            ))}
          </Select>
        </div>
        <Button type="submit" disabled={saving}>
          {saving ? "Saving…" : "Add target"}
        </Button>
      </form>

      {error && (
        <p
          role="alert"
          className="mt-3 rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-600 dark:text-red-400"
        >
          {error}
        </p>
      )}

      <div className="mt-6">
        {targets.loading ? (
          <Skeleton className="h-24 w-full" />
        ) : targets.error ? (
          <p className="text-sm text-muted-foreground">{targets.error}</p>
        ) : targets.data && targets.data.length > 0 ? (
          <ul className="divide-y divide-border rounded-md border border-border">
            {targets.data.map((t) => (
              <li
                key={t.id}
                className="flex items-center justify-between px-3 py-2 text-sm"
              >
                <span>
                  <span className="font-medium tabular-nums">
                    {t.daily_hours}h
                  </span>{" "}
                  <span className="text-muted-foreground">
                    · {t.weekday === null ? "All days" : WEEKDAYS[t.weekday]} ·
                    from {formatDate(t.effective_from)}
                  </span>
                </span>
                <button
                  type="button"
                  onClick={() => handleDelete(t.id)}
                  className="rounded px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">No targets yet.</p>
        )}
      </div>
    </Card>
  );
}
