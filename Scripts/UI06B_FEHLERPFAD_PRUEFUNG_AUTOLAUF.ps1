# UI06b – Fehlerpfadprüfung Autostart
# Systematische Prüfung von 5 Szenarien

$ErrorActionPreference = "Stop"
$ROOT = "I:\KI_Legal_Project"
$PYTHON = "python"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "UI06b – Fehlerpfadprüfung" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# [1] Python-Runner
Write-Host "`n[1] UI06b Python-Runner ..." -ForegroundColor Yellow
& $PYTHON "$ROOT\Scripts\python_runner\ui06b_fehlerpfad_pruefung.py"
if ($LASTEXITCODE -ne 0) { throw "UI06b Python-Runner fehlgeschlagen" }

# [2] Selbsttest
Write-Host "`n[2] UI06b Selbsttest ..." -ForegroundColor Yellow
& $PYTHON "$ROOT\Scripts\python_runner\ui06b_fehlerpfad_pruefung.py" --selbsttest
if ($LASTEXITCODE -ne 0) { throw "UI06b Selbsttest fehlgeschlagen" }

# [3] Prüfdatei
Write-Host "`n[3] UI06b Prüfdatei ..." -ForegroundColor Yellow
& $PYTHON "$ROOT\Scripts\python_runner\check_ui06b_fehlerpfad_pruefung.py"
if ($LASTEXITCODE -ne 0) { throw "UI06b Prüfdatei fehlgeschlagen" }

# [4] Bericht anzeigen
Write-Host "`n[4] Bericht:" -ForegroundColor Yellow
$BERICHT = "$ROOT\Agentensteuerung\UI06b_Fehlerpfad_Pruefung\03_Berichte\UI06b_BERICHT.txt"
if (Test-Path $BERICHT) {
    Get-Content $BERICHT | Select-Object -First 40 | Write-Host
}

# [5] Browser öffnen
Write-Host "`n[5] Browseransicht öffnen ..." -ForegroundColor Yellow
$HTML = "$ROOT\Agentensteuerung\UI06b_Fehlerpfad_Pruefung\11_Browseransicht\index.html"
if (Test-Path $HTML) {
    Start-Process $HTML
    Write-Host "Geöffnet: $HTML" -ForegroundColor Green
} else {
    Write-Host "HTML nicht gefunden" -ForegroundColor Red
}

Write-Host "`nUI06b ABGESCHLOSSEN" -ForegroundColor Green
