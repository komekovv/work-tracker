# Phase 1 · Step 2 — `core/db.py` (connection + migrations)

**Status:** Done
**Goal:** A configured SQLite connection layer plus an idempotent migration
runner — the foundation every other core/module piece builds on.

## What was implemented (`backend/core/db.py`)

Public surface:

- **`DB_PATH`** — `backend/data/app.db`, resolved relative to the file (stable
  regardless of current working directory).
- **`BUSY_TIMEOUT_MS = 5000`** — lock-wait budget.
- **`Migration`** — type alias: `Callable[[sqlite3.Connection], None]`. A
  migration does idempotent DDL/seed and must **not** commit (the runner owns
  the transaction).
- **`get_connection(db_path=None)`** — opens and configures a connection.
- **`connection(db_path=None)`** — context manager: commit on success, rollback
  on exception, always close.
- **`run_migrations(migrations, db_path=None)`** — runs a sequence of migrations
  in order inside one transaction; rolls back the whole batch on failure.

## Key decisions

- **WAL journaling** (`PRAGMA journal_mode=WAL`): the detector and the API are
  separate processes sharing one `app.db`. WAL lets readers and the writer work
  concurrently, which is what makes a single shared file viable. WAL is
  persisted in the DB header, so re-setting it each connect is harmless.
- **`busy_timeout=5000ms`**, mirrored by the `connect(timeout=...)` arg, so a
  connection waits for a held write lock instead of immediately raising
  "database is locked".
- **`synchronous=NORMAL`** — the recommended durability/speed balance under WAL.
- **`foreign_keys=ON`** — must be enabled per-connection in SQLite.
- **`row_factory=sqlite3.Row`** — rows accessible by column name.
- **Per-caller connections** — no shared global connection; each process/
  thread/request opens its own (SQLite connections aren't cross-thread safe).
- **Migrations live elsewhere** — db.py only knows how to *run* a sequence.
  The registry (Step 3) will collect core's + modules' migrations and feed them
  to `run_migrations`. This keeps the connection layer free of any schema
  knowledge.

## Verification (throwaway temp DB, no repo test files)

Ran a smoke check against a temp DB (not the real `app.db`):
- `journal_mode = wal`, `busy_timeout = 5000`, `foreign_keys = 1` confirmed.
- Ran the same `CREATE TABLE IF NOT EXISTS` + `INSERT OR IGNORE` migrations
  **twice** → still 1 row (idempotent).
- Row-by-name access (`row["v"] == "world"`) works.

No dependencies needed — stdlib `sqlite3` only. Nothing to install for this step.

## Next

Step 3 — `core/registry.py`: the module registration system (migrations +
router). Core will register its own tables through it so the pattern is proven
before any feature module exists.
