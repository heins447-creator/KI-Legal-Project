# KM17c – OCR-Neulauf für KM12b-abgeleitete Einzelseite
# ======================================================
# Vollständiger Autolauf: py_compile → Selbsttest → Hauptlauf → Prüfdatei
# Nutzung:  .\Scripts\KM17c_EINZELSEITE_KM12b_AUTOLAUF.ps1
# Stand:   2026-05-14

$ErrorActionPreference = "Continue"
$ROOT = "I:\KI_Legal_Project"
$PY  = "$ROOT\Tools\Python312\python.exe"
$MOD = "$ROOT\Scripts\python_runner\km17c_einzelseite_km12b_ocr.py"
$CHK = "$ROOT\Scripts\python_runner\check_km17c_einzelseite_km12b_ocr.py"

# ------------------------------------------------------------------
# 1. py_compile
# ------------------------------------------------------------------
Write-Host "=== KM17c py_compile ==="
& $PY -m py_compile $MOD 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: py_compile fehlgeschlagen (Exit $LASTEXITCODE)"
    exit 1
}
Write-Host "py_compile: OK"
Write-Host ""

# ------------------------------------------------------------------
# 2. Selbsttest
# ------------------------------------------------------------------
Write-Host "=== KM17c Selbsttest ==="
& $PY $MOD --selftest 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Selbsttest fehlgeschlagen (Exit $LASTEXITCODE)"
    exit 1
}
Write-Host ""

# ------------------------------------------------------------------
# 3. Hauptlauf (OCR für ORG-9dd16304b3b5-00162)
# ------------------------------------------------------------------
Write-Host "=== KM17c Hauptlauf ==="
& $PY $MOD 2>&1
$MAIN_RC = $LASTEXITCODE
Write-Host "Hauptlauf Exit: $MAIN_RC"
Write-Host ""

# ------------------------------------------------------------------
# 4. Prüfdatei
# ------------------------------------------------------------------
Write-Host "=== KM17c Prüfdatei ==="
& $PY $CHK 2>&1
$CHK_RC = $LASTEXITCODE
Write-Host "Prüfdatei Exit: $CHK_RC"
Write-Host ""

# ------------------------------------------------------------------
# 5. Ergebnis
# ------------------------------------------------------------------
if ($MAIN_RC -eq 0 -and $CHK_RC -eq 0) {
    Write-Host "=== KM17c ERFOLGREICH ==="
    Write-Host "Nächster Schritt: git add/commit"
    exit 0
} else {
    Write-Host "=== KM17c TEILWEISE FEHLGESCHLAGEN ==="
    Write-Host "Hauptlauf Exit: $MAIN_RC  |  Prüfdatei Exit: $CHK_RC"
    exit 1
}
