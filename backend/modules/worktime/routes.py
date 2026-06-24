"""Worktime HTTP routes.

Mounted via the registry (worktime's `router_factory`). This file holds the
read side; writes (manual session, edit, target) are added next. Handlers take
the DB path via dependency and reuse one connection per request where they loop
over many days.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import get_db_path
from backend.core import calendar as cal
from backend.core import db as core_db
from backend.modules.worktime import calc, kpi, models
from backend.modules.worktime.schemas import (
    CalendarOut,
    ComparisonOut,
    DayResultOut,
    KpiOut,
    PeriodStatsOut,
    SessionOut,
    StatsOut,
    TodayOut,
)

router = APIRouter(prefix="/api/worktime", tags=["worktime"])


def _elapsed_minutes(start_iso: str, now: datetime) -> int:
    return max(0, round((now - datetime.fromisoformat(start_iso)).total_seconds() / 60))


@router.get("/today", response_model=TodayOut)
def today(db_path: Path = Depends(get_db_path)) -> TodayOut:
    """Today's computed status, including any in-progress session's elapsed."""
    now = datetime.now()
    today_iso = now.date().isoformat()
    with core_db.connection(db_path) as conn:
        result = calc.compute_day(today_iso, conn=conn)
        open_sessions = models.get_open_sessions(conn=conn)

    # The most recent open session is the "active" one (normally there is ≤ 1).
    active = open_sessions[-1] if open_sessions else None
    active_out = None
    live_extra = 0
    if active is not None:
        elapsed = _elapsed_minutes(active.start_time, now)
        active_out = {
            "id": active.id,
            "start_time": active.start_time,
            "last_heartbeat": active.last_heartbeat,
            "elapsed_minutes": elapsed,
        }
        # Only add to *today's* live total if the open session began today (B2).
        if active.date == today_iso:
            live_extra = elapsed

    worked_live = result.worked_minutes + live_extra
    return TodayOut(
        date=result.date,
        day_type=result.day_type,
        is_sunday=result.is_sunday,
        target_minutes=result.target_minutes,
        worked_minutes=result.worked_minutes,
        worked_minutes_live=worked_live,
        over_under_minutes=worked_live - result.target_minutes,
        is_bonus=result.is_bonus,
        bonus_minutes=result.bonus_minutes,
        target_met=result.target_met,
        active_session=active_out,
    )


@router.get("/stats", response_model=StatsOut)
def stats(
    period: Literal["week", "month"] = "week",
    as_of: date | None = None,
    n: int = Query(6, ge=1, le=52),
    db_path: Path = Depends(get_db_path),
) -> StatsOut:
    """Current period totals plus the last ``n`` periods as a trend."""
    anchor = as_of or date.today()
    with core_db.connection(db_path) as conn:
        if period == "week":
            current = kpi.week_stats(anchor, conn=conn)
        else:
            current = kpi.month_stats(anchor, conn=conn)
        trend = kpi.trend(period, n, anchor, conn=conn)

    return StatsOut(
        period=period,
        as_of=anchor.isoformat(),
        stats=PeriodStatsOut.model_validate(current),
        trend=[PeriodStatsOut.model_validate(p) for p in trend],
    )


@router.get("/kpi", response_model=KpiOut)
def kpi_metrics(
    as_of: date | None = None,
    db_path: Path = Depends(get_db_path),
) -> KpiOut:
    """Headline KPIs: streak, current month stats, month-over-month comparison."""
    anchor = as_of or date.today()
    with core_db.connection(db_path) as conn:
        month = kpi.month_stats(anchor, conn=conn)
        streak = kpi.streak(anchor, conn=conn)
        comparison = kpi.compare("month", anchor, conn=conn)

    return KpiOut(
        as_of=anchor.isoformat(),
        streak=streak,
        month=PeriodStatsOut.model_validate(month),
        comparison=ComparisonOut.model_validate(comparison),
    )


@router.get("/sessions", response_model=list[SessionOut])
def sessions(
    frm: date | None = Query(None, alias="from"),
    to: date | None = None,
    db_path: Path = Depends(get_db_path),
) -> list[SessionOut]:
    """Sessions whose start day falls in [from, to] (defaults to this month)."""
    if frm is None or to is None:
        m_start, m_end = cal.month_bounds(date.today())
        frm = frm or m_start
        to = to or m_end
    rows = models.get_sessions_between(frm, to, db_path=db_path)
    return [SessionOut.model_validate(s) for s in rows]


@router.get("/calendar", response_model=CalendarOut)
def calendar(
    month: str | None = None,
    db_path: Path = Depends(get_db_path),
) -> CalendarOut:
    """Per-day results for a month (``month`` as 'YYYY-MM', default current)."""
    if month is None:
        anchor = date.today()
    else:
        try:
            anchor = datetime.strptime(month, "%Y-%m").date()
        except ValueError:
            raise HTTPException(status_code=422, detail="month must be 'YYYY-MM'")

    first, last = cal.month_bounds(anchor)
    with core_db.connection(db_path) as conn:
        days = [
            DayResultOut.model_validate(calc.compute_day(d, conn=conn))
            for d in cal.iter_days(first, last)
        ]
    return CalendarOut(month=first.strftime("%Y-%m"), days=days)
