# -*- coding: utf-8 -*-
<#
.CORE-21 ARBEITSINDEX AUTOLAUF
Erstellt den Umschalt- und Arbeitsindex für ALIN_Neustart_Core.
#>

$ErrorActionPreference = "Stop"
$PythonExe = "I:\KI_Legal_Project\Tools\Python312\python.exe"
$Runner = "I:\KI_Legal_Project\Scripts\python_runner\core21_arbeitsindex.py"
$Checker = "I:\KI_Legal_Project\Scripts\python_runner\check_core21_arbeitsindex.py"

function Write-Header {
    param([string]$Text)
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

Write-Header "CORE-21: ARBEITSINDEX AUTOLAUF"

# 1. py_compile auf Runner
Write-Host "`n[1/5] py_compile auf core21_arbeitsindex.py ..." -ForegroundColor Yellow
& $PythonExe -m py_compile $Runner
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: py_compile für Runner fehlgeschlagen" -ForegroundColor Red
    exit 1
}
Write-Host "OK – Runner kompiliert." -ForegroundColor Green

# 2. py_compile auf Checker
Write-Host "`n[2/5] py_compile auf check_core21_arbeitsindex.py ..." -ForegroundColor Yellow
& $PythonExe -m py_compile $Checker
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: py_compile für Checker fehlgeschlagen" -ForegroundColor Red
    exit 1
}
Write-Host "OK – Checker kompiliert." -ForegroundColor Green

# 3. Runner ausführen
Write-Host "`n[3/5] core21_arbeitsindex.py ausführen ..." -ForegroundColor Yellow
& $PythonExe $Runner
$runnerExit = $LASTEXITCODE
if ($runnerExit -ne 0) {
    Write-Host "FEHLER: Runner mit Exit-Code $runnerExit beendet" -ForegroundColor Red
    exit $runnerExit
}
Write-Host "OK – Runner erfolgreich." -ForegroundColor Green

# 4. Check ausführen
Write-Host "`n[4/5] check_core21_arbeitsindex.py ausführen ..." -ForegroundColor Yellow
& $PythonExe $Checker
$checkExit = $LASTEXITCODE
if ($checkExit -ne 0) {
    Write-Host "FEHLER: Check mit Exit-Code $checkExit beendet" -ForegroundColor Red
    exit $checkExit
}
Write-Host "OK – Check erfolgreich." -ForegroundColor Green

# 5. Zusammenfassung
Write-Host "`n[5/5] Zusammenfassung" -ForegroundColor Yellow
Write-Host "  Arbeitsindex:  ALIN_Neustart_Core\08_Migration\09_Manifest\CORE21_arbeitsindex.json" -ForegroundColor White
Write-Host "  Bericht:       ALIN_Neustart_Core\Reports\CORE21_ARBEITSINDEX_BERICHT.txt" -ForegroundColor White
Write-Host "  Konfiguration: Config\core21_arbeitsindex_v1.json" -ForegroundColor White
Write-Host "  Git-Status vor: ALIN_Neustart_Core\08_Migration\09_Manifest\CORE21_git_status_vor.txt" -ForegroundColor White
Write-Host "  Git-Status nach: ALIN_Neustart_Core\08_Migration\09_Manifest\CORE21_git_status_nach.txt" -ForegroundColor White

Write-Header "CORE-21 AUTOLAUF ABGESCHLOSSEN"
Write-Host "Alle Prüfungen bestanden. Bereit für Git-Commit." -ForegroundColor Green
