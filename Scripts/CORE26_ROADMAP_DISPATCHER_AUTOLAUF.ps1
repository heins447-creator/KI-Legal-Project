# CORE-26: Roadmap-Dispatcher und Selbstfortsetzung - PowerShell Autolauf
# Setze PYTHON_EXE = I:\KI_Legal_Project\Tools\Python312\python.exe
# Wechsle in Projektverzeichnis
# Führe py_compile auf Runner und Check aus
# Führe Check aus
# Führe Runner aus
# Zeige Ergebnis

$PYTHON_EXE = "I:\KI_Legal_Project\Tools\Python312\python.exe"
$PROJECT_DIR = "I:\KI_Legal_Project"
$RUNNER = "Scripts\python_runner\core26_roadmap_dispatcher.py"
$CHECK = "Scripts\python_runner\check_core26_roadmap_dispatcher.py"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CORE-26: Roadmap-Dispatcher Autolauf" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Wechsle in Projektverzeichnis
Set-Location $PROJECT_DIR

# 1. py_compile auf Runner
Write-Host "`n[1/4] py_compile auf Runner..." -ForegroundColor Yellow
& $PYTHON_EXE -m py_compile $RUNNER
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: py_compile auf Runner fehlgeschlagen" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Runner py_compile erfolgreich" -ForegroundColor Green

# 2. py_compile auf Check
Write-Host "`n[2/4] py_compile auf Check..." -ForegroundColor Yellow
& $PYTHON_EXE -m py_compile $CHECK
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: py_compile auf Check fehlgeschlagen" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Check py_compile erfolgreich" -ForegroundColor Green

# 3. Check ausführen
Write-Host "`n[3/4] Check ausführen..." -ForegroundColor Yellow
& $PYTHON_EXE $CHECK
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Check fehlgeschlagen" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Check erfolgreich" -ForegroundColor Green

# 4. Runner ausführen
Write-Host "`n[4/4] Runner ausführen..." -ForegroundColor Yellow
& $PYTHON_EXE $RUNNER
$RUNNER_EXIT = $LASTEXITCODE
if ($RUNNER_EXIT -ne 0) {
    Write-Host "WARNUNG: Runner mit Exit-Code $RUNNER_EXIT beendet" -ForegroundColor Yellow
} else {
    Write-Host "OK: Runner erfolgreich" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CORE-26 Autolauf abgeschlossen" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

exit $RUNNER_EXIT
