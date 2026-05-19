$ErrorActionPreference = "Stop"
$ROOT = "I:\KI_Legal_Project"
$PY   = "$ROOT\Tools\Python312\python.exe"
$MOD  = "$ROOT\Scripts\python_runner\km12b_uebergrosse_arbeitsabbildungen.py"
$CHK  = "$ROOT\Scripts\python_runner\check_km12b_uebergrosse_arbeitsabbildungen.py"

Write-Host "=== KM12b py_compile ==="
& $PY -m py_compile $MOD
if ($LASTEXITCODE -ne 0) { throw "py_compile fehlgeschlagen" }

Write-Host "=== KM12b Selbsttest ==="
& $PY $MOD --selftest
if ($LASTEXITCODE -ne 0) { throw "Selbsttest fehlgeschlagen" }

Write-Host "=== KM12b Hauptlauf ==="
& $PY $MOD
if ($LASTEXITCODE -ne 0) { throw "Hauptlauf fehlgeschlagen" }

Write-Host "=== KM12b Pruefdatei ==="
& $PY $CHK
if ($LASTEXITCODE -ne 0) { throw "Pruefdatei fehlgeschlagen" }

Write-Host "=== KM12b ERFOLGREICH ==="
