$ErrorActionPreference = "Stop"
$ROOT = "I:\KI_Legal_Project"
$PY   = "$ROOT\Tools\Python312\python.exe"
$MOD  = "$ROOT\Scripts\python_runner\km16_sprachrouting_vor_ocr.py"
$CHK  = "$ROOT\Scripts\python_runner\check_km16_sprachrouting_vor_ocr.py"

Write-Host "=== KM16 py_compile ==="
& $PY -m py_compile $MOD
if ($LASTEXITCODE -ne 0) { throw "py_compile fehlgeschlagen" }

Write-Host "=== KM16 Selbsttest ==="
& $PY $MOD --selftest
if ($LASTEXITCODE -ne 0) { throw "Selbsttest fehlgeschlagen" }

Write-Host "=== KM16 Hauptlauf ==="
& $PY $MOD
if ($LASTEXITCODE -ne 0) { throw "Hauptlauf fehlgeschlagen" }

Write-Host "=== KM16 Pruefdatei ==="
& $PY $CHK
if ($LASTEXITCODE -ne 0) { throw "Pruefdatei fehlgeschlagen" }

Write-Host "=== KM16 ERFOLGREICH ==="