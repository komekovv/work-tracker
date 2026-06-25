"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Modal } from "@/components/ui/modal";
import {
  ApiError,
  createManualSession,
  deleteSession,
  editSession,
} from "@/lib/api";

export interface SessionFormState {
  open: boolean;
  mode: "add" | "edit";
  sessionId?: number;
  start: string; // datetime-local "YYYY-MM-DDTHH:MM"
  end: string; // empty = open session (no end yet)
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
  const [confirmDelete, setConfirmDelete] = useState(false);

  // Re-seed the fields each time the modal opens (for a new add/edit target).
  useEffect(() => {
    if (state.open) {
      setStart(state.start);
      setEnd(state.end);
      setError(null);
      setSaving(false);
      setConfirmDelete(false);
    }
  }, [state.open, state.start, state.end]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!start) {
      setError("Start is required.");
      return;
    }
    // Same-format local ISO strings: lexicographic compare == chronological.
    if (end && start >= end) {
      setError("End must be after start.");
      return;
    }

    // Empty end → open session (clock-in).
    const endValue = end ? end : null;

    setSaving(true);
    try {
      if (state.mode === "add") {
        await createManualSession({ start_time: start, end_time: endValue });
      } else if (state.sessionId !== undefined) {
        await editSession(state.sessionId, {
          start_time: start,
          end_time: endValue,
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

  async function handleDelete() {
    if (state.sessionId === undefined) return;
    setError(null);
    setSaving(true);
    try {
      await deleteSession(state.sessionId);
      onSaved();
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete session.");
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
          <Label htmlFor="session-end">
            End{" "}
            <span className="font-normal text-muted-foreground">
              (leave empty for an open session)
            </span>
          </Label>
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

        <div className="flex items-center justify-between pt-1">
          {/* Delete (edit mode only), with a two-click confirm. */}
          <div>
            {state.mode === "edit" &&
              (confirmDelete ? (
                <Button
                  type="button"
                  variant="ghost"
                  disabled={saving}
                  onClick={handleDelete}
                  className="text-red-600 dark:text-red-400"
                >
                  Confirm delete?
                </Button>
              ) : (
                <Button
                  type="button"
                  variant="ghost"
                  disabled={saving}
                  onClick={() => setConfirmDelete(true)}
                  className="text-muted-foreground hover:text-red-600 dark:hover:text-red-400"
                >
                  Delete
                </Button>
              ))}
          </div>

          <div className="flex gap-2">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? "Saving…" : "Save"}
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  );
}
