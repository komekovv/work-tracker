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

$ErrorActionPreference = "Stop"

if (-not (Get-Command $Nssm -ErrorAction SilentlyContinue)) {
    throw "nssm not found. Put nssm.exe on PATH, or pass -Nssm <path>."
}

# Run nssm without letting its stderr abort the script.
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

foreach ($name in "WorkTrackerAPI", "WorkTrackerDetector") {
    if (Get-Service -Name $name -ErrorAction SilentlyContinue) {
        Invoke-Nssm stop $name | Out-Null
        Invoke-Nssm remove $name confirm | Out-Null
        Write-Host "Removed $name"
    } else {
        Write-Host "$name not installed; skipping"
    }
}
