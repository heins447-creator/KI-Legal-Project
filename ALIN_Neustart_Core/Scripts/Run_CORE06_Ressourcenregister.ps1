# CORE-06 – Ressourcenregister Vervollständigung
# PowerShell-Starter
# Auftragsnummer: CORE-06

$ROOT = "I:\KI_Legal_Project"
$PY = "$ROOT\Tools\Python312\python.exe"
$CORE = "$ROOT\ALIN_Neustart_Core"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CORE-06 – Ressourcenregister Befüllung" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Schritt 1: Befüllung und Abgleich
Write-Host "`n[1/2] Ressourcenregister befüllen und abgleichen..." -ForegroundColor Yellow
& $PY "$CORE\Scripts\alin_core06_ressourcenregister_befuellen.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER beim Befüllen. Abbruch." -ForegroundColor Red
    exit 1
}

# Schritt 2: Prüfung
Write-Host "`n[2/2] Ressourcenregister prüfen..." -ForegroundColor Yellow
& $PY "$CORE\Scripts\alin_core06_pruefung.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER bei der Prüfung." -ForegroundColor Red
    exit 1
}

Write-Host "`nCORE-06 erfolgreich abgeschlossen." -ForegroundColor Green
Write-Host "Bericht: $CORE\Reports\ALIN_CORE06_RESSOURCENREGISTER_BERICHT.txt" -ForegroundColor Green
