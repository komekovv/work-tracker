"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Modal } from "@/components/ui/modal";
import { ApiError, createManualSession, editSession } from "@/lib/api";

export interface SessionFormState {
  open: boolean;
  mode: "add" | "edit";
  sessionId?: number;
  start: string; // datetime-local "YYYY-MM-DDTHH:MM"
  end: string;
}

export function SessionFormModal({
  state,
  onClose,
  onSaved,
}: {
  state: SessionFormState;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [start, setStart] = useState(state.start);
  const [end, setEnd] = useState(state.end);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Re-seed the fields each time the modal opens (for a new add/edit target).
  useEffect(() => {
    if (state.open) {
      setStart(state.start);
      setEnd(state.end);
      setError(null);
      setSaving(false);
    }
  }, [state.open, state.start, state.end]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!start || !end) {
      setError("Start and end are required.");
      return;
    }
    // Same-format local ISO strings: lexicographic compare == chronological.
    if (start >= end) {
      setError("End must be after start.");
      return;
    }

    setSaving(true);
    try {
      if (state.mode === "add") {
        await createManualSession({ start_time: start, end_time: end });
      } else if (state.sessionId !== undefined) {
        await editSession(state.sessionId, {
          start_time: start,
          end_time: end,
        });
      }
      onSaved();
      onClose();
    } catch (err) {
      // ApiError carries the backend detail (e.g. overlap 409, 404).
      setError(err instanceof ApiError ? err.message : "Could not save session.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal
      open={state.open}
      onClose={onClose}
      title={state.mode === "add" ? "Add session" : "Edit session"}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="session-start">Start</Label>
          <Input
            id="session-start"
            type="datetime-local"
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="session-end">End</Label>
          <Input
            id="session-end"
            type="datetime-local"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
          />
        </div>

        {error && (
          <p
            role="alert"
            className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-600 dark:text-red-400"
          >
            {error}
          </p>
        )}

        <div className="flex justify-end gap-2 pt-1">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
