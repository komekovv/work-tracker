"""Pydantic schemas for core API I/O.

Kept separate from `routes.py` so request/response shapes are easy to find and
reuse. Using `datetime.date` for date fields lets FastAPI validate the
'YYYY-MM-DD' format automatically (a bad date → 422).
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel

# The day-type enum, mirrored from core.migrations.DAY_TYPES for request
# validation (a bad value → 422 before any handler code runs).
DayTypeName = Literal["workday", "holiday", "leave", "vacation"]


class DayTypeIn(BaseModel):
    """Request body for setting a day-type marking."""

    date: date
    type: DayTypeName
    name: str | None = None
    planned: bool = False
    affects_target: bool | None = None


class DayTypeOut(BaseModel):
    """The effective day-type marking after a set (reflects case C4)."""

    date: date
    type: DayTypeName
    name: str | None
    planned: bool
    affects_target: bool
