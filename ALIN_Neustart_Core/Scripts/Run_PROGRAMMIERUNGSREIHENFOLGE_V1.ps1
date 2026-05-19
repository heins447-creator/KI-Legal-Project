# PROGRAMMIERUNGSREIHENFOLGE_V1
# Erzeugt und prueft die verbindliche weitere Programmierungsreihenfolge.

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptRoot

Write-Host "PROGRAMMIERUNGSREIHENFOLGE_V1 starten" -ForegroundColor Cyan

$Runner = Join-Path $BaseDir "Scripts\python_runner\programmierungsreihenfolge_v1.py"
$Check = Join-Path $BaseDir "Scripts\python_runner\check_programmierungsreihenfolge_v1.py"

$PythonCandidates = @()
$PythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($PythonCommand) {
    $PythonCandidates += $PythonCommand.Source
}
$BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (Test-Path $BundledPython) {
    $PythonCandidates += $BundledPython
}
$PyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($PyLauncher) {
    $PythonCandidates += $PyLauncher.Source
}
if ($PythonCandidates.Count -eq 0) {
    Write-Host "FEHLER: Kein Python-Laeufer gefunden (python oder py)." -ForegroundColor Red
    exit 1
}
$PythonExe = $PythonCandidates[0]

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

Write-Host "PROGRAMMIERUNGSREIHENFOLGE_V1 erfolgreich abgeschlossen" -ForegroundColor Green
