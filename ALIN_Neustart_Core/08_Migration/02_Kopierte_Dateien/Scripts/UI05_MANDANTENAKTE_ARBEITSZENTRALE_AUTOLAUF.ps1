# CORE-05 – Mandantenakte Gesamtarbeitsplatz / Arbeitszentrale
# Autor: ALIN Agent
# Zweck: Zentrale Arbeitsseite für UI03 + UI04b

param(
    [switch]$Test
)

$ErrorActionPreference = "Stop"
$ROOT = "I:\KI_Legal_Project"
$PYTHON = (Get-Command python -ErrorAction SilentlyContinue).Source

if (-not $PYTHON) {
    $PYTHON = (Get-Command python3 -ErrorAction SilentlyContinue).Source
}
if (-not $PYTHON) {
    Write-Host "[FEHLER] Python nicht gefunden." -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "UI05 – Mandantenakte Arbeitszentrale" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($Test) {
    Write-Host "`n[SELBSTTEST]" -ForegroundColor Yellow
    & $PYTHON "$ROOT\Scripts\python_runner\ui05_mandantenakte_arbeitszentrale.py" --selbsttest
} else {
    Write-Host "`n[HAUPTLAUF]" -ForegroundColor Green
    & $PYTHON "$ROOT\Scripts\python_runner\ui05_mandantenakte_arbeitszentrale.py"
}

$exitCode = $LASTEXITCODE

Write-Host "`n========================================" -ForegroundColor Cyan
if ($exitCode -eq 0) {
    Write-Host "UI05 ABGESCHLOSSEN" -ForegroundColor Green
    $html = "$ROOT\Agentensteuerung\UI05_Mandantenakte_Arbeitszentrale\11_Browseransicht\index.html"
    if (Test-Path $html) {
        Write-Host "Browseransicht: $html" -ForegroundColor Gray
    }
} else {
    Write-Host "UI05 FEHLER (Exit $exitCode)" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Cyan

exit $exitCode
