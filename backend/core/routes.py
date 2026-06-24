"""Core HTTP routes — dynamic settings and day-type markings.

Mounted automatically by the registry (core's `router_factory`). All handlers
take the active DB path via the `get_db_path` dependency and delegate to the
core logic modules, which already own validation and rules (e.g. case C4).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response

from backend.api.deps import get_db_path
from backend.core import config, day_types
from backend.core import db as core_db
from backend.core.schemas import DayTypeIn, DayTypeOut

router = APIRouter(prefix="/api", tags=["core"])


@router.get("/settings")
def get_settings(db_path: Path = Depends(get_db_path)) -> dict[str, str]:
    """All dynamic settings as a key→value map."""
    return config.get_all(db_path=db_path)


@router.post("/settings")
def update_settings(
    values: dict[str, str],
    db_path: Path = Depends(get_db_path),
) -> dict[str, str]:
    """Upsert one or more settings (bulk), returning the full updated map."""
    with core_db.connection(db_path) as conn:
        for key, value in values.items():
            config.set(key, value, conn=conn)
    return config.get_all(db_path=db_path)


@router.post("/day-type", response_model=DayTypeOut)
def set_day_type(
    payload: DayTypeIn,
    db_path: Path = Depends(get_db_path),
) -> DayTypeOut:
    """Set a day-type marking; returns the effective row (honours case C4)."""
    marking = day_types.set_day_type(
        payload.date,
        payload.type,
        name=payload.name,
        planned=payload.planned,
        affects_target=payload.affects_target,
        db_path=db_path,
    )
    return DayTypeOut(
        date=marking.date,
        type=marking.type,
        name=marking.name,
        planned=marking.planned,
        affects_target=marking.affects_target,
    )


@router.delete("/day-type/{day}", status_code=204)
def delete_day_type(
    day: date,
    db_path: Path = Depends(get_db_path),
) -> Response:
    """Remove a day-type marking; 404 if the date was not marked."""
    if not day_types.delete_day_type(day, db_path=db_path):
        raise HTTPException(status_code=404, detail="No day-type marking for that date")
    return Response(status_code=204)
