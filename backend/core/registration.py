"""Core's own registration into the registry.

Core is treated like a module for wiring purposes: it owns the shared
``settings`` and ``day_types`` tables and (in Phase 4) the core routes. It is
registered first so its shared tables exist before any feature module's
migrations run.
"""

from __future__ import annotations

from backend.core.migrations import CORE_MIGRATIONS
from backend.core.registry import ModuleRegistration, Registry


def _core_router_factory():
    """Lazily import and return core's router (keeps FastAPI out of import)."""
    from backend.core.routes import router

    return router


def register(registry: Registry) -> None:
    """Register core's tables and routes with the registry."""
    registry.register(
        ModuleRegistration(
            name="core",
            migrations=CORE_MIGRATIONS,
            router_factory=_core_router_factory,
        )
    )
