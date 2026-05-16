# CORE-07 – Quellen- und Adapterregister Vervollständigung
# PowerShell-Starter
# Auftragsnummer: CORE-07

$ROOT = "I:\KI_Legal_Project"
$PY = "$ROOT\Tools\Python312\python.exe"
$CORE = "$ROOT\ALIN_Neustart_Core"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CORE-07 – Quellen-Adapterregister Befuellung" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Schritt 1: Befüllung und Abgleich
Write-Host "`n[1/2] Quellen-Adapterregister befuellen und abgleichen..." -ForegroundColor Yellow
& $PY "$CORE\Scripts\alin_core07_quellen_adapterregister_befuellen.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER beim Befuellen. Abbruch." -ForegroundColor Red
    exit 1
}

# Schritt 2: Prüfung
Write-Host "`n[2/2] Quellen-Adapterregister pruefen..." -ForegroundColor Yellow
& $PY "$CORE\Scripts\alin_core07_pruefung.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER bei der Pruefung." -ForegroundColor Red
    exit 1
}

Write-Host "`nCORE-07 erfolgreich abgeschlossen." -ForegroundColor Green
$BerichtPfad = "$CORE\Reports\ALIN_CORE07_QUELLEN_ADAPTERREGISTER_BERICHT.txt"
Write-Host "Bericht: $BerichtPfad" -ForegroundColor Green
