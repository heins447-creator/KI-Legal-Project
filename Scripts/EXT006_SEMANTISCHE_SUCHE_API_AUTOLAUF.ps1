$ErrorActionPreference = "Stop"
$ProjektPython = "I:\KI_Legal_Project\Tools\Python312\python.exe"
$BaseDir      = "I:\KI_Legal_Project"
$Runner       = "$BaseDir\Scripts\python_runner\ext006_semantische_suche_api.py"
$Check        = "$BaseDir\Scripts\python_runner\check_ext006_semantische_suche_api.py"

Write-Host "========================================"
Write-Host " EXT-006 - Semantische Suche API Autolauf"
Write-Host "========================================"

# 1) py_compile auf Runner
Write-Host "[1/4] py_compile auf Runner..."
& $ProjektPython -m py_compile $Runner
if ($LASTEXITCODE -ne 0) { Write-Error "py_compile Runner fehlgeschlagen" }
Write-Host "OK"

# 2) py_compile auf Check
Write-Host "[2/4] py_compile auf Check..."
& $ProjektPython -m py_compile $Check
if ($LASTEXITCODE -ne 0) { Write-Error "py_compile Check fehlgeschlagen" }
Write-Host "OK"

# 3) Check ausfuehren
Write-Host "[3/4] Check ausfuehren..."
& $ProjektPython $Check
if ($LASTEXITCODE -ne 0) { Write-Error "Check fehlgeschlagen" }
Write-Host "OK"

# 4) Runner ausfuehren
Write-Host "[4/4] Runner ausfuehren..."
& $ProjektPython $Runner
if ($LASTEXITCODE -ne 0) { Write-Error "Runner fehlgeschlagen" }
Write-Host "OK"

Write-Host ""
Write-Host "EXT-006 Autolauf erfolgreich abgeschlossen."
