"""Worktime detector — turns computer power state into work sessions.

Runs as an NSSM Windows service. Lifecycle:

- **boot**: ensure the schema, recover any crash-orphaned session (closing it at
  its *last heartbeat*, not now), then open a fresh session.
- **run**: write a heartbeat every interval, so a hard power-off loses at most
  one interval of time.
- **stop**: on the service-stop signal (NSSM sends Ctrl+C/Break on stop and at
  PC shutdown), **close the session and exit immediately, right in the signal
  handler.**

Deliberately **single-threaded**: the main thread sleeps in short ticks and the
signal handler does the close + `sys.exit(0)` directly — no worker threads or
event coordination that could delay or miss the shutdown write. This mirrors a
pattern proven reliable under NSSM.

Run with:  ``python -m backend.modules.worktime.detector``
Point it at a specific DB with the ``WORKTIME_DB_PATH`` env var.
"""

from __future__ import annotations

import atexit
import logging
import os
import signal
import sys
import threading
import time
from pathlib import Path

from backend.core import config
from backend.core.db import DB_PATH
from backend.core.registry import Registry, load_all
from backend.modules.worktime import models

logger = logging.getLogger("worktime.detector")

HEARTBEAT_SETTING = "worktime.heartbeat_seconds"
DEFAULT_HEARTBEAT_SECONDS = 60

# Main-loop granularity: the loop wakes this often to check the heartbeat timer.
# Kept short (1s) so that even if a stop signal doesn't interrupt `time.sleep`
# (Ctrl+Break doesn't on Windows; Ctrl+C does), the session still closes within
# ~1s — well inside the PC-shutdown time budget.
_TICK_SECONDS = 1


class Detector:
    """Owns one open session and a simple heartbeat loop around it."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        heartbeat_seconds: int | None = None,
    ) -> None:
        self.db_path = Path(db_path) if db_path is not None else DB_PATH
        self._explicit_interval = heartbeat_seconds
        self.session_id: int | None = None
        self._closed = False
        self._lock = threading.Lock()  # guards the one-time close

    @property
    def heartbeat_seconds(self) -> int:
        """Interval from the constructor override, else the dynamic setting."""
        if self._explicit_interval is not None:
            return self._explicit_interval
        value = config.get_int(
            HEARTBEAT_SETTING, DEFAULT_HEARTBEAT_SECONDS, db_path=self.db_path
        )
        return value if value and value > 0 else DEFAULT_HEARTBEAT_SECONDS

    # -- lifecycle ---------------------------------------------------------

    def boot(self) -> int:
        """Ensure schema, recover orphans, open a new session. Returns its id."""
        reg = Registry()
        load_all(reg)  # fresh registry each boot → safe to call repeatedly
        reg.init_db(self.db_path)

        recovered = models.recover_orphans(db_path=self.db_path)
        if recovered:
            logger.info(
                "Recovered %d orphan session(s): %s", len(recovered), recovered
            )

        self.session_id = models.open_session(db_path=self.db_path)
        self._closed = False
        logger.info("Opened session %s", self.session_id)
        return self.session_id

    def close(self) -> None:
        """Close the open session exactly once (idempotent)."""
        with self._lock:
            if self._closed or self.session_id is None:
                return
            self._closed = True
            session_id = self.session_id
        try:
            models.close_session(session_id, db_path=self.db_path)
            logger.info("Closed session %s", session_id)
        except Exception:
            logger.exception("Failed to close session %s", session_id)

    def run(self) -> None:
        """Boot (with retry), then heartbeat until stopped. Blocking."""
        # Install handlers first so the service can be stopped cleanly even
        # while still retrying boot.
        self._install_signal_handlers()
        atexit.register(self.close)  # backstop for any exit path

        self._boot_with_retry()

        interval = self.heartbeat_seconds
        logger.info(
            "Detector running (heartbeat every %ss). Stop the service to close.",
            interval,
        )
        next_beat = time.monotonic() + interval
        try:
            while True:
                time.sleep(_TICK_SECONDS)
                if time.monotonic() >= next_beat:
                    try:
                        models.update_heartbeat(self.session_id, db_path=self.db_path)
                    except Exception:  # never let a transient DB error kill the loop
                        logger.exception(
                            "heartbeat failed for session %s", self.session_id
                        )
                    next_beat = time.monotonic() + interval
        finally:
            # Normal-exit backstop; the signal handler usually closes first.
            self.close()

    def _boot_with_retry(self) -> None:
        """Open the session, retrying transient startup failures.

        At PC boot the API service may be initialising the **same** SQLite file
        at the same moment, which can briefly lock it. Rather than crash (and let
        NSSM throttle-restart us into a Paused state), we retry until boot
        succeeds. Staying alive in this loop also means NSSM sees the process as
        running, not failing. The signal handlers installed before this allow a
        clean stop mid-retry.
        """
        delay = 2
        attempt = 0
        while True:
            attempt += 1
            try:
                self.boot()
                return
            except Exception:
                logger.exception(
                    "Boot attempt %d failed (DB busy at startup?); retrying in %ss",
                    attempt,
                    delay,
                )
                time.sleep(delay)
                delay = min(delay * 2, 30)  # backoff, capped

    # -- signal handling ---------------------------------------------------

    def _on_signal(self, signum, _frame=None) -> None:
        """Close the session and exit immediately (runs in the main thread)."""
        logger.info(
            "Received stop signal %s; closing session %s", signum, self.session_id
        )
        self.close()
        sys.exit(0)

    def _install_signal_handlers(self) -> None:
        # SIGBREAK is Windows-only; SIGTERM/SIGINT everywhere. NSSM's stop sends
        # a console Ctrl+C / Ctrl+Break which arrive as these signals.
        for name in ("SIGINT", "SIGTERM", "SIGBREAK"):
            sig = getattr(signal, name, None)
            if sig is None:
                continue
            try:
                signal.signal(sig, self._on_signal)
            except (ValueError, OSError):
                pass


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    db_path = os.environ.get("WORKTIME_DB_PATH") or None
    Detector(db_path=db_path).run()


if __name__ == "__main__":
    main()