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
from datetime import date, timedelta
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
    as_of: str | date | None = None,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> PeriodStats:
    """Aggregate `compute_day` over the inclusive ``[start, end]`` range.

    If ``as_of`` is given and falls before ``end``, the range is capped at it —
    this yields month-/week-to-date stats for the *current* period while leaving
    past periods (whose end is already <= as_of) unaffected.
    """
    start_d = cal.to_date(start)
    end_d = cal.to_date(end)
    if as_of is not None:
        cap = cal.to_date(as_of)
        if cap < end_d:
            end_d = cap

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


def streak(
    as_of: str | date | None = None,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> int:
    """Count consecutive target-met days ending at ``as_of`` (default today).

    Walking backwards (case D3):

    - Days with **no requirement** — bonus days (Sunday/holiday/leave/vacation)
      *and* days whose resolved target is 0 — are **skipped**: they neither
      count nor break the run. This is why leave/vacation don't break a streak,
      and why pre-target history can't inflate it.
    - A day that **met** its (>0) target adds to the streak.
    - The first day that **missed** its target ends the streak.

    The scan is bounded below by the earliest recorded session, so it always
    terminates; with no sessions the streak is 0.
    """
    with optional_connection(conn, db_path) as c:
        row = c.execute("SELECT MIN(date) AS d FROM sessions").fetchone()
        earliest = row["d"]
        if earliest is None:
            return 0
        earliest_d = cal.to_date(earliest)
        day = cal.to_date(as_of) if as_of is not None else date.today()

        count = 0
        while day >= earliest_d:
            r = calc.compute_day(day, conn=c)
            if r.target_minutes == 0:  # no requirement → skip, don't break
                day -= timedelta(days=1)
                continue
            if r.target_met:
                count += 1
                day -= timedelta(days=1)
            else:
                break
    return count


def _period_bounds(
    period: str,
    anchor: date,
    conn: sqlite3.Connection | None,
    db_path: Path | str | None,
) -> tuple[date, date]:
    """Inclusive bounds of the week/month containing ``anchor``."""
    if period == "week":
        return cal.week_bounds(anchor, conn=conn, db_path=db_path)
    if period == "month":
        return cal.month_bounds(anchor)
    raise ValueError("period must be 'week' or 'month'")


def trend(
    period: str = "week",
    n: int = 6,
    as_of: str | date | None = None,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> list[PeriodStats]:
    """The last ``n`` consecutive periods up to ``as_of``, oldest first."""
    anchor = cal.to_date(as_of) if as_of is not None else date.today()
    series: list[PeriodStats] = []
    with optional_connection(conn, db_path) as c:
        start, _ = _period_bounds(period, anchor, c, db_path)
        for _ in range(max(0, n)):
            p_start, p_end = _period_bounds(period, start, c, db_path)
            # Cap at the anchor so the latest (current) period is to-date; past
            # periods end before the anchor and are unaffected.
            series.append(period_stats(p_start, p_end, as_of=anchor, conn=c))
            start = p_start - timedelta(days=1)  # step into the previous period
    series.reverse()
    return series


@dataclass(frozen=True)
class Comparison:
    """Current period vs the immediately preceding one (case D2)."""

    period: str
    current: PeriodStats
    previous: PeriodStats
    worked_diff_minutes: int          # current - previous
    completion_diff_pct: float | None  # points, None if either side has none
    pct_change: float | None           # worked % change, None if no prior data
    has_prior: bool                    # did the previous period have any work?


def compare(
    period: str = "month",
    as_of: str | date | None = None,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> Comparison:
    """Compare the current period to the previous one.

    Safe when there is no prior data (case D2): `pct_change` is `None` and
    `has_prior` is `False` rather than raising.
    """
    anchor = cal.to_date(as_of) if as_of is not None else date.today()
    with optional_connection(conn, db_path) as c:
        cur_start, cur_end = _period_bounds(period, anchor, c, db_path)
        prev_start, prev_end = _period_bounds(
            period, cur_start - timedelta(days=1), c, db_path
        )
        # Current period is to-date (capped at the anchor); the previous period
        # is complete, so it is left uncapped.
        current = period_stats(cur_start, cur_end, as_of=anchor, conn=c)
        previous = period_stats(prev_start, prev_end, conn=c)

    worked_diff = current.worked_minutes - previous.worked_minutes
    has_prior = previous.worked_minutes > 0
    pct_change = (
        round(worked_diff / previous.worked_minutes * 100, 1) if has_prior else None
    )
    completion_diff = (
        round(current.completion_pct - previous.completion_pct, 1)
        if current.completion_pct is not None and previous.completion_pct is not None
        else None
    )

    return Comparison(
        period=period,
        current=current,
        previous=previous,
        worked_diff_minutes=worked_diff,
        completion_diff_pct=completion_diff,
        pct_change=pct_change,
        has_prior=has_prior,
    )


def month_stats(
    in_month: str | date,
    *,
    as_of: str | date | None = None,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> PeriodStats:
    """Stats for the month containing ``in_month`` (capped at ``as_of`` if set)."""
    first, last = cal.month_bounds(in_month)
    return period_stats(first, last, as_of=as_of, conn=conn, db_path=db_path)


def week_stats(
    in_week: str | date,
    *,
    as_of: str | date | None = None,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> PeriodStats:
    """Stats for the week containing ``in_week`` (capped at ``as_of`` if set)."""
    first, last = cal.week_bounds(in_week, conn=conn, db_path=db_path)
    return period_stats(first, last, as_of=as_of, conn=conn, db_path=db_path)
