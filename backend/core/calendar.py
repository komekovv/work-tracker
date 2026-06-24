"""Shared date / calendar helpers.

Used across the app (KPI periods, the calendar page, stats grouping). Keeps one
canonical answer to "what week/month is this date in?" and "what weekday is it?".

**Weekday convention:** Python's native ``date.weekday()`` — **Monday = 0 …
Sunday = 6**. This is the index the ``targets.weekday`` column (plan §4) uses,
so per-weekday target overrides line up with these helpers.

Week boundaries honour the dynamic ``week_start_day`` setting, but the module
stays usable as pure date math: if no DB/connection is supplied, the week starts
on Monday by default.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path

from backend.core import config

# Monday = 0 … Sunday = 6 (matches date.weekday()).
SUNDAY = 6

_WEEKDAY_NAMES = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def to_date(value: str | date) -> date:
    """Coerce an ISO 'YYYY-MM-DD' string or a ``date`` to a ``date``."""
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def weekday(value: str | date) -> int:
    """Weekday index, Monday = 0 … Sunday = 6."""
    return to_date(value).weekday()


def is_sunday(value: str | date) -> bool:
    """True if the date is a Sunday (relevant to bonus rules, plan §5)."""
    return to_date(value).weekday() == SUNDAY


def resolve_week_start(
    week_start: int | str | None = None,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> int:
    """Resolve the week-start weekday index (Mon=0 … Sun=6).

    Precedence: an explicit ``week_start`` (int 0–6 or day name) wins; else the
    ``week_start_day`` setting is read when a DB is available; else Monday (0).
    """
    if week_start is not None:
        if isinstance(week_start, bool):  # guard: bool is an int subclass
            raise TypeError("week_start must be an int 0-6 or a day name")
        if isinstance(week_start, int):
            if not 0 <= week_start <= 6:
                raise ValueError(f"week_start out of range: {week_start}")
            return week_start
        name = week_start.strip().lower()
        if name not in _WEEKDAY_NAMES:
            raise ValueError(f"Unknown week_start day name: {week_start!r}")
        return _WEEKDAY_NAMES[name]

    if conn is not None or db_path is not None:
        raw = config.get("week_start_day", "monday", conn=conn, db_path=db_path)
        name = raw.strip().lower()
        if name in _WEEKDAY_NAMES:
            return _WEEKDAY_NAMES[name]
        if name.isdigit() and 0 <= int(name) <= 6:
            return int(name)
        raise ValueError(f"Invalid week_start_day setting: {raw!r}")

    return 0  # default: Monday


def week_bounds(
    value: str | date,
    *,
    week_start: int | str | None = None,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> tuple[date, date]:
    """Return the ``(start, end)`` dates of the week containing ``value``.

    The week spans 7 days starting on the resolved week-start weekday.
    """
    d = to_date(value)
    ws = resolve_week_start(week_start, conn=conn, db_path=db_path)
    offset = (d.weekday() - ws) % 7
    start = d - timedelta(days=offset)
    return start, start + timedelta(days=6)


def month_bounds(value: str | date) -> tuple[date, date]:
    """Return the ``(first, last)`` dates of the month containing ``value``."""
    d = to_date(value)
    first = d.replace(day=1)
    if d.month == 12:
        next_first = date(d.year + 1, 1, 1)
    else:
        next_first = date(d.year, d.month + 1, 1)
    return first, next_first - timedelta(days=1)


def iter_days(start: str | date, end: str | date) -> Iterator[date]:
    """Yield each date from ``start`` to ``end`` inclusive.

    Yields nothing if ``end`` is before ``start``.
    """
    current = to_date(start)
    last = to_date(end)
    while current <= last:
        yield current
        current += timedelta(days=1)


def days_in_range(start: str | date, end: str | date) -> list[date]:
    """Materialised inclusive list of dates from ``start`` to ``end``."""
    return list(iter_days(start, end))
