<#
.SYNOPSIS UI02-0 Bestandsabgleich Tuerschwelle PowerShell-Starter
.DESCRIPTION Startet den Python-Laeufer fuer den Bestandsabgleich
#>
$ErrorActionPreference = "Stop"
$Modul = "UI02_0"
$Root = "I:\KI_Legal_Project"
$Python = "$Root\Tools\Python312\python.exe"
$Runner = "$Root\Scripts\python_runner\ui02_0_bestandsabgleich_tuerschwelle.py"
$LogDir = "$Root\Windows_App\Logs"
$Zeit = Get-Date -Format "yyyy-MM-dd_HHmmss"
$LogFile = "$LogDir\UI02_0_LAUF_$Zeit.log"

Write-Host "=== $Modul Bestandsabgleich Tuerschwelle ==="
Write-Host "Start: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "Python: $Python"
Write-Host "Runner: $Runner"
Write-Host "Log   : $LogFile"
Write-Host ""

if (-not (Test-Path $Python)) {
    Write-Error "Python nicht gefunden: $Python"
    exit 1
}
if (-not (Test-Path $Runner)) {
    Write-Error "Runner nicht gefunden: $Runner"
    exit 1
}
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$exitCode = 0
try {
    & $Python $Runner 2>&1 | Tee-Object -FilePath $LogFile
    $exitCode = $LASTEXITCODE
} catch {
    Write-Error "FEHLER: $_"
    $exitCode = 1
}

$StatusDatei = "$Root\Agentensteuerung\UI02_0_Bestandsabgleich_Tuerschwelle\02_Status\UI02_0_STATUS.json"
if (Test-Path $StatusDatei) {
    Write-Host "`nStatus: $(Get-Content $StatusDatei | ConvertFrom-Json | ConvertTo-Json -Compress)"
}

Write-Host "`nExit: $exitCode"
Write-Host "Ende: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
exit $exitCode
