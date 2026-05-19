# CORE-10b – Ressourcenlücken klären
# PowerShell-Starter

$ROOT = "I:\KI_Legal_Project"
$PY = "$ROOT\Tools\Python312\python.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CORE-10b: Ressourcenlücken klären" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Analyse
Write-Host "`n[1/2] Analyse wird ausgeführt..." -ForegroundColor Yellow
& $PY "$ROOT\ALIN_Neustart_Core\Scripts\alin_core10b_ressourcenluecken_klaeren.py"
$analysisExit = $LASTEXITCODE

# 2. Prüfung
Write-Host "`n[2/2] Prüfung wird ausgeführt..." -ForegroundColor Yellow
& $PY "$ROOT\ALIN_Neustart_Core\Scripts\alin_core10b_pruefung.py"
$checkExit = $LASTEXITCODE

Write-Host "`n========================================" -ForegroundColor Cyan
if ($analysisExit -eq 0 -and $checkExit -eq 0) {
    Write-Host "CORE-10b: ALLES BESTANDEN" -ForegroundColor Green
} else {
    Write-Host "CORE-10b: FEHLER AUFGETRETEN" -ForegroundColor Red
    Write-Host "Analyse Exit-Code: $analysisExit" -ForegroundColor Red
    Write-Host "Prüfung Exit-Code: $checkExit" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Cyan
