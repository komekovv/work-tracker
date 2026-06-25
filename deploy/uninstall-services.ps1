#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Stop and remove the Work-Tracker Windows services.

.PARAMETER Nssm
  Path to nssm.exe (default "nssm").

.EXAMPLE
  # From an elevated PowerShell:
  .\deploy\uninstall-services.ps1
#>
param(
    [string]$Nssm = "nssm"
)

$ErrorActionPreference = "Continue"

if (-not (Get-Command $Nssm -ErrorAction SilentlyContinue)) {
    throw "nssm not found. Put nssm.exe on PATH, or pass -Nssm <path>."
}

foreach ($name in "WorkTrackerAPI", "WorkTrackerDetector") {
    & $Nssm status $name 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        & $Nssm stop $name 2>$null | Out-Null
        & $Nssm remove $name confirm | Out-Null
        Write-Host "Removed $name"
    } else {
        Write-Host "$name not installed; skipping"
    }
}
