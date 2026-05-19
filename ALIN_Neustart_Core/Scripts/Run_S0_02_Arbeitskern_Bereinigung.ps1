$ErrorActionPreference = "Stop"
$core = "I:\KI_Legal_Project\ALIN_Neustart_Core"
$script = Join-Path $core "Scripts\check_s0_02_arbeitskern_bereinigung.py"
$bericht = Join-Path $core "Reports\S0_02_ARBEITSKERN_BEREINIGUNG_BERICHT.txt"
$status = Join-Path $core "Reports\S0_02_ARBEITSKERN_BEREINIGUNG_STATUS.json"
$bundledPython = "C:\Users\heins\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
Set-Location -LiteralPath $core

if (Test-Path -LiteralPath $bundledPython) {
    & $bundledPython -m py_compile $script
    if ($LASTEXITCODE -ne 0) { throw "py_compile fehlgeschlagen" }
    & $bundledPython $script
    if ($LASTEXITCODE -ne 0) { throw "Pruefskript fehlgeschlagen" }
} else {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        & $pythonCmd.Source -m py_compile $script
        if ($LASTEXITCODE -ne 0) { throw "py_compile fehlgeschlagen" }
        & $pythonCmd.Source $script
        if ($LASTEXITCODE -ne 0) { throw "Pruefskript fehlgeschlagen" }
    } else {
        $pyCmd = Get-Command py -ErrorAction SilentlyContinue
        if (-not $pyCmd) { throw "Kein Python-Starter gefunden." }
        & $pyCmd.Source -3 -m py_compile $script
        if ($LASTEXITCODE -ne 0) { throw "py_compile fehlgeschlagen" }
        & $pyCmd.Source -3 $script
        if ($LASTEXITCODE -ne 0) { throw "Pruefskript fehlgeschlagen" }
    }
}

Write-Host "AKTIVER_PROGRAMMIERORDNER: $core"
Write-Host "BERICHT: $bericht"
Write-Host "STATUS: $status"