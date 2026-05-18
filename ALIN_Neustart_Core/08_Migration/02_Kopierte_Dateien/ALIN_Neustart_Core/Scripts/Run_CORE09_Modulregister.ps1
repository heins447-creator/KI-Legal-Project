# CORE-09 - Modulregister vervollstaendigen
# PowerShell-Starter

$ErrorActionPreference = "Stop"
$BaseDir = "I:\KI_Legal_Project\ALIN_Neustart_Core"
$ScriptsDir = "$BaseDir\Scripts"
$ReportsDir = "$BaseDir\Reports"
$Timestamp = Get-Date -Format "yyyy-MM-ddTHH-mm-ss"

# Python-Pfad aus Config oder Fallback
$ConfigPath = "$BaseDir\Config\CORE02_python.config.json"
$PythonExe = "I:\KI_Legal_Project\Tools\Python312\python.exe"
if (Test-Path $ConfigPath) {
    try {
        $cfg = Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($cfg.python_exe -and (Test-Path $cfg.python_exe)) {
            $PythonExe = $cfg.python_exe
        }
    } catch { }
}

Write-Host "========================================"
Write-Host "CORE-09 - Modulregister vervollstaendigen"
Write-Host "========================================"
Write-Host "Python: $PythonExe"
Write-Host ""

# 1. Git-Status vorher
Write-Host "--- Git-Status VORHER ---"
git -C "I:\KI_Legal_Project" status --short
Write-Host ""

# 2. Python-Befuellskript ausfuehren
Write-Host "--- Schritt 1: Modulregister befuellen ---"
& $PythonExe "$ScriptsDir\alin_core09_modulregister_befuellen.py"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Befuellskript fehlgeschlagen mit Exit-Code $LASTEXITCODE"
}
Write-Host ""

# 3. Python-Pruefskript ausfuehren
Write-Host "--- Schritt 2: Pruefung durchfuehren ---"
& $PythonExe "$ScriptsDir\alin_core09_pruefung.py"
$PruefExit = $LASTEXITCODE
Write-Host ""

# 4. Berichte anzeigen
Write-Host "--- Berichte ---"
$Bericht = "$ReportsDir\ALIN_CORE09_MODULREGISTER_BERICHT.txt"
$PruefBericht = "$ReportsDir\ALIN_CORE09_PRUEFBERICHT.txt"

if (Test-Path $Bericht) {
    Write-Host "Modulregister-Bericht: $Bericht"
    Get-Content $Bericht | Select-Object -First 30
} else {
    Write-Warning "Modulregister-Bericht nicht gefunden"
}
Write-Host ""

if (Test-Path $PruefBericht) {
    Write-Host "Pruefbericht: $PruefBericht"
    Get-Content $PruefBericht | Select-Object -First 30
} else {
    Write-Warning "Pruefbericht nicht gefunden"
}
Write-Host ""

# 5. Git-Status nachher
Write-Host "--- Git-Status NACHHER ---"
git -C "I:\KI_Legal_Project" status --short
Write-Host ""

# 6. Zusammenfassung
Write-Host "========================================"
Write-Host "ZUSAMMENFASSUNG"
Write-Host "========================================"
Write-Host "Pruefung Exit-Code: $PruefExit"
if ($PruefExit -eq 0) {
    Write-Host "Status: ERFOLGREICH"
    Write-Host "Hinweis: Kein Commit ohne Freigabe."
} else {
    Write-Host "Status: FEHLER - Pruefung nicht bestanden"
}
Write-Host "========================================"
