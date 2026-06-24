"""Typed read/write access to the dynamic ``settings`` table.

The point of ``settings`` is that the app is reconfigurable without code
changes. Values are stored as TEXT; this module is the typed front door:

- ``get`` / ``get_bool`` / ``get_int`` / ``get_float`` — read with a default.
- ``set`` — upsert a value (booleans normalised to ``'true'``/``'false'``).
- ``get_all`` — the whole settings dict.
- ``delete`` — remove a key.

**Missing vs malformed:** a key that isn't present returns the caller's
``default``. A key that *is* present but can't be parsed as the requested type
raises ``ValueError`` — that's a genuine misconfiguration and shouldn't be
silently masked.

**Connections:** every function accepts an optional ``conn``. Pass one to take
part in a caller-owned transaction (the caller commits); omit it and the
function opens, commits, and closes its own connection via ``db.connection``.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from backend.core import db

# Recognised textual forms for boolean settings (case-insensitive).
_TRUE_TOKENS = {"1", "true", "yes", "on"}
_FALSE_TOKENS = {"0", "false", "no", "off"}


@contextmanager
def _conn_ctx(
    conn: sqlite3.Connection | None, db_path: Path | str | None
) -> Iterator[sqlite3.Connection]:
    """Use the caller's connection if given (caller owns commit/close),
    otherwise open a self-managed one."""
    if conn is not None:
        yield conn
    else:
        with db.connection(db_path) as owned:
            yield owned


def _to_text(value: Any) -> str:
    """Serialise a Python value to its stored TEXT form."""
    # bool is a subclass of int, so it must be checked first.
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def get(
    key: str,
    default: str | None = None,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> str | None:
    """Return the raw string value for ``key``, or ``default`` if unset."""
    with _conn_ctx(conn, db_path) as c:
        row = c.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
    return row["value"] if row is not None else default


def get_bool(
    key: str,
    default: bool = False,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> bool:
    """Return ``key`` as a bool. Missing → default; malformed → ValueError."""
    raw = get(key, conn=conn, db_path=db_path)
    if raw is None:
        return default
    token = raw.strip().lower()
    if token in _TRUE_TOKENS:
        return True
    if token in _FALSE_TOKENS:
        return False
    raise ValueError(f"Setting '{key}'={raw!r} is not a boolean")


def get_int(
    key: str,
    default: int | None = None,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> int | None:
    """Return ``key`` as an int. Missing → default; malformed → ValueError."""
    raw = get(key, conn=conn, db_path=db_path)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"Setting '{key}'={raw!r} is not an integer") from None


def get_float(
    key: str,
    default: float | None = None,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> float | None:
    """Return ``key`` as a float. Missing → default; malformed → ValueError."""
    raw = get(key, conn=conn, db_path=db_path)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        raise ValueError(f"Setting '{key}'={raw!r} is not a number") from None


def set(
    key: str,
    value: Any,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> None:
    """Insert or update ``key``. Booleans are normalised to true/false text."""
    with _conn_ctx(conn, db_path) as c:
        c.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, _to_text(value)),
        )


def get_all(
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> dict[str, str]:
    """Return all settings as a ``{key: value}`` dict, ordered by key."""
    with _conn_ctx(conn, db_path) as c:
        rows = c.execute("SELECT key, value FROM settings ORDER BY key").fetchall()
    return {row["key"]: row["value"] for row in rows}


def delete(
    key: str,
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | str | None = None,
) -> bool:
    """Delete ``key``. Returns True if a row was removed, False if absent."""
    with _conn_ctx(conn, db_path) as c:
        cur = c.execute("DELETE FROM settings WHERE key = ?", (key,))
        return cur.rowcount > 0
