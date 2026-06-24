"""Core's own registration into the registry.

Core is treated like a module for wiring purposes: it owns the shared
``settings`` and ``day_types`` tables and (in Phase 4) the core routes. It is
registered first so its shared tables exist before any feature module's
migrations run.
"""

from __future__ import annotations

from backend.core.migrations import CORE_MIGRATIONS
from backend.core.registry import ModuleRegistration, Registry


def register(registry: Registry) -> None:
    """Register core's tables (and, later, routes) with the registry."""
    registry.register(
        ModuleRegistration(
            name="core",
            migrations=CORE_MIGRATIONS,
            router=None,  # core routes (settings, day-type) added in Phase 4
        )
    )
