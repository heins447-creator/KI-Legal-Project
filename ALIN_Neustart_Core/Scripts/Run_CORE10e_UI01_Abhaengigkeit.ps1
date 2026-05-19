# CORE-10e – fehlende Abhaengigkeit ui01_anwaltsansicht klaeren
# =============================================================
# Auftrag:  Pruefen und korrigieren der Abhaengigkeit in
#           check_ui01_anwaltsansicht_v1
# Grenzen:  Keine UI bauen, keine Altbestandsdateien aendern,
#           keine UI01 reparieren, keine DB-Aenderung, keine OCR,
#           keine Uebersetzung, keine Ressourcen, keine Schnittstellen.
# =============================================================

$ErrorActionPreference = "Stop"
$BaseDir = "ALIN_Neustart_Core"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CORE-10e – UI01 Abhaengigkeit klaeren" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Python-Analyseskript
$PythonScript = "$BaseDir\Scripts\alin_core10e_ui01_abhaengigkeit_klaeren.py"
Write-Host "`nStarte Analyse..." -ForegroundColor Yellow
& python $PythonScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Analyse fehlgeschlagen (Exit $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}

# Pruefdatei
$CheckScript = "$BaseDir\Scripts\alin_core10e_pruefung.py"
Write-Host "`nStarte Pruefdatei..." -ForegroundColor Yellow
& python $CheckScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Pruefdatei fehlgeschlagen (Exit $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "CORE-10e erfolgreich abgeschlossen" -ForegroundColor Green
Write-Host "Bericht: $BaseDir\Reports\ALIN_CORE10E_UI01_ABHAENGIGKEIT_BERICHT.txt" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
