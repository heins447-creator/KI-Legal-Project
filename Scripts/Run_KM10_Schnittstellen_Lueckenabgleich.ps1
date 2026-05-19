# PowerShell-Starter KM10 – Schnittstellen- und Lueckenabgleich
# ================================================================
# Zweck: Startet den Python-Runner und die Pruefdatei.
#
# Pfad:  Scripts\Run_KM10_Schnittstellen_Lueckenabgleich.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = "I:\KI_Legal_Project"
$Python = "$ProjectRoot\Tools\Python312\python.exe"
$Runner = "$ProjectRoot\Scripts\python_runner\km10_schnittstellen_lueckenabgleich.py"
$Check = "$ProjectRoot\Scripts\python_runner\check_km10_schnittstellen_lueckenabgleich.py"

# Skript-Verzeichnis existiert?
if (-not (Test-Path "$ProjectRoot\Scripts\python_runner")) {
    Write-Warning "python_runner-Verzeichnis fehlt. Bitte Projektstruktur pruefen."
}

# Kopiere Runner in python_runner, falls nicht dort
if (-not (Test-Path $Runner)) {
    Write-Host "Kopiere km10_schnittstellen_lueckenabgleich.py nach Scripts\python_runner..."
    Copy-Item -Path "$ProjectRoot\Agentensteuerung\10_Schnittstellen_Lueckenabgleich_Dokumentenstrasse\01_Skript\km10_schnittstellen_lueckenabgleich.py" -Destination $Runner -Force
}

if (-not (Test-Path $Check)) {
    Write-Host "Kopiere check_km10_schnittstellen_lueckenabgleich.py nach Scripts\python_runner..."
    Copy-Item -Path "$ProjectRoot\Agentensteuerung\10_Schnittstellen_Lueckenabgleich_Dokumentenstrasse\01_Skript\check_km10_schnittstellen_lueckenabgleich.py" -Destination $Check -Force
}

Write-Host "================================================================"
Write-Host "KLEINMODUL 10 – SCHNITTSTELLEN- UND LUECKENABGLEICH"
Write-Host "================================================================"
Write-Host ""

# 1. Runner starten
Write-Host "[1/2] Runner: km10_schnittstellen_lueckenabgleich.py"
Write-Host "------------------------------------------------------------"
& $Python $Runner
$RunnerExit = $LASTEXITCODE
Write-Host "Runner ExitCode: $RunnerExit"
Write-Host ""

# 2. Check starten
Write-Host "[2/2] Check: check_km10_schnittstellen_lueckenabgleich.py"
Write-Host "------------------------------------------------------------"
& $Python $Check
$CheckExit = $LASTEXITCODE
Write-Host "Check ExitCode: $CheckExit"
Write-Host ""

Write-Host "================================================================"
Write-Host "ERGEBNIS"
Write-Host "================================================================"
Write-Host "Berichte: I:\KI_Legal_Project\Agentensteuerung\10_Schnittstellen_Lueckenabgleich_Dokumentenstrasse\03_Berichte"
Write-Host "Status:   I:\KI_Legal_Project\Agentensteuerung\10_Schnittstellen_Lueckenabgleich_Dokumentenstrasse\02_Status"
Write-Host "Artefakte: I:\KI_Legal_Project\Agentensteuerung\10_Schnittstellen_Lueckenabgleich_Dokumentenstrasse\06_Artefakte"
Write-Host ""

if ($RunnerExit -eq 0 -and $CheckExit -eq 0) {
    Write-Host "KM10 ERFOLGREICH ABGESCHLOSSEN" -ForegroundColor Green
} else {
    Write-Host "KM10 MIT FEHLERN ABGESCHLOSSEN" -ForegroundColor Yellow
    Write-Host "Runner ExitCode: $RunnerExit, Check ExitCode: $CheckExit"
}

exit $CheckExit
