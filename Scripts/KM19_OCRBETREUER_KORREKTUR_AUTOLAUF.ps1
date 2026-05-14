# KM19_OCRBETREUER_KORREKTUR_AUTOLAUF.ps1
# ==========================================
# Startet KM19 (OCR-Betreuer-Korrekturlauf),
# prueft Ergebnisse, schreibt Log.

$ErrorActionPreference = "Stop"
$ROOT = "I:\KI_Legal_Project"
$PYTHON = "$ROOT\Tools\Python312\python.exe"
$RUNNER = "$ROOT\Scripts\python_runner\km19_ocrbetreuer_korrektur.py"
$CHECK  = "$ROOT\Scripts\python_runner\check_km19_ocrbetreuer_korrektur.py"
$LOGDIR = "$ROOT\Windows_App\Logs"
$TIMESTAMP = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$LOGFILE = "$LOGDIR\KM19_AUTOLAUF_$TIMESTAMP.txt"

Write-Host "KM19 Autolauf start: $TIMESTAMP" -ForegroundColor Cyan
Write-Host "Python: $PYTHON" -ForegroundColor Gray
Write-Host "Runner: $RUNNER" -ForegroundColor Gray

# 1. Runner ausfuehren
Write-Host "`n[1/3] KM19 Runner wird ausgefuehrt..." -ForegroundColor Yellow
& $PYTHON $RUNNER 2>&1 | Tee-Object -FilePath $LOGFILE
if ($LASTEXITCODE -ne 0) {
    Write-Host "KM19 Runner exits with code $LASTEXITCODE" -ForegroundColor Red
}

# 2. Check ausfuehren
Write-Host "`n[2/3] KM19 Check wird ausgefuehrt..." -ForegroundColor Yellow
& $PYTHON $CHECK 2>&1 | Tee-Object -FilePath $LOGFILE -Append
if ($LASTEXITCODE -ne 0) {
    Write-Host "KM19 Check exits with code $LASTEXITCODE" -ForegroundColor Red
} else {
    Write-Host "KM19 Check: ALL OK" -ForegroundColor Green
}

# 3. Statusdatei
Write-Host "`n[3/3] KM19 Status:" -ForegroundColor Yellow
Get-Content "$ROOT\Agentensteuerung\19_OCR_Betreuer_Korrektur\02_Status\KM19_STATUS.json" | Write-Host -ForegroundColor Gray

Write-Host "`nKM19 Autolauf abgeschlossen: $TIMESTAMP" -ForegroundColor Cyan
Write-Host "Log: $LOGFILE" -ForegroundColor Gray
