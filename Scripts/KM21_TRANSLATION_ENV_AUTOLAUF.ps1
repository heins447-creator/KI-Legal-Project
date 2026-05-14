# KM21 – Translation Environment Prepare – AUTOLAUF
# Starter: PowerShell.exe -NoProfile -ExecutionPolicy Bypass -File "I:\KI_Legal_Project\Scripts\KM21_TRANSLATION_ENV_AUTOLAUF.ps1"

$root = "I:\KI_Legal_Project"
$python = "$root\Tools\Python312\python.exe"
$runner = "$root\Scripts\python_runner\km21_translation_env_prepare.py"
$pruefung = "$root\Scripts\python_runner\check_km21_translation_env_prepare.py"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ErrorActionPreference = "Continue"

function Write-Step($n, $txt) {
    Write-Host "`n============================================================"
    Write-Host "[Step $n] $txt"
    Write-Host "============================================================"
}

Write-Host "KM21 – TRANSLATION ENVIRONMENT PREPARE – AUTOLAUF"
Write-Host "Zeit: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# Step 1: py_compile
Write-Step "1/4" "py_compile"
$pyc = & $python -c "import py_compile; py_compile.compile(r'$runner', doraise=True); print('py_compile OK')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "py_compile FEHLER: $pyc"
    exit 1
}
Write-Host $pyc

# Step 2: Selbsttest
Write-Step "2/4" "Selbsttest"
$st = & $python $runner --selbsttest 2>&1
Write-Host $st
if ($LASTEXITCODE -ne 0) {
    Write-Host "SELBSTTEST FEHLGESCHLAGEN"
    exit 1
}

# Step 3: Hauptlauf
Write-Step "3/4" "Hauptlauf"
$hl = & $python $runner 2>&1
Write-Host $hl
if ($LASTEXITCODE -ne 0) {
    Write-Host "HAUPTLAUF FEHLGESCHLAGEN"
    exit 1
}

# Step 4: Pruefdatei
Write-Step "4/4" "Pruefdatei"
$pr = & $python $pruefung 2>&1
Write-Host $pr
if ($LASTEXITCODE -ne 0) {
    Write-Host "PRUEFDATEI NICHT BESTANDEN"
    # Read status for diagnosis
    $status_path = "$root\Agentensteuerung\21_Translation_Environment\02_Status\KM21_STATUS.json"
    if (Test-Path $status_path) {
        Write-Host "Status:"
        Get-Content $status_path -Encoding UTF8 | Write-Host
    }
    exit 1
}

Write-Host "`n============================================================"
Write-Host "KM21 ERFOLGREICH ABGESCHLOSSEN"
Write-Host "============================================================"

# Final status summary
$status = Get-Content "$root\Agentensteuerung\21_Translation_Environment\02_Status\KM21_STATUS.json" -Encoding UTF8 | ConvertFrom-Json
Write-Host ""
Write-Host "--- KM21 ABSCHLUSS ---"
Write-Host "Lokale Uebersetzung verfuegbar: $($status.lokale_uebersetzung_verfuegbar)"
Write-Host "Argos Translate: $($status.argos_translate_status)"
Write-Host "Sprachrichtungen verfuegbar: $($status.sprachrichtungen_verfuegbar)/$($status.sprachrichtungen_geprueft)"
Write-Host "Inventardateien: $($status.inventardateien)"
Write-Host "Dummy-Tests erfolgreich: $($status.test_erfolgreich)"
Write-Host "KM15-Uebersetzung freigegeben: $($status.km15_uebersetzung_freigegeben)"
Write-Host "Naechster Auftrag: $($status.naechster_empfohlener_auftrag)"

# Log
$logdir = "$root\Windows_App\Logs"
if (-not (Test-Path $logdir)) { New-Item -ItemType Directory -Path $logdir -Force | Out-Null }
"$timestamp | KM21 | ERFOLG | argos=$($status.argos_translate_status) | sprachen=$($status.sprachrichtungen_verfuegbar) | fehler=$($status.fehler_anzahl)" | Out-File -FilePath "$logdir\km21_lauf.txt" -Encoding UTF8 -Append
