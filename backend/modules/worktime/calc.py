"""Worktime calculations — target resolution, bonus, over/under.

Everything here is **live and read-only**: values are computed from the current
`targets`, `day_types`, and `sessions` data each time, never snapshotted. That
keeps results correct when targets or day-types change retroactively (case A3).
Work is done at the **day level** — a target applies to a day's *total* worked
time, not to individual sessions.

This step covers target resolution; per-day bonus/over-under is added next.
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from backend.core import calendar as cal
from backend.core.db import optional_connection


def resolve_target(
    target_date: str | date,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> float | None:
    """Return the daily target hours in effect for ``target_date``, or None.

    Resolution precedence (cases A1–A4):

    1. **Specificity wins (A2/A4):** a rule for the date's exact weekday beats
       the base (all-days) rule, even if the base rule is newer. A weekday
       "short day" persists until itself changed.
    2. **Recency within a specificity (A1/A3):** among rules of the same
       specificity, the most recent ``effective_from`` on/before the date wins
       (ties broken by latest id). Retroactive edits therefore just change what
       resolution returns — no stored value to update.

    Returns ``None`` when no daily target is defined on/before the date; the
    caller decides how to treat "no target" (Step 2 treats it as 0).
    """
    d = cal.to_date(target_date)
    iso = d.isoformat()
    weekday = d.weekday()  # Mon=0…Sun=6, matches targets.weekday

    with optional_connection(conn, db_path) as c:
        # 1. Most recent weekday-specific rule on/before the date.
        row = c.execute(
            "SELECT daily_hours FROM targets "
            "WHERE period = 'daily' AND weekday = ? AND effective_from <= ? "
            "ORDER BY effective_from DESC, id DESC LIMIT 1",
            (weekday, iso),
        ).fetchone()
        if row is None:
            # 2. Fall back to the most recent base (all-days) rule.
            row = c.execute(
                "SELECT daily_hours FROM targets "
                "WHERE period = 'daily' AND weekday IS NULL AND effective_from <= ? "
                "ORDER BY effective_from DESC, id DESC LIMIT 1",
                (iso,),
            ).fetchone()

    return row["daily_hours"] if row is not None else None
