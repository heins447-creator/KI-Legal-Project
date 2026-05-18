# CORE-10c – SQL-Modulnamen bereinigen
# ====================================
# Auftrag:  20 Module im modulregister.json haben SQL-Code als modulname.
#           Diese werden auf den Dateinamen korrigiert.
# Grenzen:  Nur ALIN_Neustart_Core. Keine Ressourcen, Schnittstellen,
#           Abhaengigkeiten oder Altbestand.
# =================================================================

$ErrorActionPreference = "Stop"
$BaseDir = "ALIN_Neustart_Core"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CORE-10c – SQL-Modulnamen bereinigen" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Python-Skript ausfuehren
$PythonScript = "$BaseDir\Scripts\alin_core10c_sql_modulnamen_bereinigen.py"
Write-Host "`nStarte Bereinigung..." -ForegroundColor Yellow
& python $PythonScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Bereinigung fehlgeschlagen (Exit $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}

# Pruefdatei ausfuehren
$CheckScript = "$BaseDir\Scripts\check_alin_core10c_sql_modulnamen.py"
Write-Host "`nStarte Pruefdatei..." -ForegroundColor Yellow
& python $CheckScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Pruefdatei fehlgeschlagen (Exit $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "CORE-10c erfolgreich abgeschlossen" -ForegroundColor Green
Write-Host "Bericht: $BaseDir\Reports\ALIN_CORE10C_SQL_MODULNAMEN_BERICHT.txt" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
