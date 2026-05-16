# CORE-10 Konsistenzpruefung – PowerShell-Starter
# Achtung: Keine Umlaute in Kommentaren/Strings (Encoding-Kompatibilitaet)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$coreDir = Split-Path -Parent $scriptDir

# Python-Config laden
$configPath = Join-Path $coreDir "Config\CORE02_python.config.json"
if (-not (Test-Path $configPath)) {
    Write-Error "Config nicht gefunden: $configPath"
    exit 1
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json
$pythonExe = $config.python_exe

if (-not $pythonExe -or -not (Test-Path $pythonExe)) {
    # Fallback: py.exe
    $pythonExe = "py.exe"
}

$pruefSkript = Join-Path $scriptDir "alin_core10_konsistenz_pruefung.py"
if (-not (Test-Path $pruefSkript)) {
    Write-Error "Pruefskript nicht gefunden: $pruefSkript"
    exit 1
}

Write-Host "========================================"
Write-Host "CORE-10 Konsistenzpruefung"
Write-Host "========================================"
Write-Host "Python: $pythonExe"
Write-Host "Skript: $pruefSkript"
Write-Host ""

# Skript ausfuehren
& $pythonExe "$pruefSkript"
$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "========================================"
if ($exitCode -eq 0) {
    Write-Host "Ergebnis: ALLE PRUEFUNGEN BESTANDEN"
} else {
    Write-Host "Ergebnis: FINDINGS VORHANDEN (Exit-Code $exitCode)"
}
Write-Host "========================================"

# Git-Status anzeigen (nur lesend, kein Commit)
Write-Host ""
Write-Host "--- Git-Status (nur Anzeige) ---"
$gitDir = Join-Path $coreDir ".."
try {
    Push-Location $gitDir
    git status --short
    Pop-Location
} catch {
    Write-Host "Git-Status konnte nicht ermittelt werden."
}

Write-Host ""
Write-Host "CORE-10 abgeschlossen."
exit $exitCode
