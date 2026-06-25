"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, deleteDayType, getDayTypes, setDayType } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { DayTypeName } from "@/lib/types";
import { useApi } from "@/lib/use-api";

const TYPES: { value: DayTypeName; label: string }[] = [
  { value: "holiday", label: "Holiday" },
  { value: "leave", label: "Leave" },
  { value: "vacation", label: "Vacation" },
];

function todayISO(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

export function HolidaySettings() {
  const year = new Date().getFullYear();
  const markings = useApi(() => getDayTypes(`${year}-01-01`, `${year}-12-31`));

  const [date, setDate] = useState(todayISO());
  const [type, setType] = useState<DayTypeName>("holiday");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!date) {
      setError("Pick a date.");
      return;
    }
    setSaving(true);
    try {
      await setDayType({ date, type, name: name || null });
      setName("");
      markings.reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(d: string) {
    await deleteDayType(d);
    markings.reload();
  }

  return (
    <Card className="p-6">
      <h2 className="text-base font-semibold">Holidays &amp; time off ({year})</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Mark a day as holiday, leave, or vacation. Worked hours on these days
        count as bonus.
      </p>

      <form
        onSubmit={handleAdd}
        className="mt-4 grid gap-3 sm:grid-cols-[auto_auto_1fr_auto] sm:items-end"
      >
        <div className="space-y-1.5">
          <Label htmlFor="h-date">Date</Label>
          <Input
            id="h-date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="h-type">Type</Label>
          <Select
            id="h-type"
            value={type}
            onChange={(e) => setType(e.target.value as DayTypeName)}
          >
            {TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="h-name">Name (optional)</Label>
          <Input
            id="h-name"
            type="text"
            placeholder="e.g. New Year"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <Button type="submit" disabled={saving}>
          {saving ? "Saving…" : "Mark day"}
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
        {markings.loading ? (
          <Skeleton className="h-24 w-full" />
        ) : markings.error ? (
          <p className="text-sm text-muted-foreground">{markings.error}</p>
        ) : markings.data && markings.data.length > 0 ? (
          <ul className="divide-y divide-border rounded-md border border-border">
            {markings.data.map((m) => (
              <li
                key={m.date}
                className="flex items-center justify-between px-3 py-2 text-sm"
              >
                <span className="flex items-center gap-2">
                  <span className="tabular-nums">{formatDate(m.date)}</span>
                  <Badge tone="leave">{m.type}</Badge>
                  {m.name && (
                    <span className="text-muted-foreground">{m.name}</span>
                  )}
                </span>
                <button
                  type="button"
                  onClick={() => handleDelete(m.date)}
                  className="rounded px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">No marked days yet.</p>
        )}
      </div>
    </Card>
  );
}
