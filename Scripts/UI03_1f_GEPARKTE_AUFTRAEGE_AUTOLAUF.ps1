# UI03-1f Geparkte Auftraege verwalten AUTOLAUF
$ErrorActionPreference = "Stop"
$ROOT = "I:\KI_Legal_Project"
$PYTHON = "$ROOT\Tools\Python312\python.exe"
$RUNNER = "$ROOT\Scripts\python_runner\ui03_1f_geparkte_auftraege.py"
$CHECK = "$ROOT\Scripts\python_runner\check_ui03_1f_geparkte_auftraege.py"
$LOG = "$ROOT\Windows_App\Logs\UI03_1f_GEPARKTE_AUFTRAEGE_BERICHT.txt"

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
Write-Log "UI03-1f Geparkte Auftraege AUTOLAUF START"
Write-Log "=========================================="

# Git-Status vorher
Write-Log "Git-Status vorher:"
git -C $ROOT status --short | ForEach-Object { Write-Log "  $_" }

# 1. py_compile
$ok1 = Run-Step { & $PYTHON -m py_compile $RUNNER } "py_compile"

# 2. Selbsttest
$ok2 = Run-Step { & $PYTHON $RUNNER --selbsttest } "Selbsttest"

# 3. Hauptlauf
$ok3 = Run-Step { & $PYTHON $RUNNER } "Hauptlauf"

# 4. Pruefdatei
$ok4 = Run-Step { & $PYTHON $CHECK } "Pruefdatei"

# Ergebnis
Write-Log "=========================================="
Write-Log "py_compile : $(if($ok1){'OK'}else{'FEHLER'})"
Write-Log "Selbsttest : $(if($ok2){'OK'}else{'FEHLER'})"
Write-Log "Hauptlauf  : $(if($ok3){'OK'}else{'FEHLER'})"
Write-Log "Pruefdatei : $(if($ok4){'OK'}else{'FEHLER'})"

if ($ok1 -and $ok2 -and $ok3 -and $ok4) {
    Write-Log "ALLE SCHRITTE BESTANDEN"
    git -C $ROOT add -A
    git -C $ROOT commit -m "UI03-1f Geparkte Uebersetzungsauftraege verwalten (CORE-11-konform)"
    Write-Log "Git-Commit erfolgt"
} else {
    Write-Log "AUTOLAUF NICHT VOLLSTAENDIG BESTANDEN"
}

Write-Log "UI03-1f Geparkte Auftraege AUTOLAUF ENDE"
