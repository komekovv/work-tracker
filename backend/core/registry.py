"""Module registration system — the heart of the modular monolith.

Each registrable unit (core itself, and every feature module) describes
itself with a :class:`ModuleRegistration`: a name, its idempotent
**migrations**, and (later) an API **router**. The registry collects these so
that:

- ``api/main.py`` can run every module's migrations and mount every module's
  router by *iterating the registry* — it never names a specific module.
- Adding a new module is purely additive: drop a package under
  ``backend/modules/`` that exposes a ``register(registry)`` hook. No edits to
  core or to the API app (open-closed principle).

Design note: the router is stored as a loosely-typed object (``Any``) rather
than importing FastAPI here. That keeps this module importable with **only the
standard library**, so the data/registry layer can be exercised before the web
stack is installed. FastAPI types are validated where routers are actually
mounted (the API layer, Phase 4).
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.core.db import Migration, run_migrations


@dataclass(frozen=True)
class ModuleRegistration:
    """One registrable unit's contribution to the app.

    - ``name``: unique identifier (also the log/label name).
    - ``migrations``: idempotent migrations owned by this unit, run in order.
    - ``router``: a FastAPI ``APIRouter`` (typed loosely; mounted in Phase 4).
      ``None`` for units that contribute only tables.
    """

    name: str
    migrations: tuple[Migration, ...] = ()
    router: Any | None = None


class Registry:
    """An ordered collection of :class:`ModuleRegistration` objects.

    Registration order is preserved and used as the order in which migrations
    run and routers mount. Core is expected to register first (its shared
    tables underpin the modules).
    """

    def __init__(self) -> None:
        self._registrations: dict[str, ModuleRegistration] = {}

    def register(self, registration: ModuleRegistration) -> None:
        """Add a registration. Raises on a duplicate name."""
        if registration.name in self._registrations:
            raise ValueError(
                f"Module '{registration.name}' is already registered"
            )
        self._registrations[registration.name] = registration

    @property
    def registrations(self) -> tuple[ModuleRegistration, ...]:
        """All registrations, in registration order."""
        return tuple(self._registrations.values())

    def migrations(self) -> Iterator[Migration]:
        """Every registered migration, flattened, in order."""
        for reg in self._registrations.values():
            yield from reg.migrations

    def routers(self) -> Iterator[tuple[str, Any]]:
        """``(name, router)`` for every registration that has a router."""
        for reg in self._registrations.values():
            if reg.router is not None:
                yield reg.name, reg.router

    def init_db(self, db_path: Path | str | None = None) -> None:
        """Run all registered migrations against the database."""
        run_migrations(self.migrations(), db_path=db_path)

    def clear(self) -> None:
        """Drop all registrations (useful for re-discovery in one process)."""
        self._registrations.clear()


# Process-wide singleton. Core and modules register into this; the API app and
# the detector both load it at startup.
registry = Registry()


def discover_modules(reg: Registry) -> None:
    """Import every subpackage under ``backend.modules`` and let it register.

    A module opts in by exposing a top-level ``register(registry)`` callable
    (in its package ``__init__`` or re-exported there). Modules without one are
    skipped, so an empty/placeholder module package is harmless.
    """
    import backend.modules as modules_pkg

    for info in pkgutil.iter_modules(modules_pkg.__path__):
        module = importlib.import_module(f"{modules_pkg.__name__}.{info.name}")
        register_hook = getattr(module, "register", None)
        if callable(register_hook):
            register_hook(reg)


def load_all(reg: Registry | None = None) -> Registry:
    """Populate a registry with core first, then all discovered modules.

    This is the single entry point both the API app and the detector use to
    assemble the application. Imports are done lazily here to avoid import
    cycles (core.registration imports back into this module).
    """
    reg = reg if reg is not None else registry

    from backend.core import registration as core_registration

    core_registration.register(reg)
    discover_modules(reg)
    return reg
