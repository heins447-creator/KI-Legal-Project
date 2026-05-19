#!/usr/bin/env powershell
#Requires -Version 5.1
<#
.SYNOPSIS
    CORE-14 – Auswertung der CORE-13 Altbestand-Inventur
.DESCRIPTION
    Liest CORE-13 Inventur und erstellt Zielentscheidungen fuer den Umbau.
    Nur lesend. Keine Dateien werden verschoben, geloescht oder umbenannt.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projektWurzel = Resolve-Path (Join-Path $scriptDir "..")
$pythonExe = "I:\KI_Legal_Project\Tools\Python312\python.exe"
$runner = Join-Path $projektWurzel "Scripts\python_runner\core14_core13_auswertung.py"
$check = Join-Path $projektWurzel "Scripts\python_runner\check_core14_core13_auswertung.py"

function Write-Log {
    param([string]$msg)
    Write-Host "[CORE-14] $msg"
}

Write-Log "Starte CORE-14 Auswertung..."

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python nicht gefunden: $pythonExe"
    exit 1
}

if (-not (Test-Path $runner)) {
    Write-Error "Runner nicht gefunden: $runner"
    exit 1
}

# Selbsttest
Write-Log "Fuehre Selbsttest durch..."
& $pythonExe $runner --test
if ($LASTEXITCODE -ne 0) {
    Write-Error "Selbsttest fehlgeschlagen."
    exit 1
}
Write-Log "Selbsttest OK."

# Hauptlauf
Write-Log "Fuehre Hauptlauf durch..."
& $pythonExe $runner
if ($LASTEXITCODE -ne 0) {
    Write-Error "Hauptlauf fehlgeschlagen."
    exit 1
}
Write-Log "Hauptlauf abgeschlossen."

# Check
Write-Log "Fuehre Check durch..."
& $pythonExe $check
if ($LASTEXITCODE -ne 0) {
    Write-Error "Check fehlgeschlagen."
    exit 1
}
Write-Log "Check OK."

Write-Log "CORE-14 AUSWERTUNG ERFOLGREICH ABGESCHLOSSEN."
