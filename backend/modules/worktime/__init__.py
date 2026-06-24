"""Worktime module: the first feature module.

Tracks work sessions from computer power state, computes targets/bonus,
and exposes KPI analytics. Owns the `sessions` and `targets` tables.

Re-exports ``register`` so ``core.registry.discover_modules`` can wire the
module by importing this package and calling its hook.
"""

from backend.modules.worktime.registration import register

__all__ = ["register"]
