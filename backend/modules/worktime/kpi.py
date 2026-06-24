"""Worktime KPI analytics — aggregation over date ranges.

Builds on `calc.compute_day` (live, read-only) and `core.calendar`. This step
covers period totals and completion; streak/trend/comparison come next.

Decomposition used throughout:

    worked_minutes = worked_toward_target_minutes + bonus_minutes

so bonus is always reported **separately** and never inflates target
completion (case D4). Empty or target-less ranges return zeros with
`completion_pct = None` rather than raising (case D1).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from backend.core import calendar as cal
from backend.core.db import optional_connection
from backend.modules.worktime import calc


@dataclass(frozen=True)
class PeriodStats:
    """Aggregated stats for an inclusive date range (minutes unless noted)."""

    start: str
    end: str
    days: int                          # calendar days in the range
    worked_minutes: int                # all worked time (toward-target + bonus)
    worked_toward_target_minutes: int  # worked on non-bonus days
    target_minutes: int                # required target on counted days
    bonus_minutes: int                 # worked time on bonus days (separate)
    over_under_minutes: int            # net worked - target on non-bonus days
    completion_pct: float | None       # toward-target / target * 100; None if no target
    days_worked: int                   # days with any worked time
    days_counted: int                  # non-bonus days that actually require a target
    days_met: int                      # counted days whose target was met
    average_worked_minutes: float | None  # worked_minutes / days_worked


def period_stats(
    start: str | date,
    end: str | date,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> PeriodStats:
    """Aggregate `compute_day` over the inclusive ``[start, end]`` range."""
    start_d = cal.to_date(start)
    end_d = cal.to_date(end)

    days = 0
    worked = 0
    worked_toward = 0
    target_total = 0
    bonus_total = 0
    over_under = 0
    days_worked = 0
    days_counted = 0
    days_met = 0

    with optional_connection(conn, db_path) as c:
        for day in cal.iter_days(start_d, end_d):
            r = calc.compute_day(day, conn=c)
            days += 1
            worked += r.worked_minutes
            bonus_total += r.bonus_minutes
            if r.worked_minutes > 0:
                days_worked += 1
            if r.target_met is not None:  # non-bonus day
                worked_toward += r.worked_minutes
                target_total += r.target_minutes
                over_under += r.over_under_minutes
                if r.target_minutes > 0:  # only days that actually require work
                    days_counted += 1
                    if r.target_met:
                        days_met += 1

    completion = (
        round(worked_toward / target_total * 100, 1) if target_total > 0 else None
    )
    average_worked = round(worked / days_worked, 1) if days_worked > 0 else None

    return PeriodStats(
        start=start_d.isoformat(),
        end=end_d.isoformat(),
        days=days,
        worked_minutes=worked,
        worked_toward_target_minutes=worked_toward,
        target_minutes=target_total,
        bonus_minutes=bonus_total,
        over_under_minutes=over_under,
        completion_pct=completion,
        days_worked=days_worked,
        days_counted=days_counted,
        days_met=days_met,
        average_worked_minutes=average_worked,
    )


def month_stats(
    in_month: str | date,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> PeriodStats:
    """Stats for the whole calendar month containing ``in_month``."""
    first, last = cal.month_bounds(in_month)
    return period_stats(first, last, conn=conn, db_path=db_path)


def week_stats(
    in_week: str | date,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> PeriodStats:
    """Stats for the week containing ``in_week`` (honours `week_start_day`)."""
    first, last = cal.week_bounds(in_week, conn=conn, db_path=db_path)
    return period_stats(first, last, conn=conn, db_path=db_path)
