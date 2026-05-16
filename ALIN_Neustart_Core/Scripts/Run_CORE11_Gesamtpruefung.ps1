# CORE-11 – Gesamtprüfung und Abnahme
# PowerShell-Starter

$ROOT = "I:\KI_Legal_Project"
$PY = "$ROOT\Tools\Python312\python.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CORE-11: Gesamtprüfung und Abnahmebericht" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 0. py_compile
Write-Host "`n[0/3] py_compile Prüfung..." -ForegroundColor Yellow
& $PY -m py_compile "$ROOT\ALIN_Neustart_Core\Scripts\alin_core11_gesamtpruefung.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FEHLER bei alin_core11_gesamtpruefung.py" -ForegroundColor Red
    exit 1
} else {
    Write-Host "  OK: alin_core11_gesamtpruefung.py" -ForegroundColor Green
}

# 1. Git-Status vorher
Write-Host "`n[1/3] Git-Status vorher..." -ForegroundColor Yellow
& git -C $ROOT status --short

# 2. Hauptlauf
Write-Host "`n[2/3] Gesamtprüfung wird ausgeführt..." -ForegroundColor Yellow
& $PY "$ROOT\ALIN_Neustart_Core\Scripts\alin_core11_gesamtpruefung.py"
$mainExit = $LASTEXITCODE

# 3. Git-Status nachher
Write-Host "`n[3/3] Git-Status nachher..." -ForegroundColor Yellow
& git -C $ROOT status --short

Write-Host "`n========================================" -ForegroundColor Cyan
if ($mainExit -eq 0) {
    Write-Host "CORE-11: ABNAHME EMPFOHLEN" -ForegroundColor Green
} else {
    Write-Host "CORE-11: PRUEFUNG FEHLGESCHLAGEN" -ForegroundColor Red
    Write-Host "Exit-Code: $mainExit" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Cyan
