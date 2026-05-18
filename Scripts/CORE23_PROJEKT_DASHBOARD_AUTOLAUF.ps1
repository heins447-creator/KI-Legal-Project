# CORE23_PROJEKT_DASHBOARD_AUTOLAUF.ps1
# PowerShell-Starter für CORE-23: Arbeitsstart-Zentrale / Projekt-Dashboard
#
# Läuft:
#   1. Git-Status vorher sichern
#   2. core23_projekt_dashboard.py ausführen
#   3. check_core23_projekt_dashboard.py ausführen
#   4. Bei Erfolg: Git-Status nachher + optionales Commit
#
# Ergebnisdateien:
#   ALIN_Neustart_Core/08_Migration/09_Manifest/CORE23_dashboard.json
#   ALIN_Neustart_Core/08_Migration/09_Manifest/CORE23_dashboard.html
#   ALIN_Neustart_Core/Reports/CORE23_PROJEKT_DASHBOARD_BERICHT.txt

$ErrorActionPreference = "Stop"
$BaseDir = "I:\KI_Legal_Project"
$PythonExe = "I:\KI_Legal_Project\Tools\Python312\python.exe"
$Runner = "$BaseDir\Scripts\python_runner\core23_projekt_dashboard.py"
$Checker = "$BaseDir\Scripts\python_runner\check_core23_projekt_dashboard.py"
$ManifestDir = "$BaseDir\ALIN_Neustart_Core\08_Migration\09_Manifest"
$ReportsDir = "$BaseDir\ALIN_Neustart_Core\Reports"

function Write-Header($text) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host $text -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

# 1. Git-Status vorher
Write-Header "1. Git-Status VORHER"
cd $BaseDir
git status --short > "$ManifestDir\CORE23_git_status_vor.txt" 2>&1
Write-Host "Gespeichert: CORE23_git_status_vor.txt"

# 2. Runner
Write-Header "2. CORE-23 Runner"
if (-not (Test-Path $PythonExe)) {
    Write-Error "Python nicht gefunden: $PythonExe"
    exit 1
}
& $PythonExe $Runner
if ($LASTEXITCODE -ne 0) {
    Write-Error "Runner fehlgeschlagen (Exit $LASTEXITCODE)"
    exit 1
}

# 3. Checker
Write-Header "3. CORE-23 Checker"
& $PythonExe $Checker
if ($LASTEXITCODE -ne 0) {
    Write-Error "Checker fehlgeschlagen (Exit $LASTEXITCODE). Kein Commit."
    exit 1
}

# 4. Git-Status nachher + optional Commit
Write-Header "4. Git-Status NACHHER"
git status --short > "$ManifestDir\CORE23_git_status_nach.txt" 2>&1
Write-Host "Gespeichert: CORE23_git_status_nach.txt"

# Prüfe ob neue Dateien da sind
$newFiles = @(
    "$ManifestDir\CORE23_dashboard.json",
    "$ManifestDir\CORE23_dashboard.html",
    "$ReportsDir\CORE23_PROJEKT_DASHBOARD_BERICHT.txt"
)
$allExist = $true
foreach ($f in $newFiles) {
    if (-not (Test-Path $f)) {
        Write-Warning "Fehlende Datei: $f"
        $allExist = $false
    }
}

if ($allExist) {
    Write-Host "Alle Ergebnisdateien vorhanden." -ForegroundColor Green
    # Optional: Add + Commit
    git add -A
    git commit -m "CORE-23: Arbeitsstart-Zentrale / Projekt-Dashboard generiert`n`n- CORE23_dashboard.json`n- CORE23_dashboard.html`n- CORE23_PROJEKT_DASHBOARD_BERICHT.txt`n`nPrüfung bestanden."
    Write-Host "Git-Commit durchgeführt." -ForegroundColor Green
} else {
    Write-Warning "Nicht alle Ergebnisdateien gefunden. Kein Commit."
    exit 1
}

Write-Header "CORE-23 ABGESCHLOSSEN"
