"""Core table migrations and seed data.

Defines the two shared, core-owned tables from the plan (§4):

- ``settings`` — dynamic key-value config, so the app is reconfigurable without
  touching code. Values are stored as TEXT; typed access lives in
  ``core/config.py`` (Step 5).
- ``day_types`` — one row per calendar date marking it as workday / holiday /
  leave / vacation, set either in advance (``planned=1``) or manually
  (``planned=0``).

Each migration is idempotent (``CREATE TABLE IF NOT EXISTS`` /
``INSERT OR IGNORE``), so the registry can run them on every startup. DB-level
``CHECK`` constraints enforce the enums/flags so bad data can't be written even
by a buggy caller.
"""

from __future__ import annotations

import sqlite3

# Allowed day-type values, kept here as the single source of truth for the DB
# constraint. The shared day-type logic (Step 6) reuses these.
DAY_TYPES = ("workday", "holiday", "leave", "vacation")


def create_settings(conn: sqlite3.Connection) -> None:
    """Key-value settings table."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )


def create_day_types(conn: sqlite3.Connection) -> None:
    """Per-date day-type table.

    ``date`` is the PRIMARY KEY (text 'YYYY-MM-DD'), which gives the
    one-row-per-date uniqueness the plan calls for. ``affects_target`` lets a
    marked day opt out of target requirements (defaults to 1; the calc layer in
    Phase 3 interprets it).
    """
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS day_types (
            date           TEXT PRIMARY KEY,
            type           TEXT NOT NULL
                             CHECK (type IN ({", ".join("'%s'" % t for t in DAY_TYPES)})),
            name           TEXT,
            planned        INTEGER NOT NULL DEFAULT 0 CHECK (planned IN (0, 1)),
            affects_target INTEGER NOT NULL DEFAULT 1 CHECK (affects_target IN (0, 1))
        )
        """
    )


# Default core settings. These are genuinely core (UI + calendar); module-
# specific defaults (e.g. the detector heartbeat interval) belong to their
# module, not here. INSERT OR IGNORE means re-seeding never clobbers a value the
# user has since changed.
_DEFAULT_SETTINGS = {
    "theme": "system",            # 'light' | 'dark' | 'system'
    "week_start_day": "monday",   # used by calendar / week-boundary helpers
}


def seed_settings(conn: sqlite3.Connection) -> None:
    """Insert default settings without overwriting existing ones."""
    conn.executemany(
        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
        list(_DEFAULT_SETTINGS.items()),
    )


# Order matters: create tables before seeding into them.
CORE_MIGRATIONS = (create_settings, create_day_types, seed_settings)
