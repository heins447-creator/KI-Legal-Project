# UI04 DURCHSTICH SEKRETARIAT -> ANWALT -> RUECKLAUF AUTOLAUF
$ErrorActionPreference = "Stop"
$ROOT = "I:\KI_Legal_Project"
$PYTHON = "$ROOT\Tools\Python312\python.exe"
$RUNNER = "$ROOT\Scripts\python_runner\ui04_durchstich_sekretariat_anwalt_ruecklauf.py"
$CHECK = "$ROOT\Scripts\python_runner\check_ui04_durchstich_sekretariat_anwalt_ruecklauf.py"
$LOG = "$ROOT\Windows_App\Logs\UI04_AUTOLAUF_BERICHT.txt"

function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts  $msg" | Tee-Object -FilePath $LOG -Append
}

function Run-Step($cmd, $label) {
    Write-Log "[$label] START"
    try {
        $out = & $cmd 2>&1
        $out | ForEach-Object { Write-Log "  $_" }
        if ($LASTEXITCODE -ne 0) {
            Write-Log "[$label] FEHLER (Exit $LASTEXITCODE)"
            return $false
        }
        Write-Log "[$label] OK"
        return $true
    } catch {
        Write-Log "[$label] EXCEPTION: $($_.Exception.Message)"
        return $false
    }
}

Remove-Item $LOG -ErrorAction SilentlyContinue
Write-Log "UI04 AUTOLAUF START"
Write-Log "======================================"

# Git-Status vorher
Write-Log "Git-Status vorher:"
git -C $ROOT status --short | ForEach-Object { Write-Log "  $_" }

# 1. py_compile Runner
$ok1 = Run-Step { & $PYTHON -m py_compile $RUNNER } "py_compile_runner"

# 2. py_compile Check
$ok2 = Run-Step { & $PYTHON -m py_compile $CHECK } "py_compile_check"

# 3. Selbsttest
$ok3 = Run-Step { & $PYTHON $RUNNER --selbsttest } "Selbsttest"

# 4. Hauptlauf
$ok4 = Run-Step { & $PYTHON $RUNNER } "Hauptlauf"

# 5. Pruefdatei
$ok5 = Run-Step { & $PYTHON $CHECK } "Pruefdatei"

# Ergebnis
Write-Log "======================================"
Write-Log "py_compile_runner : $(if($ok1){'OK'}else{'FEHLER'})"
Write-Log "py_compile_check    : $(if($ok2){'OK'}else{'FEHLER'})"
Write-Log "Selbsttest          : $(if($ok3){'OK'}else{'FEHLER'})"
Write-Log "Hauptlauf           : $(if($ok4){'OK'}else{'FEHLER'})"
Write-Log "Pruefdatei          : $(if($ok5){'OK'}else{'FEHLER'})"

if ($ok1 -and $ok2 -and $ok3 -and $ok4 -and $ok5) {
    Write-Log "ALLE SCHRITTE BESTANDEN"
    git -C $ROOT add -A
    git -C $ROOT commit -m "UI04 Durchstich Sekretariat -> Anwalt -> Ruecklauf -> Sekretariatsergebnis erstellt"
    Write-Log "Git-Commit erfolgt"
} else {
    Write-Log "AUTOLAUF NICHT VOLLSTAENDIG BESTANDEN"
}

Write-Log "UI04 AUTOLAUF ENDE"
