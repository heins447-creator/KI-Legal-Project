# CORE-05 – Toolregister vervollstaendigen und mit Update-Register abgleichen
# PowerShell-Starter

$Sep = "=" * 70
Write-Host $Sep
Write-Host "CORE-05 – Toolregister vervollstaendigen und mit Update-Register abgleichen"
Write-Host $Sep

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CoreDir = Split-Path -Parent $ScriptDir
$PythonScript = Join-Path $ScriptDir "alin_core05_toolregister_befuellen.py"
$PruefScript = Join-Path $ScriptDir "alin_core05_pruefung.py"

# Python-Interpreter finden
$PyCandidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
    (Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\python.exe"),
    "C:\Python313\python.exe",
    "C:\Python312\python.exe",
    "C:\Python311\python.exe"
)

$PythonExe = $null
foreach ($cand in $PyCandidates) {
    if (Test-Path $cand) {
        $PythonExe = $cand
        break
    }
}

# Fallback: Config-Datei
if (-not $PythonExe) {
    $ConfigPath = Join-Path $CoreDir "Config\CORE02_python.config.json"
    if (Test-Path $ConfigPath) {
        $Config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
        if ($Config.python_exe -and (Test-Path $Config.python_exe)) {
            $PythonExe = $Config.python_exe
        }
    }
}

if (-not $PythonExe) {
    Write-Host "FEHLER: Python-Interpreter nicht gefunden." -ForegroundColor Red
    Write-Host "Bitte in Config\CORE02_python.config.json eintragen."
    exit 1
}

Write-Host "Python-Interpreter: $PythonExe"
Write-Host ""

# Schritt 1: Toolregister befuellen
Write-Host "[1/2] Toolregister befuellen und mit Update-Register abgleichen..."
& $PythonExe $PythonScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER beim Befuellen des Toolregisters." -ForegroundColor Red
    exit 1
}
Write-Host "OK: Toolregister befuellt." -ForegroundColor Green
Write-Host ""

# Schritt 2: Pruefung durchfuehren
Write-Host "[2/2] Pruefung durchfuehren..."
& $PythonExe $PruefScript
$PruefExit = $LASTEXITCODE
if ($PruefExit -eq 0) {
    Write-Host "OK: Pruefung erfolgreich." -ForegroundColor Green
} else {
    Write-Host "WARNUNG: Pruefung hat Fehler gefunden (Exit-Code: $PruefExit)." -ForegroundColor Yellow
}

Write-Host ""
Write-Host $Sep
Write-Host "CORE-05 abgeschlossen."
Write-Host $Sep

exit $PruefExit
