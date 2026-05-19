# WINAPP – Windows App Build und Release (Vorbereitung)
# KEIN Produktivrelease. KEIN Deployment. NUR lokale Vorbereitung.

$ErrorActionPreference = "Stop"
$Base = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Base "Tools\Python312\python.exe"
$Runner = Join-Path $Base "Scripts\python_runner\winapp_windows_app_build_release.py"
$Check = Join-Path $Base "Scripts\python_runner\check_winapp_windows_app_build_release.py"

function Step($n, $desc, $cmd) {
    Write-Host "[$n/4] $desc..." -NoNewline
    try {
        & $cmd 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Exit $LASTEXITCODE" }
        Write-Host " OK" -ForegroundColor Green
    } catch {
        Write-Host " FEHLER: $_" -ForegroundColor Red
        exit 1
    }
}

Step 1 "py_compile auf Runner" { & $Python -m py_compile $Runner }
Step 2 "py_compile auf Check"  { & $Python -m py_compile $Check }
Step 3 "Check ausfuehren"      { & $Python $Check }
Step 4 "Runner ausfuehren"      { & $Python $Runner }

Write-Host "`nWINAPP Autolauf erfolgreich abgeschlossen." -ForegroundColor Green
