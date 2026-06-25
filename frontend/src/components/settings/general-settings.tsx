"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, getSettings, updateSettings } from "@/lib/api";
import type { Settings } from "@/lib/types";
import { useApi } from "@/lib/use-api";

const WEEKDAYS = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
];

// `theme` is controlled client-side (localStorage) by the Theme card above, so
// it's hidden from this generic editor to avoid a confusing dead field.
const HIDDEN = new Set(["theme"]);

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

export function GeneralSettings() {
  const settings = useApi(getSettings);
  const [draft, setDraft] = useState<Settings>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (settings.data) setDraft(settings.data);
  }, [settings.data]);

  const keys = Object.keys(draft)
    .filter((k) => !HIDDEN.has(k))
    .sort();

  const setValue = (key: string, value: string) => {
    setDraft((d) => ({ ...d, [key]: value }));
    setSaved(false);
  };

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const payload: Settings = {};
      for (const k of keys) payload[k] = draft[k];
      await updateSettings(payload);
      settings.reload();
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save settings.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card className="p-6">
      <h2 className="text-base font-semibold">General settings</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Dynamic settings stored in the database.
      </p>

      {settings.loading ? (
        <Skeleton className="mt-4 h-24 w-full" />
      ) : settings.error ? (
        <p className="mt-4 text-sm text-muted-foreground">{settings.error}</p>
      ) : (
        <form onSubmit={handleSave} className="mt-4 space-y-4">
          {keys.map((k) => (
            <div
              key={k}
              className="grid gap-1.5 sm:grid-cols-[14rem_1fr] sm:items-center"
            >
              <Label htmlFor={`s-${k}`} className="font-mono text-xs">
                {k}
              </Label>
              {k === "week_start_day" ? (
                <Select
                  id={`s-${k}`}
                  value={draft[k]}
                  onChange={(e) => setValue(k, e.target.value)}
                >
                  {WEEKDAYS.map((w) => (
                    <option key={w} value={w}>
                      {cap(w)}
                    </option>
                  ))}
                </Select>
              ) : (
                <Input
                  id={`s-${k}`}
                  value={draft[k]}
                  onChange={(e) => setValue(k, e.target.value)}
                />
              )}
            </div>
          ))}

          {error && (
            <p
              role="alert"
              className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-600 dark:text-red-400"
            >
              {error}
            </p>
          )}

          <div className="flex items-center gap-3">
            <Button type="submit" disabled={saving}>
              {saving ? "Saving…" : "Save settings"}
            </Button>
            {saved && (
              <span className="text-sm text-muted-foreground">Saved.</span>
            )}
          </div>
        </form>
      )}
    </Card>
  );
}
