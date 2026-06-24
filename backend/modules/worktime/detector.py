"""Worktime detector — the service that turns power state into sessions.

Runs as a long-lived process (an NSSM service in Phase 7). Its life cycle:

1. **Boot** — ensure the schema exists, recover any orphan sessions left by a
   crash, then open a fresh session. Orphan recovery runs *before* opening so
   the new session is never mistaken for an orphan.
2. **Heartbeat** — every `worktime.heartbeat_seconds` (a dynamic setting),
   stamp `last_heartbeat` on the open session. This is what bounds the data loss
   on an unclean shutdown to roughly one interval.
3. **Shutdown** — on SIGINT / SIGTERM / SIGBREAK (Windows) or normal exit, close
   the session cleanly. A lock + flag (and the DB-level guard in
   `close_session`) make the close idempotent, so the signal handler, the loop's
   `finally`, and the `atexit` backstop can all fire without double-closing.

Run it with:  ``python -m backend.modules.worktime.detector``
Optionally point it at a specific DB with the ``WORKTIME_DB_PATH`` env var.
"""

from __future__ import annotations

import atexit
import logging
import os
import signal
import threading
from pathlib import Path

from backend.core import config
from backend.core.db import DB_PATH
from backend.core.registry import Registry, load_all
from backend.modules.worktime import models

logger = logging.getLogger("worktime.detector")

HEARTBEAT_SETTING = "worktime.heartbeat_seconds"
DEFAULT_HEARTBEAT_SECONDS = 60

# How often the main thread wakes to notice a shutdown signal. Short, so signals
# are acted on promptly regardless of the heartbeat interval.
_SIGNAL_POLL_SECONDS = 0.5


class Detector:
    """Owns one open session and the heartbeat loop around it."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        heartbeat_seconds: int | None = None,
    ) -> None:
        self.db_path = Path(db_path) if db_path is not None else DB_PATH
        self._explicit_interval = heartbeat_seconds
        self.session_id: int | None = None
        self._stop = threading.Event()
        self._closed = False
        self._lock = threading.Lock()

    @property
    def heartbeat_seconds(self) -> int:
        """Interval from the constructor override, else the dynamic setting."""
        if self._explicit_interval is not None:
            return self._explicit_interval
        value = config.get_int(
            HEARTBEAT_SETTING, DEFAULT_HEARTBEAT_SECONDS, db_path=self.db_path
        )
        # Guard against a non-positive misconfiguration.
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
        ok = models.close_session(session_id, db_path=self.db_path)
        logger.info(
            "Closed session %s (%s)", session_id, "ok" if ok else "already closed"
        )

    def run(self) -> None:
        """Boot, then run until a stop signal, then close. Blocking."""
        self.boot()
        self._install_signal_handlers()
        atexit.register(self.close)  # backstop for paths that skip `finally`

        worker = threading.Thread(
            target=self._heartbeat_loop, name="heartbeat", daemon=True
        )
        worker.start()
        logger.info(
            "Detector running (heartbeat every %ss). Ctrl+C to stop.",
            self.heartbeat_seconds,
        )
        try:
            # Poll in short slices so signal handlers are serviced promptly.
            while not self._stop.wait(_SIGNAL_POLL_SECONDS):
                pass
        finally:
            self._stop.set()
            worker.join(timeout=self.heartbeat_seconds + 1)
            self.close()

    # -- internals ---------------------------------------------------------

    def _heartbeat_loop(self) -> None:
        """Stamp the heartbeat each interval until stopped."""
        while not self._stop.wait(self.heartbeat_seconds):
            try:
                models.update_heartbeat(self.session_id, db_path=self.db_path)
                logger.debug("heartbeat for session %s", self.session_id)
            except Exception:  # never let a transient DB error kill the loop
                logger.exception("heartbeat failed for session %s", self.session_id)

    def _on_signal(self, signum, _frame) -> None:
        logger.info("Received signal %s; shutting down", signum)
        self._stop.set()

    def _install_signal_handlers(self) -> None:
        # SIGBREAK exists only on Windows; SIGTERM/SIGINT everywhere. Installing
        # must happen on the main thread, so failures are tolerated.
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
