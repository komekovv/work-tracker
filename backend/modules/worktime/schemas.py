"""Pydantic response schemas for the worktime API.

All durations are **minutes** (raw integers); the frontend formats hours for
display. Most schemas mirror the calc/kpi/models dataclasses and are built from
them via `from_attributes`, so the API shape tracks the domain types.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ManualSessionIn(BaseModel):
    """Request body for a manual clock-in/out (both ends required)."""

    start_time: datetime
    end_time: datetime


class SessionEditIn(BaseModel):
    """Partial edit of a session — supply start, end, or both."""

    start_time: datetime | None = None
    end_time: datetime | None = None


class TargetIn(BaseModel):
    """Request body for setting/changing a target rule."""

    effective_from: date
    daily_hours: float = Field(ge=0)
    period: Literal["daily", "weekly"] = "daily"
    weekday: int | None = Field(default=None, ge=0, le=6)


class TargetOut(BaseModel):
    """A stored target rule."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    effective_from: str
    period: str
    weekday: int | None
    daily_hours: float


class SessionOut(BaseModel):
    """A recorded work session (subset of columns relevant to clients)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    date: str
    start_time: str
    end_time: str | None
    duration_minutes: int | None
    is_sunday: bool
    last_heartbeat: str | None
    source: str


class DayResultOut(BaseModel):
    """One day's computed picture (used by /today and /calendar)."""

    model_config = ConfigDict(from_attributes=True)

    date: str
    day_type: str
    is_sunday: bool
    worked_minutes: int
    target_minutes: int
    over_under_minutes: int
    is_bonus: bool
    bonus_minutes: int
    target_met: bool | None


class PeriodStatsOut(BaseModel):
    """Aggregated stats for a date range."""

    model_config = ConfigDict(from_attributes=True)

    start: str
    end: str
    days: int
    worked_minutes: int
    worked_toward_target_minutes: int
    target_minutes: int
    bonus_minutes: int
    over_under_minutes: int
    completion_pct: float | None
    days_worked: int
    days_counted: int
    days_met: int
    average_worked_minutes: float | None


class ComparisonOut(BaseModel):
    """Period-over-period comparison."""

    model_config = ConfigDict(from_attributes=True)

    period: str
    current: PeriodStatsOut
    previous: PeriodStatsOut
    worked_diff_minutes: int
    completion_diff_pct: float | None
    pct_change: float | None
    has_prior: bool


class ActiveSessionOut(BaseModel):
    """The currently-open session, with live elapsed time."""

    id: int
    start_time: str
    last_heartbeat: str | None
    elapsed_minutes: int


class TodayOut(BaseModel):
    """Today's status: the computed day plus any in-progress session."""

    date: str
    day_type: str
    is_sunday: bool
    target_minutes: int
    worked_minutes: int            # recorded (closed) sessions today
    worked_minutes_live: int       # recorded + open session elapsed
    over_under_minutes: int        # based on live worked
    is_bonus: bool
    bonus_minutes: int
    target_met: bool | None
    active_session: ActiveSessionOut | None


class StatsOut(BaseModel):
    """Current period totals plus a trend series of the same period type."""

    period: str
    as_of: str
    stats: PeriodStatsOut
    trend: list[PeriodStatsOut]


class KpiOut(BaseModel):
    """Headline KPIs: streak, current month, month-over-month comparison."""

    as_of: str
    streak: int
    month: PeriodStatsOut
    comparison: ComparisonOut


class CalendarOut(BaseModel):
    """A month of per-day results for the calendar view."""

    month: str
    days: list[DayResultOut]
