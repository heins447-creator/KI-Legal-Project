# CORE-13 – Automatische Altbestandsinventur und Vor-Klassifikation
# PowerShell-Starter (read-only, berührt keine Originaldateien)
# Rote Linie: produktiv_freigegeben=false, nur_musterdaten=true, echte_daten_erlaubt=false

$ErrorActionPreference = "Stop"
$ProjektWurzel = "I:\KI_Legal_Project"
$PythonExe   = "$ProjektWurzel\Tools\Python312\python.exe"
$Runner      = "$ProjektWurzel\Scripts\python_runner\core13_altbestand_inventur.py"
$Check       = "$ProjektWurzel\Scripts\python_runner\check_core13_altbestand_inventur.py"

function Write-Header($text) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host $text -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

function Test-PythonSyntax($path) {
    Write-Host "[INFO] py_compile: $path"
    & $PythonExe -m py_compile $path
    if ($LASTEXITCODE -ne 0) { throw "SYNTAXFEHLER in $path" }
    Write-Host "[OK]   Syntax OK" -ForegroundColor Green
}

Set-Location $ProjektWurzel

Write-Header "CORE-13 ALTBESTAND INVENTUR – START"
Write-Host "Zeitstempel: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "Python:      $PythonExe"
Write-Host "Runner:      $Runner"
Write-Host "Check:       $Check"

# --- 1. Syntax-Prüfung ---
Write-Header "SCHRITT 1: Syntax-Prüfung"
Test-PythonSyntax $Runner
Test-PythonSyntax $Check

# --- 2. Check-Datei ---
Write-Header "SCHRITT 2: Check-Datei"
& $PythonExe $Check
if ($LASTEXITCODE -ne 0) { throw "CHECK FEHLGESCHLAGEN" }
Write-Host "[OK]   Check bestanden" -ForegroundColor Green

# --- 3. Git-Status vorher ---
Write-Header "SCHRITT 3: Git-Status VORHER"
git status --short

# --- 4. Hauptlauf ---
Write-Header "SCHRITT 4: Inventur-Hauptlauf (read-only)"
& $PythonExe $Runner
if ($LASTEXITCODE -ne 0) { throw "HAUPTLAUF FEHLGESCHLAGEN" }
Write-Host "[OK]   Hauptlauf abgeschlossen" -ForegroundColor Green

# --- 5. Ausgaben anzeigen ---
Write-Header "SCHRITT 5: Erzeugte Ausgabedateien"
$AusgabeOrdner = "$ProjektWurzel\ALIN_Neustart_Core\07_Bestandsaufnahme_Altbestand"
$BerichtOrdner = "$ProjektWurzel\ALIN_Neustart_Core\Reports"

Get-ChildItem -Path $AusgabeOrdner -Filter "CORE13_*" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  $($_.Name)  [$($_.Length) Bytes]"
}
Get-ChildItem -Path $BerichtOrdner -Filter "CORE13_*" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  $($_.Name)  [$($_.Length) Bytes]"
}

# --- 6. Git-Status nachher ---
Write-Header "SCHRITT 6: Git-Status NACHHER"
git status --short

Write-Header "CORE-13 ALTBESTAND INVENTUR – ABGESCHLOSSEN"
Write-Host "Zeitstempel: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
