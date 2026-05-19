# Phase 0, AP 0.7: Network-Guard

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptRoot
$PythonConfigPath = Join-Path $BaseDir "Config\CORE02_python.config.json"

Write-Host "Phase 0, AP 0.7 Network-Guard starten" -ForegroundColor Cyan

$PythonExe = $null
if (Test-Path $PythonConfigPath) {
    $PythonConfig = Get-Content -Raw $PythonConfigPath | ConvertFrom-Json
    if ($PythonConfig.python_exe -and (Test-Path $PythonConfig.python_exe)) {
        $PythonExe = $PythonConfig.python_exe
    }
}

if (-not $PythonExe) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        $PythonExe = $PythonCommand.Source
    }
}

if (-not $PythonExe) {
    Write-Host "FEHLER: Kein Python-Laeufer gefunden." -ForegroundColor Red
    exit 1
}

$Runner = Join-Path $BaseDir "Scripts\python_runner\phase0_ap07_network_guard.py"
$Check = Join-Path $BaseDir "Scripts\python_runner\check_phase0_ap07_network_guard.py"

& $PythonExe $Runner
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Laeufer fehlgeschlagen." -ForegroundColor Red
    exit 1
}

& $PythonExe $Check
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Pruefung fehlgeschlagen." -ForegroundColor Red
    exit 1
}

Write-Host "Phase 0, AP 0.7 erfolgreich abgeschlossen" -ForegroundColor Green
