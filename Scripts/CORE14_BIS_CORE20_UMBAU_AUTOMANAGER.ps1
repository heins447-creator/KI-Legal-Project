#!/usr/bin/env powershell
#Requires -Version 5.1
<#
.SYNOPSIS
    CORE-14 bis CORE-20 – Autonomer Umbau-Automanager
.DESCRIPTION
    Master-Starter fuer den gesamten Umbau-Automanager.
    Fuehrt CORE-14 bis CORE-20 sequentiell aus.
    Nur kopierend. Keine alten Dateien werden geloescht, verschoben oder umbenannt.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projektWurzel = Resolve-Path (Join-Path $scriptDir "..")
$pythonExe = "I:\KI_Legal_Project\Tools\Python312\python.exe"

function Write-Log {
    param([string]$msg)
    Write-Host "[AUTOMANAGER] $msg"
}

function Invoke-Step {
    param(
        [string]$name,
        [string]$runner,
        [string]$check
    )
    Write-Log "=== $name ==="
    $runnerPath = Join-Path $projektWurzel "Scripts\python_runner\$runner"
    $checkPath = Join-Path $projektWurzel "Scripts\python_runner\$check"

    if (-not (Test-Path $runnerPath)) {
        Write-Error "Runner nicht gefunden: $runnerPath"
        exit 1
    }

    Write-Log "Selbsttest $name..."
    & $pythonExe $runnerPath --test
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Selbsttest $name fehlgeschlagen."
        exit 1
    }
    Write-Log "Selbsttest $name OK."

    Write-Log "Hauptlauf $name..."
    & $pythonExe $runnerPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Hauptlauf $name fehlgeschlagen."
        exit 1
    }
    Write-Log "Hauptlauf $name abgeschlossen."

    if (Test-Path $checkPath) {
        Write-Log "Check $name..."
        & $pythonExe $checkPath
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Check $name fehlgeschlagen."
            exit 1
        }
        Write-Log "Check $name OK."
    }
}

Write-Log "=================================================="
Write-Log "CORE-14 BIS CORE-20 UMBAU-AUTOMANAGER"
Write-Log "=================================================="

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python nicht gefunden: $pythonExe"
    exit 1
}

# Schritt 1: CORE-14 Auswertung
Invoke-Step -name "CORE-14 Auswertung" -runner "core14_core13_auswertung.py" -check "check_core14_core13_auswertung.py"

# Schritt 2: CORE-15 Migrationsplan
Invoke-Step -name "CORE-15 Migrationsplan" -runner "core15_migrationsplan.py" -check "check_core15_migrationsplan.py"

# Schritt 3: CORE-16 Dry-Run Validierung
Invoke-Step -name "CORE-16 Dry-Run" -runner "core16_dry_run_validierung.py" -check "check_core16_dry_run_validierung.py"

# Schritt 4: CORE-17 Kopierende Migration
Invoke-Step -name "CORE-17 Kopierende Migration" -runner "core17_kopierende_migration.py" -check "check_core17_kopierende_migration.py"

# Schritt 5: CORE-18 Neustruktur Validierung
Invoke-Step -name "CORE-18 Neustruktur" -runner "core18_neustruktur_validierung.py" -check "check_core18_neustruktur_validierung.py"

# Schritt 6: CORE-19 Reste-/Archiv-/Sperrplan
Invoke-Step -name "CORE-19 Reste/Archiv/Sperr" -runner "core19_reste_archiv_sperrplan.py" -check "check_core19_reste_archiv_sperrplan.py"

# Schritt 7: CORE-20 Master-Bericht
Invoke-Step -name "CORE-20 Master-Bericht" -runner "core20_master_umbau_bericht.py" -check "check_core20_master_umbau_bericht.py"

Write-Log "=================================================="
Write-Log "ALLE SCHRITTE ERFOLGREICH ABGESCHLOSSEN"
Write-Log "=================================================="
Write-Log "Bericht: ALIN_Neustart_Core\Reports\CORE20_MASTER_UMBAU_BERICHT.txt"
