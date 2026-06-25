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

# Run nssm without letting its stderr abort the script. NSSM prints
# informational/diagnostic text to stderr (e.g. "Can't open service!"), which
# under ErrorActionPreference='Stop' would otherwise raise a NativeCommandError.
function Invoke-Nssm {
    param([Parameter(ValueFromRemainingArguments = $true)] $NssmArgs)
    $old = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $Nssm @NssmArgs 2>$null | Out-Null
        return $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $old
    }
}

function Install-WtService {
    param([string]$Name, [string]$Params, [string]$LogPrefix)

    # Idempotent: remove an existing service of the same name first. Use
    # Get-Service (not nssm) so a missing service is a clean "not found".
    if (Get-Service -Name $Name -ErrorAction SilentlyContinue) {
        Invoke-Nssm stop $Name | Out-Null
        Invoke-Nssm remove $Name confirm | Out-Null
    }

    $code = Invoke-Nssm install $Name $Python
    if ($code -ne 0) { throw "nssm failed to install $Name (exit $code)." }

    Invoke-Nssm set $Name AppParameters $Params | Out-Null
    Invoke-Nssm set $Name AppDirectory $Repo | Out-Null
    Invoke-Nssm set $Name Start SERVICE_AUTO_START | Out-Null
    Invoke-Nssm set $Name AppStdout (Join-Path $LogDir "$LogPrefix.out.log") | Out-Null
    Invoke-Nssm set $Name AppStderr (Join-Path $LogDir "$LogPrefix.err.log") | Out-Null
    Invoke-Nssm set $Name AppRotateFiles 1 | Out-Null
    Invoke-Nssm set $Name AppExit Default Restart | Out-Null
    Write-Host "Configured $Name"
}

Install-WtService -Name "WorkTrackerAPI" `
    -Params "-m uvicorn backend.api.main:app --host 127.0.0.1 --port $Port" `
    -LogPrefix "api"

Install-WtService -Name "WorkTrackerDetector" `
    -Params "-m backend.modules.worktime.detector" `
    -LogPrefix "detector"

Invoke-Nssm start WorkTrackerAPI | Out-Null
Invoke-Nssm start WorkTrackerDetector | Out-Null

Write-Host ""
Write-Host "Done. Open the app at http://127.0.0.1:$Port"
Write-Host "Logs: $LogDir"
