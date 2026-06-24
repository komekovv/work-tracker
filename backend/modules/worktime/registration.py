"""Worktime's registration into the core registry.

Discovery (``core.registry.discover_modules``) imports this package and calls
its ``register`` hook, so the module wires itself in with no edits to core or
the API app. The router is ``None`` for now — worktime's HTTP routes arrive in
Phase 4.
"""

from __future__ import annotations

from backend.core.registry import ModuleRegistration, Registry
from backend.modules.worktime.models import WORKTIME_MIGRATIONS


def register(registry: Registry) -> None:
    """Register the worktime module's tables (and, later, routes)."""
    registry.register(
        ModuleRegistration(
            name="worktime",
            migrations=WORKTIME_MIGRATIONS,
            router=None,  # routes added in Phase 4
        )
    )
