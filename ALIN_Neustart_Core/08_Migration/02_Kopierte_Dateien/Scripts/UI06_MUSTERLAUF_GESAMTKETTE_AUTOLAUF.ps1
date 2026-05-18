# UI06 – Musterlauf Gesamtkette Autostart
# Posteingang -> Türschwelle -> Mandantenakte -> UI05-Arbeitszentrale

$ErrorActionPreference = "Stop"
$ROOT = "I:\KI_Legal_Project"
$PYTHON = "python"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "UI06 – Musterlauf Gesamtkette" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# [1] Python-Runner
Write-Host "`n[1] UI06 Python-Runner ..." -ForegroundColor Yellow
& $PYTHON "$ROOT\Scripts\python_runner\ui06_musterlauf_gesamtkette.py"
if ($LASTEXITCODE -ne 0) { throw "UI06 Python-Runner fehlgeschlagen" }

# [2] Selbsttest
Write-Host "`n[2] UI06 Selbsttest ..." -ForegroundColor Yellow
& $PYTHON "$ROOT\Scripts\python_runner\ui06_musterlauf_gesamtkette.py" --selbsttest
if ($LASTEXITCODE -ne 0) { throw "UI06 Selbsttest fehlgeschlagen" }

# [3] Prüfdatei
Write-Host "`n[3] UI06 Prüfdatei ..." -ForegroundColor Yellow
& $PYTHON "$ROOT\Scripts\python_runner\check_ui06_musterlauf_gesamtkette.py"
if ($LASTEXITCODE -ne 0) { throw "UI06 Prüfdatei fehlgeschlagen" }

# [4] Bericht anzeigen
Write-Host "`n[4] Bericht:" -ForegroundColor Yellow
$BERICHT = "$ROOT\Agentensteuerung\UI06_Musterlauf_Gesamtkette\03_Berichte\UI06_BERICHT.txt"
if (Test-Path $BERICHT) {
    Get-Content $BERICHT | Select-Object -First 30 | Write-Host
}

# [5] Browser öffnen
Write-Host "`n[5] Browseransicht öffnen ..." -ForegroundColor Yellow
$HTML = "$ROOT\Agentensteuerung\UI06_Musterlauf_Gesamtkette\11_Browseransicht\index.html"
if (Test-Path $HTML) {
    Start-Process $HTML
    Write-Host "Geöffnet: $HTML" -ForegroundColor Green
} else {
    Write-Host "HTML nicht gefunden" -ForegroundColor Red
}

Write-Host "`nUI06 ABGESCHLOSSEN" -ForegroundColor Green
