# CORE-10a – Findings priorisieren und Reparaturauftraege ableiten
# =================================================================
# Auftrag:  P0-P3-Priorisierung der 551 CORE-10-Findings erstellen
#           KEINE Registeraenderungen – nur Analyse und Planung
# =================================================================

$ErrorActionPreference = "Stop"
$BaseDir = "ALIN_Neustart_Core"
$ReportsDir = "$BaseDir\Reports"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CORE-10a – Findings-Priorisierung" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Verzeichnisse sicherstellen
New-Item -ItemType Directory -Force -Path $ReportsDir | Out-Null

# Python-Skript ausfuehren
$PythonScript = "$BaseDir\Scripts\alin_core10a_findings_priorisierung.py"
Write-Host "`nStarte Analyse-Skript..." -ForegroundColor Yellow
& python $PythonScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Analyse-Skript fehlgeschlagen (Exit $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}

# Pruefdatei ausfuehren
$CheckScript = "$BaseDir\Scripts\check_alin_core10a_findings_priorisierung.py"
Write-Host "`nStarte Pruefdatei..." -ForegroundColor Yellow
& python $CheckScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Pruefdatei fehlgeschlagen (Exit $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "CORE-10a erfolgreich abgeschlossen" -ForegroundColor Green
Write-Host "Bericht: $ReportsDir\ALIN_CORE10A_FINDINGS_PRIORISIERUNG_BERICHT.txt" -ForegroundColor Green
Write-Host "JSON:    $ReportsDir\ALIN_CORE10A_PRIORISIERUNG.json" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
