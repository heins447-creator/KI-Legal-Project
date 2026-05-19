# ================================================================================
# CORE-25: Programmierbare Gesamt-Roadmap - PowerShell Autolauncher
# ================================================================================
# Ziel: Startet den Python-Runner CORE-25 mit dem korrekten Interpreter,
#       speichert Git-Status vorher und nachher, und protokolliert das Ergebnis.
# ================================================================================

$ErrorActionPreference = "Stop"
$BaseDir = "I:\KI_Legal_Project"
$PythonExe = "$BaseDir\Tools\Python312\python.exe"
$Runner = "$BaseDir\Scripts\python_runner\core25_gesamt_roadmap.py"
$Check = "$BaseDir\Scripts\python_runner\check_core25_gesamt_roadmap.py"
$GitStatusVor = "$BaseDir\ALIN_Neustart_Core\08_Migration\09_Manifest\CORE25_git_status_vor.txt"
$GitStatusNach = "$BaseDir\ALIN_Neustart_Core\08_Migration\09_Manifest\CORE25_git_status_nach.txt"
$LogFile = "$BaseDir\ALIN_Neustart_Core\Reports\CORE25_GESAMT_ROADMAP_BERICHT.txt"

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"
    $line = "[$ts] $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding UTF8 -ErrorAction SilentlyContinue
}

# --- Git-Status vorher ---
Write-Log "CORE-25 AUTOLAUF gestartet"
Write-Log "Speichere Git-Status VORHER..."
New-Item -ItemType Directory -Force -Path (Split-Path $GitStatusVor) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $LogFile) | Out-Null
git -C $BaseDir status > $GitStatusVor 2>&1

# --- py_compile Pruefung ---
Write-Log "Pruefe py_compile fuer Runner..."
& $PythonExe -m py_compile $Runner
if ($LASTEXITCODE -ne 0) {
    Write-Log "FEHLER: py_compile fuer Runner fehlgeschlagen"
    exit 1
}
Write-Log "py_compile Runner OK"

Write-Log "Pruefe py_compile fuer Check..."
& $PythonExe -m py_compile $Check
if ($LASTEXITCODE -ne 0) {
    Write-Log "FEHLER: py_compile fuer Check fehlgeschlagen"
    exit 1
}
Write-Log "py_compile Check OK"

# --- Runner ausfuehren ---
Write-Log "Starte CORE-25 Runner..."
& $PythonExe $Runner
$runnerRc = $LASTEXITCODE
Write-Log "Runner beendet mit RC=$runnerRc"

if ($runnerRc -ne 0) {
    Write-Log "WARNUNG: Runner mit RC=$runnerRc beendet"
}

# --- Check ausfuehren ---
Write-Log "Starte CORE-25 Check..."
& $PythonExe $Check
$checkRc = $LASTEXITCODE
Write-Log "Check beendet mit RC=$checkRc"

if ($checkRc -ne 0) {
    Write-Log "FEHLER: Check nicht bestanden"
    exit $checkRc
}

Write-Log "Check bestanden."

# --- Git-Status nachher ---
Write-Log "Speichere Git-Status NACHHER..."
git -C $BaseDir status > $GitStatusNach 2>&1

Write-Log "CORE-25 AUTOLAUF erfolgreich abgeschlossen"
exit 0
