"""SQLite connection management and migration runner.

This is the bedrock the rest of the backend sits on. The detector service
and the API run as **separate processes** writing to the same `app.db`, so
the connection is configured for multi-process safety:

- **WAL** journaling: readers don't block writers and vice-versa, which is
  what makes one shared file workable across two processes.
- **busy_timeout**: a connection waits (instead of immediately raising
  "database is locked") when another process holds the write lock.

Migrations are plain callables that issue **idempotent** DDL
(`CREATE TABLE IF NOT EXISTS`, `INSERT OR IGNORE`), so running them on every
startup is safe. The registry (Step 3) collects them; this module only knows
how to *run* a sequence of them.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path

# The DB lives at backend/data/app.db, resolved relative to THIS file so the
# location is stable no matter what the current working directory is.
_CORE_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _CORE_DIR.parent
DB_PATH = _BACKEND_DIR / "data" / "app.db"

# How long (milliseconds) a connection waits for a held lock before giving up
# with "database is locked". Generous, because detector + API contend.
BUSY_TIMEOUT_MS = 5000

# A migration receives an open connection and performs idempotent schema/seed
# work. It must not commit — `run_migrations` owns the transaction boundary.
Migration = Callable[[sqlite3.Connection], None]


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open and configure a SQLite connection.

    Each caller (process / thread / request) should use its own connection;
    SQLite connections are not meant to be shared across threads.
    """
    path = Path(db_path) if db_path is not None else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    # timeout is in seconds and mirrors busy_timeout so the Python-side wait
    # matches the SQLite-side wait.
    conn = sqlite3.connect(path, timeout=BUSY_TIMEOUT_MS / 1000)

    # Rows accessible by column name (row["col"]) instead of positional only.
    conn.row_factory = sqlite3.Row

    # PRAGMAs. journal_mode=WAL is persisted in the DB header (setting it each
    # time is harmless); synchronous=NORMAL is the recommended durability/speed
    # balance under WAL; foreign_keys must be enabled per-connection.
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connection(db_path: Path | str | None = None) -> Iterator[sqlite3.Connection]:
    """Connection context manager with transaction handling.

    Commits on clean exit, rolls back on exception, and always closes.
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def optional_connection(
    conn: sqlite3.Connection | None = None, db_path: Path | str | None = None
) -> Iterator[sqlite3.Connection]:
    """Yield the caller's connection, or a self-managed one if none is given.

    When ``conn`` is provided it is yielded as-is and the caller keeps ownership
    of commit/close (so several operations can share one transaction). When it
    is ``None``, a fresh connection is opened via :func:`connection` and
    committed/closed on exit. Used by the higher-level core helpers (config,
    day_types) so they all compose the same way.
    """
    if conn is not None:
        yield conn
    else:
        with connection(db_path) as owned:
            yield owned


def run_migrations(
    migrations: Iterable[Migration], db_path: Path | str | None = None
) -> None:
    """Run migrations in order inside a single transaction.

    Because every migration is idempotent, this is safe to call on each
    startup. If any migration raises, the whole batch rolls back.
    """
    with connection(db_path) as conn:
        for migrate in migrations:
            migrate(conn)
