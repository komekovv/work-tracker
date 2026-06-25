"""Worktime data model — the ``sessions`` and ``targets`` tables.

These are **worktime-owned** tables (the module registers them itself via its
``register`` hook). They run after core's migrations, so the shared ``settings``
table already exists when this module seeds into it.

``sessions`` records one row per power-on→power-off span. Some columns are
*intrinsic* to the session and written by the detector (``date``,
``start_time``, ``end_time``, ``duration_minutes``, ``is_sunday``,
``last_heartbeat``, ``source``). Others are **calc-derived and dynamic**
(``daily_target_hours``, ``is_holiday``, ``is_bonus``) — they depend on targets
and day-types that can change retroactively, so they are left NULLable here and
owned by the calc layer (Phase 3), not snapshotted at write time.

``targets`` stores **historical** target rules: each row is effective from a
date, optionally scoped to a weekday ("short days"). Which row applies to a
given day (cases A1–A4) is resolved by the calc layer (Phase 3); this module
only stores and lists them.

Durations are stored in **minutes** (integers) to avoid float artifacts (D5).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from backend.core import calendar as cal
from backend.core.db import optional_connection

# How a session row came to exist.
SESSION_SOURCES = ("auto", "manual", "crash-recovered")

# Target cadence.
TARGET_PERIODS = ("daily", "weekly")


def _in_list(values: tuple[str, ...]) -> str:
    """Render a tuple as a SQL IN-list literal, e.g. ('auto','manual')."""
    return ", ".join("'%s'" % v for v in values)


def create_sessions(conn: sqlite3.Connection) -> None:
    """Work-session table + lookup indexes."""
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS sessions (
            id                 INTEGER PRIMARY KEY,
            date               TEXT    NOT NULL,              -- start day 'YYYY-MM-DD'
            start_time         TEXT    NOT NULL,              -- ISO timestamp
            end_time           TEXT,                          -- NULL while open
            duration_minutes   INTEGER,                       -- NULL while open
            daily_target_hours REAL,                          -- calc-owned (Phase 3)
            is_sunday          INTEGER NOT NULL DEFAULT 0 CHECK (is_sunday IN (0, 1)),
            is_holiday         INTEGER CHECK (is_holiday IN (0, 1)),   -- calc-owned
            is_bonus           INTEGER CHECK (is_bonus IN (0, 1)),     -- calc-owned
            last_heartbeat     TEXT,                          -- ISO timestamp
            source             TEXT    NOT NULL
                                 CHECK (source IN ({_in_list(SESSION_SOURCES)}))
        )
        """
    )
    # Sessions are queried by day (daily totals, calendar).
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(date)"
    )
    # Partial index makes orphan lookup (end_time IS NULL) cheap.
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_sessions_open "
        "ON sessions(end_time) WHERE end_time IS NULL"
    )


def create_targets(conn: sqlite3.Connection) -> None:
    """Historical target-rule table.

    ``weekday`` is NULL for the base (all-days) rule, or 0–6 (Mon=0…Sun=6,
    matching core.calendar) for a per-weekday override.
    """
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS targets (
            id             INTEGER PRIMARY KEY,
            effective_from TEXT    NOT NULL,                  -- 'YYYY-MM-DD'
            period         TEXT    NOT NULL
                             CHECK (period IN ({_in_list(TARGET_PERIODS)})),
            weekday        INTEGER CHECK (weekday IS NULL OR (weekday BETWEEN 0 AND 6)),
            daily_hours    REAL    NOT NULL
        )
        """
    )
    # Resolution scans by effective_from (most recent on/before a date).
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_targets_effective "
        "ON targets(effective_from)"
    )


# Module-owned defaults, namespaced to avoid collisions in the shared settings
# table. The detector heartbeat interval lives here (not in core) because it is
# worktime-specific.
_DEFAULT_SETTINGS = {
    "worktime.heartbeat_seconds": "60",
}


def seed_settings(conn: sqlite3.Connection) -> None:
    """Seed worktime defaults into the shared core ``settings`` table."""
    conn.executemany(
        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
        list(_DEFAULT_SETTINGS.items()),
    )


# Order: tables before the seed that writes into settings.
WORKTIME_MIGRATIONS = (create_sessions, create_targets, seed_settings)


# ===========================================================================
# Session data access
# ===========================================================================
#
# These functions are the only writers/readers of the `sessions` table. The
# detector (Step 5) drives open → heartbeat → close; orphan recovery (Step 3)
# adds the crash path. Timestamps are stored as second-precision ISO strings;
# durations are integer minutes (D5). The `date` column is the **start day**,
# so a session that crosses midnight belongs to the day it began (B2).


@dataclass(frozen=True)
class Session:
    """A row from the `sessions` table.

    `is_holiday` / `is_bonus` are `None` until the calc layer (Phase 3) fills
    them; `is_sunday` is intrinsic and always set.
    """

    id: int
    date: str
    start_time: str
    end_time: str | None
    duration_minutes: int | None
    daily_target_hours: float | None
    is_sunday: bool
    is_holiday: bool | None
    is_bonus: bool | None
    last_heartbeat: str | None
    source: str


def _opt_bool(value: int | None) -> bool | None:
    """Preserve NULL (unknown) while coercing 0/1 to bool."""
    return None if value is None else bool(value)


def _row_to_session(row: sqlite3.Row) -> Session:
    return Session(
        id=row["id"],
        date=row["date"],
        start_time=row["start_time"],
        end_time=row["end_time"],
        duration_minutes=row["duration_minutes"],
        daily_target_hours=row["daily_target_hours"],
        is_sunday=bool(row["is_sunday"]),
        is_holiday=_opt_bool(row["is_holiday"]),
        is_bonus=_opt_bool(row["is_bonus"]),
        last_heartbeat=row["last_heartbeat"],
        source=row["source"],
    )


def _iso(moment: datetime) -> str:
    """Serialize a datetime to a second-precision ISO string."""
    return moment.isoformat(timespec="seconds")


def duration_minutes_between(start_iso: str, end_iso: str) -> int:
    """Whole minutes between two ISO timestamps, clamped at 0."""
    start = datetime.fromisoformat(start_iso)
    end = datetime.fromisoformat(end_iso)
    return max(0, round((end - start).total_seconds() / 60))


def open_session(
    start_time: datetime | None = None,
    *,
    source: str = "auto",
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> int:
    """Open a new session and return its id.

    `last_heartbeat` is seeded to the start time so that a crash before the
    first heartbeat still has a sane recovery point (Step 3).
    """
    start = start_time or datetime.now()
    start_iso = _iso(start)
    with optional_connection(conn, db_path) as c:
        cur = c.execute(
            """
            INSERT INTO sessions (date, start_time, last_heartbeat, is_sunday, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                start.date().isoformat(),  # start-day attribution (B2)
                start_iso,
                start_iso,
                1 if cal.is_sunday(start.date()) else 0,
                source,
            ),
        )
        return int(cur.lastrowid)


def update_heartbeat(
    session_id: int,
    when: datetime | None = None,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> bool:
    """Advance `last_heartbeat` for an **open** session.

    Returns False if the session is unknown or already closed (closed sessions
    are never heartbeated).
    """
    beat = _iso(when or datetime.now())
    with optional_connection(conn, db_path) as c:
        cur = c.execute(
            "UPDATE sessions SET last_heartbeat = ? "
            "WHERE id = ? AND end_time IS NULL",
            (beat, session_id),
        )
        return cur.rowcount > 0


def close_session(
    session_id: int,
    end_time: datetime | None = None,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> bool:
    """Close an open session, computing `duration_minutes`.

    Returns False if the session is unknown or already closed — a DB-level
    **double-close guard** that backs up the detector's in-process flag.
    """
    end = end_time or datetime.now()
    end_iso = _iso(end)
    with optional_connection(conn, db_path) as c:
        row = c.execute(
            "SELECT start_time FROM sessions WHERE id = ? AND end_time IS NULL",
            (session_id,),
        ).fetchone()
        if row is None:
            return False
        duration = duration_minutes_between(row["start_time"], end_iso)
        c.execute(
            "UPDATE sessions SET end_time = ?, duration_minutes = ? WHERE id = ?",
            (end_iso, duration, session_id),
        )
        return True


def get_session(
    session_id: int,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> Session | None:
    """Fetch a single session by id, or None."""
    with optional_connection(conn, db_path) as c:
        row = c.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
    return _row_to_session(row) if row is not None else None


def get_open_sessions(
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> list[Session]:
    """All sessions still open (`end_time IS NULL`), oldest first."""
    with optional_connection(conn, db_path) as c:
        rows = c.execute(
            "SELECT * FROM sessions WHERE end_time IS NULL ORDER BY start_time"
        ).fetchall()
    return [_row_to_session(r) for r in rows]


def get_sessions_by_date(
    day: str | date,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> list[Session]:
    """All sessions whose start day is `day`, in start order (B1: many/day)."""
    iso_day = cal.to_date(day).isoformat()
    with optional_connection(conn, db_path) as c:
        rows = c.execute(
            "SELECT * FROM sessions WHERE date = ? ORDER BY start_time",
            (iso_day,),
        ).fetchall()
    return [_row_to_session(r) for r in rows]


def get_sessions_between(
    start: str | date,
    end: str | date,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> list[Session]:
    """All sessions whose start day is within the inclusive ``[start, end]``.

    Dates are zero-padded ISO, so the lexicographic range matches chronological.
    """
    s = cal.to_date(start).isoformat()
    e = cal.to_date(end).isoformat()
    with optional_connection(conn, db_path) as c:
        rows = c.execute(
            "SELECT * FROM sessions WHERE date BETWEEN ? AND ? "
            "ORDER BY date, start_time",
            (s, e),
        ).fetchall()
    return [_row_to_session(r) for r in rows]


# Sentinel "end" for an open session when testing interval overlap: an open
# session occupies [start, ∞), so it overlaps anything starting after it.
_OPEN_END_SENTINEL = "9999-12-31T23:59:59"


def find_overlapping(
    start: datetime,
    end: datetime,
    *,
    exclude_id: int | None = None,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> list[Session]:
    """Sessions whose time interval overlaps ``[start, end]`` (case B6).

    Uses strict inequalities so back-to-back sessions (one ends exactly when the
    next begins) do **not** count as overlapping. Open sessions are treated as
    ongoing via a sentinel end. ``exclude_id`` skips a row (used when editing).
    """
    start_iso, end_iso = _iso(start), _iso(end)
    sql = (
        "SELECT * FROM sessions "
        "WHERE start_time < ? "
        f"AND COALESCE(end_time, '{_OPEN_END_SENTINEL}') > ?"
    )
    params: list[object] = [end_iso, start_iso]
    if exclude_id is not None:
        sql += " AND id != ?"
        params.append(exclude_id)
    with optional_connection(conn, db_path) as c:
        rows = c.execute(sql + " ORDER BY start_time", params).fetchall()
    return [_row_to_session(r) for r in rows]


def create_session(
    start: datetime,
    end: datetime | None = None,
    *,
    source: str = "manual",
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> int:
    """Insert a manual session and return its id.

    ``end`` may be ``None`` to create an **open** session (a manual clock-in with
    no end yet) — `end_time`/`duration_minutes` stay NULL. Caller is responsible
    for overlap checks (see :func:`find_overlapping`).
    """
    start_iso = _iso(start)
    end_iso = _iso(end) if end is not None else None
    duration = (
        duration_minutes_between(start_iso, end_iso) if end_iso is not None else None
    )
    with optional_connection(conn, db_path) as c:
        cur = c.execute(
            """
            INSERT INTO sessions
                (date, start_time, end_time, duration_minutes, is_sunday, source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                start.date().isoformat(),
                start_iso,
                end_iso,
                duration,
                1 if cal.is_sunday(start.date()) else 0,
                source,
            ),
        )
        return int(cur.lastrowid)


def delete_session(
    session_id: int,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> bool:
    """Delete a session by id. Returns True if a row was removed."""
    with optional_connection(conn, db_path) as c:
        cur = c.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return cur.rowcount > 0


def edit_session(
    session_id: int,
    *,
    start: datetime | None = None,
    end: datetime | None = None,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> Session | None:
    """Update a session's start and/or end; recompute derived fields.

    Returns the updated `Session`, or `None` if the id doesn't exist. If the
    final session is still open (no end), `duration_minutes` stays NULL.
    Changing the start re-derives `date` and `is_sunday` (start-day attribution).
    """
    with optional_connection(conn, db_path) as c:
        existing = c.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if existing is None:
            return None

        start_iso = _iso(start) if start is not None else existing["start_time"]
        if end is not None:
            end_iso: str | None = _iso(end)
        else:
            end_iso = existing["end_time"]

        start_date = datetime.fromisoformat(start_iso).date()
        duration = (
            duration_minutes_between(start_iso, end_iso)
            if end_iso is not None
            else None
        )
        c.execute(
            "UPDATE sessions SET start_time = ?, end_time = ?, "
            "duration_minutes = ?, date = ?, is_sunday = ? WHERE id = ?",
            (
                start_iso,
                end_iso,
                duration,
                start_date.isoformat(),
                1 if cal.is_sunday(start_date) else 0,
                session_id,
            ),
        )
        row = c.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
    return _row_to_session(row)


def recover_orphans(
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> list[int]:
    """Close sessions left open by a crash / power-loss and return their ids.

    On an unclean shutdown no SIGTERM arrives, so the session row keeps
    `end_time IS NULL`. Each such orphan is closed at its **last heartbeat**
    (NOT the current time), flagged `source='crash-recovered'`, with
    `duration_minutes` computed to that heartbeat. This caps the error at about
    one heartbeat interval (case B3).

    Must run on boot **before** opening the new session, otherwise the fresh
    session would be swept up as an orphan. The `last_heartbeat` defensively
    falls back to `start_time` (a crash before the first heartbeat → ~0
    duration), though `open_session` always seeds a heartbeat.
    """
    recovered: list[int] = []
    with optional_connection(conn, db_path) as c:
        rows = c.execute(
            "SELECT id, start_time, last_heartbeat "
            "FROM sessions WHERE end_time IS NULL"
        ).fetchall()
        for row in rows:
            end_iso = row["last_heartbeat"] or row["start_time"]
            duration = duration_minutes_between(row["start_time"], end_iso)
            c.execute(
                "UPDATE sessions SET end_time = ?, duration_minutes = ?, "
                "source = 'crash-recovered' WHERE id = ?",
                (end_iso, duration, row["id"]),
            )
            recovered.append(row["id"])
    return recovered


# ===========================================================================
# Target data access
# ===========================================================================
#
# Targets are **historical, append-by-date** rules. Each row is effective from a
# date, optionally scoped to a weekday ("short days"). This layer only stores
# and lists them; deciding which row applies to a given day (the most recent
# effective_from on/before the day, weekday override beating the base — cases
# A1–A4) is the calc layer's job (Phase 3).


@dataclass(frozen=True)
class Target:
    """A row from the `targets` table.

    `weekday` is None for the base (all-days) rule, or 0–6 (Mon=0…Sun=6) for a
    per-weekday override.
    """

    id: int
    effective_from: str
    period: str
    weekday: int | None
    daily_hours: float


def _row_to_target(row: sqlite3.Row) -> Target:
    return Target(
        id=row["id"],
        effective_from=row["effective_from"],
        period=row["period"],
        weekday=row["weekday"],
        daily_hours=row["daily_hours"],
    )


def set_target(
    effective_from: str | date,
    daily_hours: float,
    *,
    period: str = "daily",
    weekday: int | None = None,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> int:
    """Create (or replace) a target rule and return its id.

    Re-setting the same `(effective_from, period, weekday)` key replaces that
    rule (so corrections don't leave ambiguous duplicates); a different
    `effective_from` adds a new historical row (case A1 — past days keep their
    old target).
    """
    if period not in TARGET_PERIODS:
        raise ValueError(f"Unknown period {period!r}; expected one of {TARGET_PERIODS}")
    if weekday is not None:
        if isinstance(weekday, bool) or not isinstance(weekday, int):
            raise TypeError("weekday must be an int 0-6 or None")
        if not 0 <= weekday <= 6:
            raise ValueError(f"weekday out of range: {weekday}")
    if daily_hours < 0:
        raise ValueError(f"daily_hours must be >= 0, got {daily_hours}")

    eff = cal.to_date(effective_from).isoformat()
    with optional_connection(conn, db_path) as c:
        # Replace any existing rule with the same key (NULL weekday handled
        # explicitly since NULL != NULL in SQL).
        if weekday is None:
            c.execute(
                "DELETE FROM targets WHERE effective_from = ? AND period = ? "
                "AND weekday IS NULL",
                (eff, period),
            )
        else:
            c.execute(
                "DELETE FROM targets WHERE effective_from = ? AND period = ? "
                "AND weekday = ?",
                (eff, period, weekday),
            )
        cur = c.execute(
            "INSERT INTO targets (effective_from, period, weekday, daily_hours) "
            "VALUES (?, ?, ?, ?)",
            (eff, period, weekday, daily_hours),
        )
        return int(cur.lastrowid)


def list_targets(
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> list[Target]:
    """All target rules, ordered by effective_from then weekday (base first)."""
    with optional_connection(conn, db_path) as c:
        rows = c.execute(
            "SELECT * FROM targets ORDER BY effective_from, weekday, id"
        ).fetchall()
    return [_row_to_target(r) for r in rows]


def get_target(
    target_id: int,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> Target | None:
    """Fetch a target rule by id, or None."""
    with optional_connection(conn, db_path) as c:
        row = c.execute(
            "SELECT * FROM targets WHERE id = ?", (target_id,)
        ).fetchone()
    return _row_to_target(row) if row is not None else None


def delete_target(
    target_id: int,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> bool:
    """Delete a target rule by id. Returns True if a row was removed."""
    with optional_connection(conn, db_path) as c:
        cur = c.execute("DELETE FROM targets WHERE id = ?", (target_id,))
        return cur.rowcount > 0
