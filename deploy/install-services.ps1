#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Install the Work-Tracker detector and API as auto-starting Windows services
  using NSSM (https://nssm.cc).

.DESCRIPTION
  Registers two services:
    * WorkTrackerAPI      - serves the UI + /api on http://127.0.0.1:<Port>
    * WorkTrackerDetector - records work sessions from power on/off
  Both run the project's venv Python with the repo as the working directory,
  start automatically at boot, restart on crash, and log to .\logs\.

.PARAMETER Port
  Port the API binds (default 8765). The UI is served same-origin, so this is
  the only address you need.

.PARAMETER Nssm
  Path to nssm.exe (default "nssm", i.e. expected on PATH).

.EXAMPLE
  # From an elevated PowerShell:
  .\deploy\install-services.ps1 -Port 8765
#>
param(
    [int]$Port = 8765,
    [string]$Nssm = "nssm"
)

$ErrorActionPreference = "Stop"

# Repo root = parent of this script's folder (deploy\).
$Repo = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Repo "backend\.venv\Scripts\python.exe"
$LogDir = Join-Path $Repo "logs"

if (-not (Get-Command $Nssm -ErrorAction SilentlyContinue)) {
    throw "nssm not found. Install NSSM and put nssm.exe on PATH, or pass -Nssm <path>."
}
if (-not (Test-Path $Python)) {
    throw "venv Python not found at $Python. Create the venv and pip install -r backend\requirements.txt first."
}
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Install-WtService {
    param([string]$Name, [string]$Params, [string]$LogPrefix)

    # Idempotent: remove an existing service of the same name first.
    & $Nssm status $Name 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        & $Nssm stop $Name 2>$null | Out-Null
        & $Nssm remove $Name confirm | Out-Null
    }

    & $Nssm install $Name $Python | Out-Null
    & $Nssm set $Name AppParameters $Params | Out-Null
    & $Nssm set $Name AppDirectory $Repo | Out-Null
    & $Nssm set $Name Start SERVICE_AUTO_START | Out-Null
    & $Nssm set $Name AppStdout (Join-Path $LogDir "$LogPrefix.out.log") | Out-Null
    & $Nssm set $Name AppStderr (Join-Path $LogDir "$LogPrefix.err.log") | Out-Null
    & $Nssm set $Name AppRotateFiles 1 | Out-Null
    & $Nssm set $Name AppExit Default Restart | Out-Null
    Write-Host "Configured $Name"
}

Install-WtService -Name "WorkTrackerAPI" `
    -Params "-m uvicorn backend.api.main:app --host 127.0.0.1 --port $Port" `
    -LogPrefix "api"

Install-WtService -Name "WorkTrackerDetector" `
    -Params "-m backend.modules.worktime.detector" `
    -LogPrefix "detector"

& $Nssm start WorkTrackerAPI | Out-Null
& $Nssm start WorkTrackerDetector | Out-Null

Write-Host ""
Write-Host "Done. Open the app at http://127.0.0.1:$Port"
Write-Host "Logs: $LogDir"
