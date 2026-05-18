$ErrorActionPreference = "Stop"
$ProjektPython = "I:\KI_Legal_Project\Tools\Python312\python.exe"
$Runner = "Scripts\python_runner\ext003_eu_terminologie.py"
$Check  = "Scripts\python_runner\check_ext003_eu_terminologie.py"

Write-Host "[1/4] py_compile auf Runner..."
& $ProjektPython -m py_compile $Runner
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "OK"

Write-Host "[2/4] py_compile auf Check..."
& $ProjektPython -m py_compile $Check
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "OK"

Write-Host "[3/4] Check ausfuehren..."
& $ProjektPython $Check
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "OK"

Write-Host "[4/4] Runner ausfuehren..."
& $ProjektPython $Runner
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "OK"

Write-Host "EXT-003 Autolauf erfolgreich abgeschlossen."