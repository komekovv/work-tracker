"""Shared day-type logic.

A *day type* marks a calendar date as a workday, holiday, leave, or vacation.
It is core (not worktime) because day types affect every module's notion of
what a date *means*. This module is the single place that:

- validates the type against the enum and normalises dates to 'YYYY-MM-DD',
- chooses a sensible ``affects_target`` default per type,
- enforces **case C4 — manual wins over planned**: a pre-planned marking
  (``planned=True``) must never overwrite one the user set manually
  (``planned=False``); the user is the final decision-maker.

The calc layer (Phase 3) reads these rows; it does not re-implement the rules.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date as _date
from pathlib import Path

from backend.core.db import optional_connection
from backend.core.migrations import DAY_TYPES

# Named constants for the enum (single source of truth is migrations.DAY_TYPES).
WORKDAY = "workday"
HOLIDAY = "holiday"
LEAVE = "leave"
VACATION = "vacation"

# Day types that, by default, override the normal target (they zero it and turn
# worked hours into bonus — see plan §5). A plain "workday" override does not.
_TARGET_OVERRIDING = frozenset({HOLIDAY, LEAVE, VACATION})


@dataclass(frozen=True)
class DayType:
    """A single day's marking, as stored in ``day_types``."""

    date: str
    type: str
    name: str | None
    planned: bool
    affects_target: bool


def default_affects_target(day_type: str) -> bool:
    """Whether a day type overrides the target by default.

    Special days (holiday/leave/vacation) → True; workday → False. Callers can
    still pass an explicit value to override this default.
    """
    return day_type in _TARGET_OVERRIDING


def _normalize_date(value: str | _date) -> str:
    """Coerce a date or ISO string to a validated 'YYYY-MM-DD' string."""
    if isinstance(value, _date):
        return value.isoformat()
    # fromisoformat validates the shape and the calendar (e.g. rejects 2026-13-40)
    return _date.fromisoformat(value).isoformat()


def _row_to_day_type(row: sqlite3.Row) -> DayType:
    return DayType(
        date=row["date"],
        type=row["type"],
        name=row["name"],
        planned=bool(row["planned"]),
        affects_target=bool(row["affects_target"]),
    )


def get_day_type(
    date: str | _date,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> DayType | None:
    """Return the marking for ``date``, or ``None`` if the date is unmarked."""
    d = _normalize_date(date)
    with optional_connection(conn, db_path) as c:
        row = c.execute("SELECT * FROM day_types WHERE date = ?", (d,)).fetchone()
    return _row_to_day_type(row) if row is not None else None


def set_day_type(
    date: str | _date,
    day_type: str,
    *,
    name: str | None = None,
    planned: bool = False,
    affects_target: bool | None = None,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> DayType:
    """Create or update a day-type marking and return the effective row.

    **Case C4:** if this is a *planned* write (``planned=True``) and a *manual*
    marking already exists for the date, the write is skipped — the manual
    marking wins — and the existing row is returned unchanged. Every other
    combination upserts normally (in particular, a manual write always
    overwrites a planned one).

    ``affects_target`` defaults via :func:`default_affects_target` when not given.
    """
    d = _normalize_date(date)
    if day_type not in DAY_TYPES:
        raise ValueError(
            f"Unknown day type {day_type!r}; expected one of {DAY_TYPES}"
        )
    effective_affects = (
        default_affects_target(day_type)
        if affects_target is None
        else bool(affects_target)
    )

    with optional_connection(conn, db_path) as c:
        existing = c.execute(
            "SELECT * FROM day_types WHERE date = ?", (d,)
        ).fetchone()

        # C4: a planned write must not clobber a manual marking.
        if existing is not None and planned and existing["planned"] == 0:
            return _row_to_day_type(existing)

        c.execute(
            """
            INSERT INTO day_types (date, type, name, planned, affects_target)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                type = excluded.type,
                name = excluded.name,
                planned = excluded.planned,
                affects_target = excluded.affects_target
            """,
            (d, day_type, name, 1 if planned else 0, 1 if effective_affects else 0),
        )
        row = c.execute("SELECT * FROM day_types WHERE date = ?", (d,)).fetchone()
    return _row_to_day_type(row)


def delete_day_type(
    date: str | _date,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> bool:
    """Remove a marking. Returns True if a row was deleted, else False."""
    d = _normalize_date(date)
    with optional_connection(conn, db_path) as c:
        cur = c.execute("DELETE FROM day_types WHERE date = ?", (d,))
        return cur.rowcount > 0


def list_day_types(
    start: str | _date,
    end: str | _date,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> list[DayType]:
    """Return markings within the inclusive ``[start, end]`` date range.

    Dates are stored as zero-padded ISO strings, so lexicographic `BETWEEN`
    ordering matches chronological ordering.
    """
    s = _normalize_date(start)
    e = _normalize_date(end)
    with optional_connection(conn, db_path) as c:
        rows = c.execute(
            "SELECT * FROM day_types WHERE date BETWEEN ? AND ? ORDER BY date",
            (s, e),
        ).fetchall()
    return [_row_to_day_type(r) for r in rows]
