# =============================================================================
# KM17_AUTOLAUF.ps1 – Sprachrouting-OCR-Integration V1.1
# Gestartet via:
#   PowerShell.exe -NoProfile -ExecutionPolicy Bypass -File "I:\KI_Legal_Project\Scripts\KM17_AUTOLAUF.ps1"
# =============================================================================
$ErrorActionPreference = "Continue"
$ROOT = "I:\KI_Legal_Project"
$PY   = "$ROOT\Tools\Python312\python.exe"
$MOD  = "$ROOT\Scripts\python_runner\km17_sprachrouting_ocr_integration.py"
$CHK  = "$ROOT\Scripts\python_runner\check_km17_sprachrouting_ocr_integration.py"
$CONF = "$ROOT\Config\km17_sprachrouting_ocr_v1.json"
$DOC  = "$ROOT\Projektplanung\KM17_SPRACHROUTING_OCR_INTEGRATION.md"
$LOG  = "$ROOT\Windows_App\Logs\KM17_AUTOLAUF_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    $line = "$ts | $msg"
    Write-Host $line
    Add-Content -Path $LOG -Value $line -Encoding UTF8
}

# ===== 0. VORBEREITUNG =====
Log "========== KM17 AUTOLAUFBLOCK START =========="
Log "GIT-STATUS VORHER:"
Set-Location $ROOT
git status --short 2>&1 | ForEach-Object { Log $_ }
$dirs = @("$ROOT\Config","$ROOT\Scripts\python_runner","$ROOT\Projektplanung","$ROOT\Windows_App\Logs")
foreach ($d in $dirs) { New-Item -ItemType Directory -Force -Path $d | Out-Null }

# ===== 1. CONFIG PRUEFEN =====
if (-not (Test-Path $CONF)) {
    Log "FEHLER: Config fehlt: $CONF"
    exit 1
}
Log "Config: $((Get-Item $CONF).Length) bytes"

# ===== 2. MODULE PRUEFEN =====
if (-not (Test-Path $MOD)) {
    Log "FEHLER: Modul fehlt: $MOD"
    exit 1
}
Log "KM17 Modul: $((Get-Item $MOD).Length) bytes"
if (-not (Test-Path $CHK)) {
    Log "FEHLER: Pruefdatei fehlt: $CHK"
    exit 1
}
Log "KM17 Pruefdatei: $((Get-Item $CHK).Length) bytes"

# ===== 3. PIPELINE (bis 3 Schleifen) =====
$MAX = 3
for ($loop = 1; $loop -le $MAX; $loop++) {
    Log "========== SCHLEIFE $loop / $MAX =========="

    Log "py_compile..."
    $res = & $PY -m py_compile $MOD 2>&1
    if ($LASTEXITCODE -ne 0) { Log "FEHLER py_compile: $res"; if ($loop -eq $MAX) { Log "ABBRUCH"; exit 1 }; continue }
    Log "  OK"

    Log "Selbsttest..."
    $res = & $PY $MOD --selftest 2>&1
    if ($LASTEXITCODE -ne 0) { Log "FEHLER Selbsttest: $res"; if ($loop -eq $MAX) { Log "ABBRUCH"; exit 1 }; continue }
    Log "  OK"

    Log "Hauptlauf..."
    $res = & $PY $MOD 2>&1
    if ($LASTEXITCODE -ne 0) { Log "FEHLER Hauptlauf: $res"; if ($loop -eq $MAX) { Log "ABBRUCH"; exit 1 }; continue }
    Log "  OK"

    Log "Pruefdatei..."
    $res = & $PY $CHK 2>&1
    if ($LASTEXITCODE -ne 0) { Log "FEHLER Pruefdatei: $res"; if ($loop -eq $MAX) { Log "ABBRUCH"; exit 1 }; continue }
    Log "  OK"

    Log "========== ALLE SCHRITTE BESTANDEN =========="
    Write-Host ""
    Write-Host $res
    Write-Host ""

    # ZUERST Skript kopieren, DANACH git add/commit
    Log "Skript nach Scripts/ kopieren..."
    Copy-Item $PSCommandPath "$ROOT\Scripts\KM17_AUTOLAUF.ps1" -Force
    Log "  OK"

    Log "GIT-STATUS NACHER:"
    Set-Location $ROOT
    git status --short 2>&1 | ForEach-Object { Log $_ }

    Log "GIT-ADD..."
    git add Scripts/KM17_AUTOLAUF.ps1 2>&1 | Out-Null
    git add Scripts/python_runner/km17_sprachrouting_ocr_integration.py 2>&1 | Out-Null
    git add Scripts/python_runner/check_km17_sprachrouting_ocr_integration.py 2>&1 | Out-Null
    git add Config/km17_sprachrouting_ocr_v1.json 2>&1 | Out-Null
    git add Projektplanung/KM17_SPRACHROUTING_OCR_INTEGRATION.md 2>&1 | Out-Null

    Log "GIT-COMMIT..."
    $cr = git commit -m "KM17 Sprachrouting-OCR-Integration V1.1 - sprachspezifischer OCR-Lauf, writeheader, snippet-begrenzt" 2>&1
    $gitExit = $LASTEXITCODE
    Log "Commit: $cr"
    if ($gitExit -ne 0) {
        Log "WARNUNG: Git-Commit nicht erfolgt oder fehlgeschlagen (exit=$gitExit). Lauf wird als Erfolg gewertet."
    }

    Log "========== KM17 AUTOLAUFBLOCK ENDE =========="
    exit 0
}
Log "========== KM17 FEHLGESCHLAGEN NACH $MAX SCHLEIFEN =========="
exit 1
