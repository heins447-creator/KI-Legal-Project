#=============================================================================
# KM19_OCR_GESAMTKETTE_SYNCHRONISIEREN_AUTOLAUF.ps1
#=============================================================================
# Zweck: Synchronisiert KM17c-Einzelseitenergebnis in KM13 und KM17,
#         fuehrt KM14 und KM15 neu aus, schreibt Vergleichs-, 
#         Rueckbindungs- und Berichtsausgaben.
# Schreibbereich: Agentensteuerung\19_OCR_Gesamtkette_Synchronisieren
#=============================================================================

$ErrorActionPreference = "Stop"
$Python = "I:\KI_Legal_Project\Tools\Python312\python.exe"
$Runner = "I:\KI_Legal_Project\Scripts\python_runner\km19_ocr_gesamtkette_synchronisieren.py"
$Checker = "I:\KI_Legal_Project\Scripts\python_runner\check_km19_ocr_gesamtkette_synchronisieren.py"
$Bereich = "I:\KI_Legal_Project\Agentensteuerung\19_OCR_Gesamtkette_Synchronisieren"

Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host "KM19 – OCR-GESAMTKETTE SYNCHRONISIEREN – AUTOLAUF" -ForegroundColor Cyan
Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Selbsttest
Write-Host "[SCHRITT 1/4] Selbsttest..." -ForegroundColor Yellow
$selbsttestExit = & $Python $Runner --selbsttest 2>&1
$selbsttestRC = $LASTEXITCODE
Write-Host $selbsttestExit
if ($selbsttestRC -ne 0) {
    Write-Host "SELBSTTEST FEHLGESCHLAGEN. Abbruch." -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. Hauptlauf
Write-Host "[SCHRITT 2/4] Hauptlauf..." -ForegroundColor Yellow
$hauptExit = & $Python $Runner 2>&1
$hauptRC = $LASTEXITCODE
Write-Host $hauptExit
if ($hauptRC -ne 0) {
    Write-Host "HAUPTLAUF MIT FEHLER BEENDET (rc=$hauptRC). Pruefung laeuft trotzdem." -ForegroundColor Yellow
}
Write-Host ""

# 3. Pruefdatei
Write-Host "[SCHRITT 3/4] Pruefdatei..." -ForegroundColor Yellow
$checkExit = & $Python $Checker 2>&1
$checkRC = $LASTEXITCODE
Write-Host $checkExit
Write-Host ""

# 4. Zusammenfassung
Write-Host "[SCHRITT 4/4] Zusammenfassung..." -ForegroundColor Yellow
$logDatei = "$Bereich\90_RunLogs\autolauf_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
"=== KM19 AUTOLAUF LOG ===" | Out-File -FilePath $logDatei -Encoding UTF8
"Datum: $(Get-Date -Format 'o')" | Out-File -FilePath $logDatei -Append -Encoding UTF8
"Selbsttest: rc=$selbsttestRC" | Out-File -FilePath $logDatei -Append -Encoding UTF8
"Hauptlauf:  rc=$hauptRC" | Out-File -FilePath $logDatei -Append -Encoding UTF8
"Pruefdatei: rc=$checkRC" | Out-File -FilePath $logDatei -Append -Encoding UTF8
Write-Host "Log: $logDatei"

Write-Host ""
Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host "KM19 AUTOLAUF ABGESCHLOSSEN" -ForegroundColor Cyan
Write-Host "=============================================================================" -ForegroundColor Cyan

if ($checkRC -ne 0) {
    Write-Host "Pruefdatei meldet Fehler – bitte KM19_FEHLER.txt prüfen." -ForegroundColor Red
    exit 1
}
Write-Host "Alle Pruefungen bestanden." -ForegroundColor Green
exit 0
