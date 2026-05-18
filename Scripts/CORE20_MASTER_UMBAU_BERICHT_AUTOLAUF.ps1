#!/usr/bin/env powershell
#Requires -Version 5.1
<#
.SYNOPSIS
    CORE-20 – Master-Umbau-Bericht
.DESCRIPTION
    Erstellt den Gesamtbericht fuer den Umbau-Automanager.
    Nur lesend. Keine Dateien werden kopiert.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projektWurzel = Resolve-Path (Join-Path $scriptDir "..")
$pythonExe = "I:\KI_Legal_Project\Tools\Python312\python.exe"
$runner = Join-Path $projektWurzel "Scripts\python_runner\core20_master_umbau_bericht.py"
$check = Join-Path $projektWurzel "Scripts\python_runner\check_core20_master_umbau_bericht.py"

function Write-Log {
    param([string]$msg)
    Write-Host "[CORE-20] $msg"
}

Write-Log "Starte CORE-20 Master-Umbau-Bericht..."

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python nicht gefunden: $pythonExe"
    exit 1
}
if (-not (Test-Path $runner)) {
    Write-Error "Runner nicht gefunden: $runner"
    exit 1
}

Write-Log "Selbsttest..."
& $pythonExe $runner --test
if ($LASTEXITCODE -ne 0) {
    Write-Error "Selbsttest fehlgeschlagen."
    exit 1
}
Write-Log "Selbsttest OK."

Write-Log "Hauptlauf..."
& $pythonExe $runner
if ($LASTEXITCODE -ne 0) {
    Write-Error "Hauptlauf fehlgeschlagen."
    exit 1
}
Write-Log "Hauptlauf abgeschlossen."

Write-Log "Check..."
& $pythonExe $check
if ($LASTEXITCODE -ne 0) {
    Write-Error "Check fehlgeschlagen."
    exit 1
}
Write-Log "Check OK."

Write-Log "CORE-20 MASTER-UMBAU-BERICHT ERFOLGREICH ABGESCHLOSSEN."
