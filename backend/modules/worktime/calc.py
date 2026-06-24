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
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from backend.core import calendar as cal
from backend.core import day_types as day_types_mod
from backend.core.day_types import HOLIDAY, LEAVE, VACATION, WORKDAY
from backend.core.db import optional_connection

# Day types that override the normal target (zero it, make worked time bonus).
_SPECIAL_TYPES = frozenset({HOLIDAY, LEAVE, VACATION})


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


# ===========================================================================
# Per-day calculation
# ===========================================================================


@dataclass(frozen=True)
class DayResult:
    """The computed picture of one day (all times in minutes).

    `target_met` is `None` for **bonus/special days** (Sunday, holiday, leave,
    vacation): they are excluded from target completion and *skipped* by the
    streak (D3) rather than counting as pass or fail.
    """

    date: str
    day_type: str            # explicit marking, or 'workday' if unmarked
    is_sunday: bool
    worked_minutes: int
    target_minutes: int      # 0 on bonus days
    over_under_minutes: int  # worked - target; 0 on bonus days
    is_bonus: bool           # a bonus day that was actually worked
    bonus_minutes: int       # all worked minutes on a bonus day, else 0
    target_met: bool | None  # None = excluded/skipped (bonus day)


def _worked_minutes(conn: sqlite3.Connection, iso_day: str) -> int:
    """Sum recorded minutes for a day. Open sessions (NULL duration) count 0."""
    row = conn.execute(
        "SELECT COALESCE(SUM(duration_minutes), 0) AS w FROM sessions WHERE date = ?",
        (iso_day,),
    ).fetchone()
    return int(row["w"])


def compute_day(
    target_date: str | date,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> DayResult:
    """Compute the full `DayResult` for a date from live data.

    Bonus rules (cases C1–C5):

    - A **bonus day** is a Sunday, or a holiday/leave/vacation whose day-type
      marking overrides the target (`affects_target`). On a bonus day the target
      is 0 and **all** worked minutes are bonus (C1/C2/C3). A day that is both
      Sunday *and* holiday is still one bonus day — worked time is counted once
      (C5).
    - A **normal day** uses the resolved target; `over_under = worked - target`
      and `target_met = worked >= target`.

    Manual-vs-planned day-type conflicts (C4) are already settled in the
    `day_types` table, so this just reads the effective marking.
    """
    d = cal.to_date(target_date)
    iso = d.isoformat()
    is_sunday = d.weekday() == cal.SUNDAY

    with optional_connection(conn, db_path) as c:
        worked = _worked_minutes(c, iso)
        marking = day_types_mod.get_day_type(iso, conn=c)
        overrides_target = (
            marking is not None
            and marking.type in _SPECIAL_TYPES
            and marking.affects_target
        )
        bonus_day = is_sunday or overrides_target

        if bonus_day:
            target_minutes = 0
            is_bonus = worked > 0
            bonus_minutes = worked if is_bonus else 0
            over_under = 0
            target_met: bool | None = None  # excluded from completion / streak
        else:
            hours = resolve_target(iso, conn=c)
            target_minutes = round((hours or 0) * 60)
            is_bonus = False
            bonus_minutes = 0
            over_under = worked - target_minutes
            target_met = worked >= target_minutes

        day_type = marking.type if marking is not None else WORKDAY

    return DayResult(
        date=iso,
        day_type=day_type,
        is_sunday=is_sunday,
        worked_minutes=worked,
        target_minutes=target_minutes,
        over_under_minutes=over_under,
        is_bonus=is_bonus,
        bonus_minutes=bonus_minutes,
        target_met=target_met,
    )
