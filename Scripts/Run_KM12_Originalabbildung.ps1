param(
    [switch]$OnlySelfTest,
    [switch]$SkipSelfTest,
    [switch]$SkipCheck
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

try { chcp.com 65001 | Out-Null } catch {}
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

$ProjectRoot = "I:\KI_Legal_Project"
Set-Location -LiteralPath $ProjectRoot

$Global:PythonExe = Join-Path $ProjectRoot "Tools\Python312\python.exe"
$RunnerScript = Join-Path $ProjectRoot "Scripts\python_runner\km12_originalabbildung.py"
$CheckScript  = Join-Path $ProjectRoot "Scripts\python_runner\check_km12_originalabbildung.py"

$KM12Root = Join-Path $ProjectRoot "Agentensteuerung\12_Originalabbildung_Arbeitsabbildung"
$LogDir = Join-Path $KM12Root "90_RunLogs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Global:LogFile = Join-Path $LogDir "RUN_KM12_$Stamp.log"

function Write-Step {
    param([string]$Text)
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Write-LogLine {
    param([string]$Text)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Text
    Add-Content -LiteralPath $Global:LogFile -Value $line -Encoding UTF8
    Write-Host $line
}

function Invoke-Python {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Name,

        [Parameter(Mandatory=$true)]
        [string[]]$PyArgs
    )

    Write-Step $Name
    Write-LogLine $Name
    Write-LogLine ("Befehl: {0} {1}" -f $Global:PythonExe, ($PyArgs -join " "))

    $TmpOut = Join-Path $env:TEMP ("alin_py_" + [guid]::NewGuid().ToString("N") + ".log")
    $oldPreference = $ErrorActionPreference

    try {
        $ErrorActionPreference = "Continue"
        & $Global:PythonExe @PyArgs *> $TmpOut
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $oldPreference
    }

    if (Test-Path -LiteralPath $TmpOut) {
        Get-Content -LiteralPath $TmpOut -Encoding UTF8 | Tee-Object -FilePath $Global:LogFile -Append
        Remove-Item -LiteralPath $TmpOut -Force -ErrorAction SilentlyContinue
    }

    Write-LogLine ("ExitCode: {0}" -f $exitCode)

    if ($exitCode -ne 0) {
        throw "Python-Schritt fehlgeschlagen: $Name ExitCode=$exitCode"
    }
}

Write-Step "KM12 START"
Write-LogLine "KM12 START"
Write-LogLine "ProjektRoot: $ProjectRoot"
Write-LogLine "Python: $Global:PythonExe"
Write-LogLine "Runner: $RunnerScript"
Write-LogLine "Check: $CheckScript"
Write-LogLine "Grenzen: keine Originalaenderung, keine Datenbankaenderung, kein Internet, keine Installation."

if (-not (Test-Path -LiteralPath $Global:PythonExe)) { throw "Python nicht gefunden: $Global:PythonExe" }
if (-not (Test-Path -LiteralPath $RunnerScript)) { throw "KM12-Skript nicht gefunden: $RunnerScript" }
if (-not (Test-Path -LiteralPath $CheckScript)) { throw "KM12-Pruefdatei nicht gefunden: $CheckScript" }

try {
    Invoke-Python -Name "KM12 py_compile" -PyArgs @("-m", "py_compile", $RunnerScript)

    if ($OnlySelfTest) {
        Invoke-Python -Name "KM12 Selbsttest" -PyArgs @($RunnerScript, "--selftest")
        Write-Step "KM12 SELBSTTEST ERFOLGREICH"
        Write-Host "Log: $Global:LogFile"
        exit 0
    }

    if (-not $SkipSelfTest) {
        Invoke-Python -Name "KM12 Selbsttest" -PyArgs @($RunnerScript, "--selftest")
    }

    Invoke-Python -Name "KM12 Hauptlauf" -PyArgs @($RunnerScript)

    if (-not $SkipCheck) {
        Invoke-Python -Name "KM12 Pruefdatei" -PyArgs @($CheckScript)
    }

    Write-Step "KM12 ERFOLGREICH ABGESCHLOSSEN"
    Write-LogLine "KM12 ERFOLGREICH ABGESCHLOSSEN"

    Write-Host "Log:" $Global:LogFile
    Write-Host "Naechster Schritt: KM13 OCR-Pipeline"

    exit 0
}
catch {
    Write-Step "KM12 FEHLER"
    Write-LogLine "KM12 FEHLER"
    Write-LogLine $_.Exception.Message

    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Log:" $Global:LogFile

    exit 1
}