#Requires -Version 5.1
<#
.SYNOPSIS
    Ground-side viewer launcher for Windows.

.DESCRIPTION
    Bootstraps a .venv-ground virtualenv on first run, installs the ground-side
    dependencies quietly, then launches the live matplotlib viewer. Subsequent
    runs reuse the existing venv.

    Works on Windows PowerShell 5.1 and PowerShell 7 or later.

.PARAMETER Port
    Serial port name (e.g. COM7). Defaults to COM7.

.PARAMETER Help
    Print usage information and exit.

.EXAMPLE
    .\run_ground.ps1 -Port COM5
.EXAMPLE
    $env:GROUNDWINDOWS = "120"; .\run_ground.ps1 -Port COM7
#>
[CmdletBinding()]
param(
    [string]$Port = "COM7",
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Host "Usage: .\run_ground.ps1 [-Port <COMx>] [-Help]"
    Write-Host ""
    Write-Host "Launches the ground-side telemetry viewer. -Port defaults to COM7."
    Write-Host ""
    Write-Host "Supported environment variables (all optional, with defaults):"
    Write-Host "  GROUNDBAUD         Serial baud rate                     [57600]"
    Write-Host "  GROUNDMIRROR       Mirror CSV path   [ground_methane_log.csv]"
    Write-Host "  GROUNDWINDOWS      Plot window width in seconds           [300]"
    Write-Host "  GROUNDFLUSHSEC     CSV flush interval in seconds          [1.0]"
    Write-Host "  METHANEVAL_MIN     Minimum accepted methane value           [0]"
    Write-Host "  METHANEVAL_MAX     Maximum accepted methane value       [10000]"
    Write-Host ""
    Write-Host "Example:"
    Write-Host "  `$env:GROUNDWINDOWS = '120'; .\run_ground.ps1 -Port COM7"
    return
}

# Always operate from the script's own directory so paths resolve predictably.
Set-Location -LiteralPath $PSScriptRoot

$VenvDir = Join-Path $PSScriptRoot ".venv-ground"
$Activate = Join-Path $VenvDir "Scripts\Activate.ps1"
$Requirements = Join-Path $PSScriptRoot "requirements-ground.txt"
$Viewer = Join-Path $PSScriptRoot "ground_viewer.py"

if (-not (Test-Path -LiteralPath $VenvDir)) {
    Write-Host "Creating virtualenv at $VenvDir ..."
    python -m venv $VenvDir
}

if (-not (Test-Path -LiteralPath $Activate)) {
    throw "Virtualenv activation script not found at $Activate. Delete .venv-ground and rerun."
}

# Dot-source so the activated venv sticks for the rest of this process.
. $Activate

python -m pip install --quiet --upgrade pip
pip install --quiet -r $Requirements

python $Viewer $Port
