#!/usr/bin/env powershell
#Requires -Version 5.1
<#
.SYNOPSIS
    CORE-18 – Validierung der neuen Struktur
.DESCRIPTION
    Prueft, ob alle kopierten Dateien korrekt im Ziel angekommen sind.
    Nur pruefend. Keine Dateien werden kopiert.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projektWurzel = Resolve-Path (Join-Path $scriptDir "..")
$pythonExe = "I:\KI_Legal_Project\Tools\Python312\python.exe"
$runner = Join-Path $projektWurzel "Scripts\python_runner\core18_neustruktur_validierung.py"
$check = Join-Path $projektWurzel "Scripts\python_runner\check_core18_neustruktur_validierung.py"

function Write-Log {
    param([string]$msg)
    Write-Host "[CORE-18] $msg"
}

Write-Log "Starte CORE-18 Neustruktur Validierung..."

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

Write-Log "CORE-18 NEUSTRUKTUR VALIDIERUNG ERFOLGREICH ABGESCHLOSSEN."
