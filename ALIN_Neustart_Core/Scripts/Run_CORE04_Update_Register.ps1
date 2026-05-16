# CORE-04 – Update-Register initial befüllen und prüfen
# PowerShell-Starter

$Sep = "=" * 70
Write-Host $Sep
Write-Host "CORE-04 – Update-Register initial befüllen und prüfen"
Write-Host $Sep

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CoreDir = Split-Path -Parent $ScriptDir
$PythonScript = Join-Path $ScriptDir "alin_core04_update_register_befuellen.py"
$PruefScript = Join-Path $ScriptDir "alin_core04_pruefung.py"

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

# Schritt 1: Update-Register befüllen
Write-Host "[1/2] Update-Register befüllen..."
& $PythonExe $PythonScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER beim Befüllen des Update-Registers." -ForegroundColor Red
    exit 1
}
Write-Host "OK: Update-Register befüllt." -ForegroundColor Green
Write-Host ""

# Schritt 2: Prüfung durchführen
Write-Host "[2/2] Prüfung durchführen..."
& $PythonExe $PruefScript
$PruefExit = $LASTEXITCODE
if ($PruefExit -eq 0) {
    Write-Host "OK: Prüfung erfolgreich." -ForegroundColor Green
} else {
    Write-Host "WARNUNG: Prüfung hat Fehler gefunden (Exit-Code: $PruefExit)." -ForegroundColor Yellow
}

Write-Host ""
Write-Host $Sep
Write-Host "CORE-04 abgeschlossen."
Write-Host $Sep

exit $PruefExit
