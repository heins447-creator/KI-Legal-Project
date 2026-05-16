# KM21b-0 – Argos-Modellbereitstellung vorbereiten — AUTOLAUF
# Ordnerstruktur, Prüfschema, Importanleitung – KEIN Download, KEIN Internet.

$ProjectRoot = "I:\KI_Legal_Project"
$PythonRunner = Join-Path $ProjectRoot "Scripts\python_runner\km21b0_argos_modellbereitstellung.py"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "KM21b-0 – Argos-Modellbereitstellung" -ForegroundColor Cyan
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

Write-Host "[2] Hauptlauf (nur Vorbereitung, kein Download) ..." -ForegroundColor Yellow
& python $PythonRunner
$exit = $LASTEXITCODE

if ($exit -eq 0) {
    Write-Host "`nKM21b-0 VORBEREITUNG ABGESCHLOSSEN" -ForegroundColor Green
    Write-Host "Nächster Schritt: .argosmodel-Dateien manuell in Tools/Translation/Incoming/ ablegen." -ForegroundColor Cyan
} else {
    Write-Warning "Hauptlauf mit Fehlern beendet (Exit $exit)"
}
exit $exit
