$root = $PSScriptRoot
$runner = Join-Path $root "python_runner\ui02_tuerschwelle_bau.py"
$python_exe = "I:\KI_Legal_Project\Tools\Python312\python.exe"

if (-not (Test-Path $python_exe)) {
    Write-Error "Python exe nicht gefunden: $python_exe"
    exit 1
}
if (-not (Test-Path $runner)) {
    Write-Error "Runner nicht gefunden: $runner"
    exit 1
}

$arg = if ($args.Count -gt 0) { $args[0] } else { "" }
Write-Host "ALIN UI02 Tuerschwelle Bau – Starter" -ForegroundColor Cyan
Write-Host "Python: $python_exe" -ForegroundColor DarkGray
Write-Host "Runner: $runner" -ForegroundColor DarkGray
Write-Host ""

& $python_exe $runner @args
$exit = $LASTEXITCODE

$zeit = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$logdir = "I:\KI_Legal_Project\Windows_App\Logs"
if (-not (Test-Path $logdir)) { New-Item -ItemType Directory -Path $logdir -Force | Out-Null }
$logfile = Join-Path $logdir "UI02_STARTER_LOG.txt"
"[Starter $zeit] ExitCode=$exit Args=$arg" | Add-Content -Path $logfile

if ($exit -eq 0) {
    Write-Host "`n[OK] UI02 Tuerschwelle Bau abgeschlossen." -ForegroundColor Green
} else {
    Write-Host "`n[WARNUNG] Exit code $exit – siehe Log." -ForegroundColor Yellow
}
exit $exit
