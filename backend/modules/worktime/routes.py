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

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from backend.api.deps import get_db_path
from backend.core import calendar as cal
from backend.core import db as core_db
from backend.modules.worktime import calc, kpi, models
from backend.modules.worktime.schemas import (
    CalendarOut,
    ComparisonOut,
    DayResultOut,
    KpiOut,
    ManualSessionIn,
    PeriodStatsOut,
    SessionEditIn,
    SessionOut,
    StatsOut,
    TargetIn,
    TargetOut,
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
        # Cap the current period at the anchor → week/month-to-date.
        if period == "week":
            current = kpi.week_stats(anchor, as_of=anchor, conn=conn)
        else:
            current = kpi.month_stats(anchor, as_of=anchor, conn=conn)
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
        month = kpi.month_stats(anchor, as_of=anchor, conn=conn)  # month-to-date
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


def _conflict_detail(conflicts: list) -> str:
    ids = ", ".join(str(s.id) for s in conflicts)
    return f"Session overlaps existing session(s): {ids}"


@router.post("/sessions/manual", response_model=SessionOut, status_code=201)
def create_manual_session(
    payload: ManualSessionIn,
    db_path: Path = Depends(get_db_path),
) -> SessionOut:
    """Add a manual session (clock-in/out). Rejects overlaps (B6) with 409."""
    if payload.start_time >= payload.end_time:
        raise HTTPException(status_code=422, detail="start_time must be before end_time")
    with core_db.connection(db_path) as conn:
        conflicts = models.find_overlapping(
            payload.start_time, payload.end_time, conn=conn
        )
        if conflicts:
            raise HTTPException(status_code=409, detail=_conflict_detail(conflicts))
        session_id = models.create_session(
            payload.start_time, payload.end_time, source="manual", conn=conn
        )
        created = models.get_session(session_id, conn=conn)
    return SessionOut.model_validate(created)


@router.patch("/sessions/{session_id}", response_model=SessionOut)
def edit_session(
    session_id: int,
    payload: SessionEditIn,
    db_path: Path = Depends(get_db_path),
) -> SessionOut:
    """Edit a session's start/end (e.g. fix a crash day). 404/409 as needed."""
    with core_db.connection(db_path) as conn:
        existing = models.get_session(session_id, conn=conn)
        if existing is None:
            raise HTTPException(status_code=404, detail="Session not found")

        new_start = payload.start_time or datetime.fromisoformat(existing.start_time)
        if payload.end_time is not None:
            new_end: datetime | None = payload.end_time
        elif existing.end_time is not None:
            new_end = datetime.fromisoformat(existing.end_time)
        else:
            new_end = None

        if new_end is not None and new_start >= new_end:
            raise HTTPException(status_code=422, detail="start_time must be before end_time")

        # Open sessions extend to +∞ for overlap purposes.
        overlap_end = new_end or datetime.max.replace(microsecond=0)
        conflicts = models.find_overlapping(
            new_start, overlap_end, exclude_id=session_id, conn=conn
        )
        if conflicts:
            raise HTTPException(status_code=409, detail=_conflict_detail(conflicts))

        updated = models.edit_session(
            session_id, start=payload.start_time, end=payload.end_time, conn=conn
        )
    return SessionOut.model_validate(updated)


@router.post("/target", response_model=TargetOut, status_code=201)
def set_target(
    payload: TargetIn,
    db_path: Path = Depends(get_db_path),
) -> TargetOut:
    """Create or change a target rule (historical; replace-on-same-key)."""
    with core_db.connection(db_path) as conn:
        target_id = models.set_target(
            payload.effective_from,
            payload.daily_hours,
            period=payload.period,
            weekday=payload.weekday,
            conn=conn,
        )
        created = models.get_target(target_id, conn=conn)
    return TargetOut.model_validate(created)


@router.get("/targets", response_model=list[TargetOut])
def list_targets(db_path: Path = Depends(get_db_path)) -> list[TargetOut]:
    """All target rules (for the settings UI)."""
    rows = models.list_targets(db_path=db_path)
    return [TargetOut.model_validate(t) for t in rows]


@router.delete("/target/{target_id}", status_code=204)
def delete_target(
    target_id: int,
    db_path: Path = Depends(get_db_path),
) -> Response:
    """Delete a target rule by id; 404 if it doesn't exist."""
    if not models.delete_target(target_id, db_path=db_path):
        raise HTTPException(status_code=404, detail="Target not found")
    return Response(status_code=204)
