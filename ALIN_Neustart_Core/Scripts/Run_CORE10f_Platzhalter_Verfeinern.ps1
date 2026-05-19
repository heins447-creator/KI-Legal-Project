# CORE-10f – Platzhalter verfeinern
# PowerShell-Starter

$ROOT = "I:\KI_Legal_Project"
$PY = "$ROOT\Tools\Python312\python.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CORE-10f: Platzhalter-Eingabe/Ausgabe verfeinern" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 0. py_compile
Write-Host "`n[0/4] py_compile Prüfung..." -ForegroundColor Yellow
$compileErrors = 0
$scripts = @(
    "$ROOT\ALIN_Neustart_Core\Scripts\alin_core10f_platzhalter_verfeinern.py",
    "$ROOT\ALIN_Neustart_Core\Scripts\alin_core10f_pruefung.py"
)
foreach ($script in $scripts) {
    & $PY -m py_compile $script
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FEHLER bei $script" -ForegroundColor Red
        $compileErrors++
    } else {
        Write-Host "  OK: $script" -ForegroundColor Green
    }
}

# 1. Git-Status vorher
Write-Host "`n[1/4] Git-Status vorher..." -ForegroundColor Yellow
& git -C $ROOT status --short

# 2. Hauptlauf
Write-Host "`n[2/4] Hauptlauf wird ausgeführt..." -ForegroundColor Yellow
& $PY "$ROOT\ALIN_Neustart_Core\Scripts\alin_core10f_platzhalter_verfeinern.py"
$mainExit = $LASTEXITCODE

# 3. Prüfung
Write-Host "`n[3/4] Prüfung wird ausgeführt..." -ForegroundColor Yellow
& $PY "$ROOT\ALIN_Neustart_Core\Scripts\alin_core10f_pruefung.py"
$checkExit = $LASTEXITCODE

# 4. Git-Status nachher
Write-Host "`n[4/4] Git-Status nachher..." -ForegroundColor Yellow
& git -C $ROOT status --short

Write-Host "`n========================================" -ForegroundColor Cyan
if ($compileErrors -eq 0 -and $mainExit -eq 0 -and $checkExit -eq 0) {
    Write-Host "CORE-10f: ALLES BESTANDEN" -ForegroundColor Green
} else {
    Write-Host "CORE-10f: FEHLER AUFGETRETEN" -ForegroundColor Red
    Write-Host "py_compile Fehler: $compileErrors" -ForegroundColor Red
    Write-Host "Hauptlauf Exit-Code: $mainExit" -ForegroundColor Red
    Write-Host "Prüfung Exit-Code: $checkExit" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Cyan
