# ================================================================================
# CORE-24: Autonomer Entwicklungsmanager / Auftragsqueue / Selbstreparatur
# PowerShell-Starter
# ================================================================================
# Ziel:
#     Startet den CORE-24 Entwicklungsmanager autonom.
#     Führt py_compile, Runner und Check aus.
#     Schreibt Bericht und verwaltet Git-Status.
#
# Lieferpflichten aus AGENTS.md:
#     - Python-Läufer unter Scripts/python_runner/
#     - Prüfdatei unter Scripts/python_runner/
#     - PowerShell-Starter unter Scripts/
#     - Konfiguration unter Config/
#     - Dokumentation unter Projektplanung/
#     - Testlauf
#     - Bericht unter ALIN_Neustart_Core/Reports/
#     - Git-Status vor und nach Änderung
#     - Git-Commit nur bei erfolgreichem Build und erfolgreicher Prüfung
#
# Regeln:
#     - Nur Befehle aus AGENTENFREIGABE_KLARSTELLUNG.txt verwenden
#     - Keine destruktiven Operationen
#     - Bei harter Sperre: Bericht schreiben und anhalten
#     - Max. 3 Reparaturversuche pro Auftrag
#     - Git-Commit nur wenn py_compile + Check + Runner alle erfolgreich
# ================================================================================

$ErrorActionPreference = "Stop"
$BaseDir = "I:\KI_Legal_Project"
$PythonExe = "$BaseDir\Tools\Python312\python.exe"
$RunnerDir = "$BaseDir\Scripts\python_runner"
$ConfigPath = "$BaseDir\Config\core24_entwicklungsmanager_v1.json"
$BerichtPath = "$BaseDir\ALIN_Neustart_Core\Reports\CORE24_ENTWICKLUNGSMANAGER_BERICHT.txt"
$QueuePath = "$BaseDir\ALIN_Neustart_Core\08_Migration\09_Manifest\CORE24_auftragsqueue.json"
$ReparaturLogPath = "$BaseDir\ALIN_Neustart_Core\08_Migration\09_Manifest\CORE24_reparatur_log.json"
$GitStatusVorPath = "$BaseDir\ALIN_Neustart_Core\08_Migration\09_Manifest\CORE24_git_status_vor.txt"
$GitStatusNachPath = "$BaseDir\ALIN_Neustart_Core\08_Migration\09_Manifest\CORE24_git_status_nach.txt"

$SkriptName = "core24_entwicklungsmanager.py"
$CheckName = "check_core24_entwicklungsmanager.py"
$SkriptPath = "$RunnerDir\$SkriptName"
$CheckPath = "$RunnerDir\$CheckName"

function Write-Log {
    param([string]$Message)
    $ts = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
    $line = "[$ts] $Message"
    Write-Host $line
    # Auch in Bericht schreiben
    try {
        $line | Out-File -FilePath $BerichtPath -Append -Encoding utf8
    } catch {
        # Ignorieren, falls Bericht noch nicht erstellt
    }
}

function Test-PythonExe {
    if (-not (Test-Path $PythonExe)) {
        throw "Python-Interpreter nicht gefunden: $PythonExe"
    }
    Write-Log "Python-Interpreter OK: $PythonExe"
}

function Test-Config {
    if (-not (Test-Path $ConfigPath)) {
        throw "Konfiguration nicht gefunden: $ConfigPath"
    }
    Write-Log "Konfiguration OK: $ConfigPath"
}

function Run-PyCompile {
    param([string]$TargetPath)
    Write-Log "py_compile: $TargetPath"
    $proc = Start-Process -FilePath $PythonExe -ArgumentList "-m", "py_compile", $TargetPath -Wait -PassThru -NoNewWindow
    if ($proc.ExitCode -ne 0) {
        throw "py_compile FEHLGESCHLAGEN für $TargetPath (ExitCode=$($proc.ExitCode))"
    }
    Write-Log "py_compile OK: $TargetPath"
}

function Run-Check {
    param([string]$CheckScriptPath)
    Write-Log "Check: $CheckScriptPath"
    $proc = Start-Process -FilePath $PythonExe -ArgumentList $CheckScriptPath -Wait -PassThru -NoNewWindow
    if ($proc.ExitCode -ne 0) {
        throw "Check FEHLGESCHLAGEN für $CheckScriptPath (ExitCode=$($proc.ExitCode))"
    }
    Write-Log "Check OK: $CheckScriptPath"
}

function Run-Runner {
    param([string]$RunnerScriptPath)
    Write-Log "Runner: $RunnerScriptPath"
    $proc = Start-Process -FilePath $PythonExe -ArgumentList $RunnerScriptPath -Wait -PassThru -NoNewWindow
    if ($proc.ExitCode -ne 0) {
        throw "Runner FEHLGESCHLAGEN für $RunnerScriptPath (ExitCode=$($proc.ExitCode))"
    }
    Write-Log "Runner OK: $RunnerScriptPath"
}

function Save-GitStatus {
    param([string]$OutPath)
    Write-Log "Git-Status speichern: $OutPath"
    $status = git status 2>&1
    $status | Out-File -FilePath $OutPath -Encoding utf8
    Write-Log "Git-Status gespeichert: $OutPath"
}

function Add-GitFiles {
    param([string[]]$Files)
    foreach ($file in $Files) {
        Write-Log "git add: $file"
        git add $file 2>&1 | Out-Null
    }
}

function Commit-Git {
    param([string]$Message)
    Write-Log "git commit: $Message"
    $result = git commit -m $Message 2>&1
    Write-Log "git commit Ergebnis: $result"
}

# ================================================================================
# HAUPTLOGIK
# ================================================================================

try {
    Write-Log "========================================================================"
    Write-Log "CORE-24: Autonomer Entwicklungsmanager – PowerShell-Starter"
    Write-Log "========================================================================"

    # 1. Voraussetzungen prüfen
    Test-PythonExe
    Test-Config

    # 2. Verzeichnisse sicherstellen
    New-Item -ItemType Directory -Force -Path (Split-Path $BerichtPath) | Out-Null
    New-Item -ItemType Directory -Force -Path (Split-Path $QueuePath) | Out-Null
    New-Item -ItemType Directory -Force -Path (Split-Path $ReparaturLogPath) | Out-Null
    New-Item -ItemType Directory -Force -Path (Split-Path $GitStatusVorPath) | Out-Null

    # 3. py_compile für Runner und Check
    Run-PyCompile -TargetPath $SkriptPath
    Run-PyCompile -TargetPath $CheckPath

    # 4. Check ausführen
    Run-Check -CheckScriptPath $CheckPath

    # 5. Git-Status vorher
    Save-GitStatus -OutPath $GitStatusVorPath

    # 6. Runner ausführen (autonomer Entwicklungsmanager)
    Run-Runner -RunnerScriptPath $SkriptPath

    # 7. Git-Status nachher
    Save-GitStatus -OutPath $GitStatusNachPath

    # 8. Git add + commit (nur bei Erfolg)
    $zuCommitten = @(
        "Scripts/python_runner/$SkriptName",
        "Scripts/python_runner/$CheckName",
        "Config/core24_entwicklungsmanager_v1.json",
        "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_auftragsqueue.json",
        "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_reparatur_log.json",
        "ALIN_Neustart_Core/Reports/CORE24_ENTWICKLUNGSMANAGER_BERICHT.txt",
        "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_git_status_vor.txt",
        "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_git_status_nach.txt"
    )
    Add-GitFiles -Files $zuCommitten
    Commit-Git -Message "CORE-24: Autonomer Entwicklungsmanager – erfolgreicher Durchlauf"

    Write-Log "========================================================================"
    Write-Log "CORE-24: ERFOLGREICH abgeschlossen"
    Write-Log "========================================================================"
    exit 0

} catch {
    Write-Log "========================================================================"
    Write-Log "CORE-24: FEHLER – $($_.Exception.Message)"
    Write-Log "========================================================================"

    # Bei harter Sperre: Bericht wurde bereits geschrieben
    # Versuche trotzdem, Git-Status zu speichern
    try {
        Save-GitStatus -OutPath $GitStatusNachPath
    } catch {
        Write-Log "Konnte Git-Status nicht speichern: $($_.Exception.Message)"
    }

    exit 1
}
