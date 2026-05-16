#Requires -Version 5.1
<#
.SYNOPSIS
    CORE-02 - Altbestand lesend inventarisieren und Register befuellen

.DESCRIPTION
    Startet den Python-Laeufer alin_core02_altbestand_inventar.py
    und anschliessend die Pruefdatei alin_core02_pruefung.py.
    Alle Ausgaben landen unter ALIN_Neustart_Core/Reports/.

.HARTE GRENZEN
    - Keine Aenderungen am Altbestand.
    - Nur Dateien unter ALIN_Neustart_Core/ werden geschrieben.
#>

$ErrorActionPreference = "Stop"
$CoreDir = "I:\KI_Legal_Project\ALIN_Neustart_Core"
$ScriptsDir = "$CoreDir\Scripts"
$ReportsDir = "$CoreDir\Reports"
$ConfigFile = "$CoreDir\Config\CORE02_python.config.json"

New-Item -ItemType Directory -Force -Path $ReportsDir | Out-Null
New-Item -ItemType Directory -Force -Path "$CoreDir\Config" | Out-Null

# Python-Interpreter finden
$PyExe = $null
$PyCandidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"),
    (Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\python.exe"),
    (Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\python3.exe"),
    "C:\Python313\python.exe",
    "C:\Python312\python.exe",
    "C:\Python311\python.exe"
)
foreach ($c in $PyCandidates) {
    if (Test-Path $c) {
        $PyExe = $c
        break
    }
}

# Config-Datei pruefen
if (Test-Path $ConfigFile) {
    try {
        $Config = Get-Content $ConfigFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($Config.python_exe -and (Test-Path $Config.python_exe)) {
            $PyExe = $Config.python_exe
        }
    } catch {
        Write-Warning "Config-Datei konnte nicht gelesen werden."
    }
}

if (-not $PyExe) {
    Write-Error "Python-Interpreter nicht gefunden. Bitte Pfad in $ConfigFile eintragen."
    exit 1
}

$Sep = "=" * 70

Write-Host $Sep
Write-Host "CORE-02 - Altbestand lesend inventarisieren und Register befuellen"
Write-Host "Python-Interpreter: $PyExe"
Write-Host $Sep

# --- Schritt 1: Inventarisierung ---
Write-Host "`n[1/2] Inventarisierung wird gestartet..." -ForegroundColor Cyan
$InventarScript = "$ScriptsDir\alin_core02_altbestand_inventar.py"
if (-not (Test-Path $InventarScript)) {
    throw "Inventar-Skript nicht gefunden: $InventarScript"
}

& $PyExe "$InventarScript"
if ($LASTEXITCODE -ne 0) {
    throw "Inventarisierung fehlgeschlagen (Exit-Code $LASTEXITCODE)."
}
Write-Host "Inventarisierung erfolgreich." -ForegroundColor Green

# --- Schritt 2: Pruefung ---
Write-Host "`n[2/2] Pruefung wird gestartet..." -ForegroundColor Cyan
$PruefScript = "$ScriptsDir\alin_core02_pruefung.py"
if (-not (Test-Path $PruefScript)) {
    throw "Pruef-Skript nicht gefunden: $PruefScript"
}

& $PyExe "$PruefScript"
$PruefExit = $LASTEXITCODE
if ($PruefExit -ne 0) {
    Write-Warning "Pruefung mit Fehlern abgeschlossen (Exit-Code $PruefExit)."
} else {
    Write-Host "Pruefung erfolgreich. Keine Fehler." -ForegroundColor Green
}

Write-Host "`n$Sep"
Write-Host "CORE-02 abgeschlossen."
Write-Host "Berichte: $ReportsDir"
Write-Host "  - ALIN_CORE02_ALTBESTAND_INVENTAR_BERICHT.txt"
Write-Host "  - ALIN_CORE02_PRUEFBERICHT.txt"
Write-Host $Sep

exit $PruefExit
