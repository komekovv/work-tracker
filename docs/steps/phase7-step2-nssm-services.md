# Phase 7 · Step 2 — NSSM service scripts

**Status:** Done
**Goal:** Scripts to register the detector and API as auto-starting Windows
services via NSSM.

## What was implemented (`deploy/`)

- **`install-services.ps1`** (`#Requires -RunAsAdministrator`):
  - Params `-Port` (default **8765**) and `-Nssm` (default `nssm` on PATH).
  - Resolves the repo root from the script location and the venv Python.
  - Checks NSSM + venv Python exist; creates `logs/`.
  - Registers two services (idempotent — removes an existing one first):
    - **WorkTrackerAPI** → `python -m uvicorn backend.api.main:app --host
      127.0.0.1 --port <Port>`
    - **WorkTrackerDetector** → `python -m backend.modules.worktime.detector`
  - For each: `AppDirectory` = repo root, `Start` = auto, stdout/stderr to
    `logs/<svc>.{out,err}.log` with rotation, `AppExit Default Restart`.
  - Starts both services; prints the app URL.
- **`uninstall-services.ps1`** — stops and removes both services (idempotent).

## Key decisions

- **Two services, API serves the UI** (port 8765 only) — matches "served by
  FastAPI itself, no separate process." The detector is the second service.
- **Repo root as `AppDirectory`** so `backend` imports and the default DB
  (`backend/data/app.db`, resolved via `__file__`) and static dir
  (`frontend/out`) all work without extra env vars.
- **`AppExit Default Restart`** — services recover from crashes (and the
  detector's orphan recovery cleans up the interrupted session on restart).
- **Port is a script param** (default 8765) — production stays off the dev
  ports (8000/3000), per the user's choice. See [[prod-port]].
- **`logs/` gitignored.**

## Verification

I can't install the services here (needs admin + the NSSM binary), so I verified
everything they wrap:
- Both scripts **parse cleanly** (PowerShell AST parser, no execution).
- `python -m uvicorn` → uvicorn 0.49.0; the detector module imports.
- Ran the **exact API service command** (`-m uvicorn backend.api.main:app
  --host 127.0.0.1 --port 8765` from the repo root): `/health`, `/`, `/worktime`
  (UI) and `/api/worktime/today` (JSON) all 200; root is the app. Port 8000 is
  now free.
- The detector command was verified end-to-end in Phase 2 (boot/heartbeat/
  shutdown + crash recovery).

## Fix (post-install-run)

The user's first run hit `nssm.exe : Can't open service!` at the existence
check. Root cause: `nssm status <missing>` writes to **stderr**, and under
`$ErrorActionPreference = "Stop"` PowerShell promotes native stderr to a
terminating error (even with `2>$null`). Fixed by:
- checking existence with **`Get-Service -ErrorAction SilentlyContinue`** (not
  `nssm status`), and
- routing every `nssm` call through an **`Invoke-Nssm`** helper that runs it
  under `ErrorActionPreference = "Continue"` with `2>$null`, returning the exit
  code.
Verified by simulating a stderr+exit-1 native command under `Stop` (no throw)
and `Get-Service` on a missing service (clean empty result). The same helper was
added to the uninstall script.

## Next

Step 3 — README (prerequisites, setup, build, install/run services, verify,
logs, uninstall) + final end-to-end verification.
