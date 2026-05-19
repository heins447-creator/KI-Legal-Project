# AP 1.3 — Bootstrapper: Alle 16 Tools pruefen und fehlende installieren
# Aufruf: .\Run_PHASE1_AP03_Bootstrapper.ps1 [-CheckOnly] [-Tool TOOL_ID]

param(
    [switch]$CheckOnly,
    [string]$Tool = ""
)

$ROOT = (Resolve-Path "$PSScriptRoot\..").Path
$PYTHON = "$ROOT\Tools\Python312\python.exe"
$RUNNER = "$ROOT\Scripts\python_runner\phase1_ap03_bootstrapper.py"

if (-not (Test-Path $PYTHON)) {
    Write-Error "Python nicht gefunden: $PYTHON"
    exit 1
}

$args_list = @($RUNNER)
if ($CheckOnly) { $args_list += "--check-only" }
if ($Tool) { $args_list += "--tool"; $args_list += $Tool }

Write-Host "=== AP 1.3: Bootstrapper ===" -ForegroundColor Cyan
& $PYTHON @args_list
$exit_code = $LASTEXITCODE

Write-Host ""
if ($exit_code -eq 0) {
    Write-Host "Bootstrapper abgeschlossen — alle Tools bereit." -ForegroundColor Green
} else {
    Write-Host "Bootstrapper FEHLER (Exit $exit_code)" -ForegroundColor Red
}

exit $exit_code
