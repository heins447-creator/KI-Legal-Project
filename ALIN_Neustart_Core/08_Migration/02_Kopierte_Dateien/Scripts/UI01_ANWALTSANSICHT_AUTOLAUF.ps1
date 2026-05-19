# UI01_ANWALTSANSICHT_AUTOLAUF.ps1
# Anwaltliche Dokumentenvorlage V1 im Browser
# ============================================

$ErrorActionPreference = "Stop"
$Root = "I:\KI_Legal_Project"
$Python = "$Root\Tools\Python312\python.exe"
$Runner = "$Root\Scripts\python_runner\ui01_anwaltsansicht_v1.py"
$Checker = "$Root\Scripts\python_runner\check_ui01_anwaltsansicht_v1.py"
$IndexHtml = "$Root\Agentensteuerung\UI01_Anwaltsansicht_V1\10_Browseransicht\index.html"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  UI01 – ANWALTSANSICHT V1 AUTOLAUF" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Git-Status vorher
Write-Host "[GIT] Status vorher:" -ForegroundColor Gray
git -C $Root status --porcelain 2>$null | Select-Object -First 5
Write-Host ""

# 1. py_compile
Write-Host "[1/4] py_compile Runner..." -ForegroundColor Yellow
& $Python -c "import py_compile; py_compile.compile(r'$Runner', doraise=True); print('py_compile OK')"
if ($LASTEXITCODE -ne 0) { Write-Host "FEHLER: py_compile" -ForegroundColor Red; exit 1 }
Write-Host "  OK" -ForegroundColor Green

# 2. Selbsttest
Write-Host "[2/4] Selbsttest..." -ForegroundColor Yellow
& $Python $Runner --selbsttest
if ($LASTEXITCODE -ne 0) { Write-Host "FEHLER: Selbsttest" -ForegroundColor Red; exit 1 }
Write-Host "  OK" -ForegroundColor Green

# 3. Hauptlauf
Write-Host "[3/4] Hauptlauf..." -ForegroundColor Yellow
& $Python $Runner
if ($LASTEXITCODE -ne 0) { Write-Host "FEHLER: Hauptlauf" -ForegroundColor Red; exit 1 }
Write-Host "  OK" -ForegroundColor Green

# 4. Pruefdatei
Write-Host "[4/4] Pruefdatei..." -ForegroundColor Yellow
& $Python $Checker
if ($LASTEXITCODE -ne 0) { Write-Host "FEHLER: Pruefdatei" -ForegroundColor Red; exit 1 }
Write-Host "  OK" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  UI01 Autolauf ERFOLGREICH" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Browseransicht:" -ForegroundColor Cyan
Write-Host "  $IndexHtml" -ForegroundColor White
Write-Host ""

# Optional: Browser oeffnen
try {
    Start-Process $IndexHtml
    Write-Host "Browser geoeffnet." -ForegroundColor Green
} catch {
    Write-Host "Browser konnte nicht automatisch geoeffnet werden. Bitte manuell oeffnen." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Git-Commit manuell oder via: git add -A && git commit -m 'UI01 Anwaltsansicht V1 fuer erstes Dokument erstellt'" -ForegroundColor Gray
