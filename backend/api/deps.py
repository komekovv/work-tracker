"""Shared FastAPI dependencies.

The DB path is held on ``app.state`` so the whole app (and tests) can be pointed
at a specific database. Route handlers depend on :func:`get_db_path` and pass it
down to the data/calc/kpi layers, which already accept a ``db_path`` argument.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import Request

from backend.core.db import DB_PATH


def get_db_path(request: Request) -> Path:
    """Return the DB path configured on the app (defaults to the real one)."""
    return getattr(request.app.state, "db_path", DB_PATH)
