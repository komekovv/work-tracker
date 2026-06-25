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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.core.db import DB_PATH
from backend.core.registry import Registry, load_all

logger = logging.getLogger("api")

# Dev origins for the Next.js dev server. In production the static export is
# served same-origin by FastAPI, so CORS is mainly a dev convenience.
_DEV_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

# The built frontend (`frontend/out`), resolved relative to the repo root.
# Overridable via WORKTIME_STATIC_DIR.
_DEFAULT_STATIC_DIR = Path(__file__).resolve().parents[2] / "frontend" / "out"


def _mount_static(app: FastAPI, static_dir: Path) -> None:
    """Serve the Next.js static export, mapping clean routes to its files.

    The export produces flat `<route>.html` files (e.g. `worktime.html`,
    `worktime/settings.html`), so a custom resolver maps `/worktime` →
    `worktime.html`. Registered last, so the `/api/*` routers and `/health`
    always take precedence.
    """
    base = static_dir.resolve()

    # GET and HEAD: clients (and Next.js route prefetch) issue HEAD requests;
    # without HEAD the catch-all would 405 them.
    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    def serve_static(full_path: str) -> FileResponse:
        if full_path in ("", "/"):
            return FileResponse(base / "index.html")

        target = (base / full_path).resolve()
        # Guard against path traversal outside the static root.
        if base not in target.parents and target != base:
            raise HTTPException(status_code=404)

        if target.is_file():  # an asset: _next/..., favicon.ico, *.svg
            return FileResponse(target)

        route_html = base / f"{full_path}.html"  # /worktime → worktime.html
        if route_html.is_file():
            return FileResponse(route_html)

        index_html = target / "index.html"  # directory index, if any
        if index_html.is_file():
            return FileResponse(index_html)

        return FileResponse(base / "404.html", status_code=404)


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

    # Serve the built frontend same-origin, if present. Skipped in dev (where
    # `next dev` serves the UI and `out/` doesn't exist). Mounted last so it
    # never shadows the API routes.
    static_dir = Path(
        os.environ.get("WORKTIME_STATIC_DIR") or _DEFAULT_STATIC_DIR
    )
    if static_dir.is_dir():
        _mount_static(app, static_dir)
        logger.info("Serving static frontend from %s", static_dir)

    return app


# Module-level app for `uvicorn backend.api.main:app`. Building the app does not
# touch the database — migrations run on startup (lifespan), not at import.
# Honours WORKTIME_DB_PATH (same override the detector uses) for the DB location.
app = create_app(os.environ.get("WORKTIME_DB_PATH") or None)
