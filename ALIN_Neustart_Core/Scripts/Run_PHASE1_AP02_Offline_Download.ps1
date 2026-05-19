# AP 1.2 — Werkzeuge offline herunterladen und SHA-256 pruefen
# Aufruf: .\Run_PHASE1_AP02_Offline_Download.ps1 [-DryRun] [-Tool TOOL_ID]

param(
    [switch]$DryRun,
    [string]$Tool = ""
)

$ROOT = (Resolve-Path "$PSScriptRoot\..").Path
$PYTHON = "$ROOT\Tools\Python312\python.exe"
$RUNNER = "$ROOT\Scripts\python_runner\phase1_ap02_offline_download.py"

if (-not (Test-Path $PYTHON)) {
    Write-Error "Python nicht gefunden: $PYTHON"
    exit 1
}

$args_list = @($RUNNER)
if ($DryRun) { $args_list += "--dry-run" }
if ($Tool) { $args_list += "--tool"; $args_list += $Tool }

Write-Host "=== AP 1.2: Offline-Download ===" -ForegroundColor Cyan
Write-Host "Python: $PYTHON"
Write-Host "Runner: $RUNNER"
if ($DryRun) { Write-Host "[DRY-RUN Modus]" -ForegroundColor Yellow }

& $PYTHON @args_list
$exit_code = $LASTEXITCODE

Write-Host ""
if ($exit_code -eq 0) {
    Write-Host "AP 1.2 abgeschlossen." -ForegroundColor Green
} else {
    Write-Host "AP 1.2 FEHLER (Exit $exit_code)" -ForegroundColor Red
}

exit $exit_code
