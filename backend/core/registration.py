"""Core's own registration into the registry.

Core is treated like a module for wiring purposes: it owns the shared
``settings`` and ``day_types`` tables and (in Phase 4) the core routes. It is
registered first so its shared tables exist before any feature module's
migrations run.

The migration tuple is intentionally empty at this step — the actual
``settings`` / ``day_types`` migrations are added in Step 4 and simply appended
here. Wiring it now proves the registration path works before any real schema
exists.
"""

from __future__ import annotations

from backend.core.registry import ModuleRegistration, Registry


def register(registry: Registry) -> None:
    """Register core's tables (and, later, routes) with the registry."""
    registry.register(
        ModuleRegistration(
            name="core",
            migrations=(),  # settings + day_types migrations added in Step 4
            router=None,  # core routes (settings, day-type) added in Phase 4
        )
    )
