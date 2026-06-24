"""FastAPI application — wires modules via the registry.

`create_app` builds the app, mounts every registered module's router by
*iterating the registry* (never naming a module), and runs migrations on
startup. Adding a new module's routes requires no edit here — the module just
registers a `router_factory`.

Run the server with:
    uvicorn backend.api.main:app --reload
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.db import DB_PATH
from backend.core.registry import Registry, load_all

logger = logging.getLogger("api")

# Dev origins for the Next.js dev server. In production the static export is
# served same-origin by FastAPI (Phase 7), so CORS is mainly a dev convenience.
_DEV_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Run migrations once when the server starts."""
    registry: Registry = app.state.registry
    registry.init_db(app.state.db_path)
    logger.info("Migrations applied to %s", app.state.db_path)
    yield


def create_app(db_path: Path | str | None = None) -> FastAPI:
    """Build the FastAPI app, mounting all registered module routers."""
    app = FastAPI(title="Work-Time & KPI Tracker", lifespan=_lifespan)

    # Where this app's data lives (overridable for tests).
    app.state.db_path = Path(db_path) if db_path is not None else DB_PATH

    # Assemble core + modules, then mount each unit's router (lazily built).
    registry = load_all(Registry())
    app.state.registry = registry
    for name, router in registry.routers():
        app.include_router(router)
        logger.info("Mounted router for '%s'", name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_DEV_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


# Module-level app for `uvicorn backend.api.main:app`. Building the app does not
# touch the database — migrations run on startup (lifespan), not at import.
# Honours WORKTIME_DB_PATH (same override the detector uses) for the DB location.
app = create_app(os.environ.get("WORKTIME_DB_PATH") or None)
