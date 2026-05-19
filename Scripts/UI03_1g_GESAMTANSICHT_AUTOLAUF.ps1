# UI03-1g – Kombinierte Gesamtansicht AUTOLAUF
# Zusammenführt UI03-1b … 1f in ein Dashboard. Keine Neuberechnung, nur Aggregation.

$ProjectRoot = "I:\KI_Legal_Project"
$PythonRunner = Join-Path $ProjectRoot "Scripts\python_runner\ui03_1g_gesamtansicht.py"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "UI03-1g – Kombinierte Gesamtansicht" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (-not (Test-Path $PythonRunner)) {
    Write-Error "Python-Läufer nicht gefunden: $PythonRunner"
    exit 1
}

Write-Host "[1] Selbsttest ..." -ForegroundColor Yellow
& python $PythonRunner --selbsttest
if ($LASTEXITCODE -ne 0) {
    Write-Error "Selbsttest FEHLGESCHLAGEN (Exit $LASTEXITCODE)"
    exit 1
}

Write-Host "[2] Hauptlauf ..." -ForegroundColor Yellow
& python $PythonRunner
$exit = $LASTEXITCODE

if ($exit -eq 0) {
    Write-Host "`nUI03-1g GESAMTANSICHT ABGESCHLOSSEN" -ForegroundColor Green
} else {
    Write-Warning "Hauptlauf mit Fehlern beendet (Exit $exit)"
}
exit $exit
