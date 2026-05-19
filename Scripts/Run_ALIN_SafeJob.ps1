param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("KM12")]
    [string]$Job
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

try { chcp.com 65001 | Out-Null } catch {}
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ROOT = "I:\KI_Legal_Project"
$PYTHON = Join-Path $ROOT "Tools\Python312\python.exe"

if (-not (Test-Path -LiteralPath $ROOT)) {
    throw "Projektwurzel fehlt: $ROOT"
}
if (-not (Test-Path -LiteralPath $PYTHON)) {
    throw "Python fehlt: $PYTHON"
}

Set-Location -LiteralPath $ROOT

$KM12Area = Join-Path $ROOT "Agentensteuerung\12_Originalabbildung_Arbeitsabbildung"
$LogDir = Join-Path $KM12Area "90_SafeRunner"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Log = Join-Path $LogDir ("SAFEJOB_{0}_{1}.log" -f $Job, $Stamp)
$Status = Join-Path $LogDir ("SAFEJOB_{0}_{1}_STATUS.json" -f $Job, $Stamp)

function Write-LogLine {
    param([string]$Text)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Text
    $line | Tee-Object -FilePath $Log -Append
}

function Quote-ProcessArg {
    param([string]$Value)

    if ($null -eq $Value) {
        return '""'
    }

    if ($Value -notmatch '[\s"]') {
        return $Value
    }

    return '"' + ($Value -replace '"','\"') + '"'
}

function Invoke-PythonStep {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Name,

        [Parameter(Mandatory=$true)]
        [string[]]$PyArgs
    )

    Write-LogLine ""
    Write-LogLine "============================================================"
    Write-LogLine $Name
    Write-LogLine "============================================================"

    $argString = ($PyArgs | ForEach-Object { Quote-ProcessArg $_ }) -join " "
    Write-LogLine ("Befehl: {0} {1}" -f $PYTHON, $argString)

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $PYTHON
    $psi.Arguments = $argString
    $psi.WorkingDirectory = $ROOT
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true

    try { $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
    try { $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8 } catch {}

    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi

    [void]$p.Start()
    $stdout = $p.StandardOutput.ReadToEnd()
    $stderr = $p.StandardError.ReadToEnd()
    $p.WaitForExit()

    if ($stdout) {
        $stdout.TrimEnd() | Tee-Object -FilePath $Log -Append
    }

    if ($stderr) {
        Write-LogLine "STDERR:"
        $stderr.TrimEnd() | Tee-Object -FilePath $Log -Append
    }

    Write-LogLine ("ExitCode: {0}" -f $p.ExitCode)

    if ($p.ExitCode -ne 0) {
        throw "Schritt fehlgeschlagen: $Name ExitCode=$($p.ExitCode)"
    }
}

try {
    Write-LogLine "ALIN SAFEJOB START"
    Write-LogLine "Job: $Job"
    Write-LogLine "Root: $ROOT"
    Write-LogLine "Grenzen: keine Originaländerung, keine Datenbankänderung, kein Internet, keine Installation."

    if ($Job -eq "KM12") {
        $KM12Script = Join-Path $ROOT "Scripts\python_runner\km12_originalabbildung.py"
        $KM12Check  = Join-Path $ROOT "Scripts\python_runner\check_km12_originalabbildung.py"

        if (-not (Test-Path -LiteralPath $KM12Script)) {
            throw "KM12-Skript fehlt: $KM12Script"
        }

        if (-not (Test-Path -LiteralPath $KM12Check)) {
            throw "KM12-Prüfdatei fehlt: $KM12Check"
        }

        Invoke-PythonStep -Name "KM12 py_compile" -PyArgs @("-m", "py_compile", $KM12Script)
        Invoke-PythonStep -Name "KM12 Selbsttest" -PyArgs @($KM12Script, "--selftest")
        Invoke-PythonStep -Name "KM12 Hauptlauf" -PyArgs @($KM12Script)
        Invoke-PythonStep -Name "KM12 Prüfdatei" -PyArgs @($KM12Check)
    }

    $statusObj = [ordered]@{
        job = $Job
        status = "OK"
        zeitpunkt = (Get-Date).ToString("s")
        root = $ROOT
        log = $Log
        grenzen = [ordered]@{
            originale_veraendert = $false
            datenbanken_geaendert = $false
            internet = $false
            installation = $false
        }
    }

    $statusObj | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Status -Encoding UTF8

    Write-LogLine ""
    Write-LogLine "ALIN SAFEJOB ABGESCHLOSSEN"
    Write-LogLine "Status: OK"
    Write-LogLine "Log: $Log"
    Write-LogLine "Statusdatei: $Status"

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "SAFEJOB ABGESCHLOSSEN"
    Write-Host "============================================================"
    Write-Host "Status: OK"
    Write-Host "Log:" $Log
    Write-Host "Statusdatei:" $Status

    exit 0
}
catch {
    Write-LogLine ""
    Write-LogLine "SAFEJOB FEHLER"
    Write-LogLine $_.Exception.Message

    $statusObj = [ordered]@{
        job = $Job
        status = "FEHLER"
        zeitpunkt = (Get-Date).ToString("s")
        root = $ROOT
        log = $Log
        fehler = $_.Exception.Message
    }

    $statusObj | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Status -Encoding UTF8

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "SAFEJOB FEHLER"
    Write-Host "============================================================"
    Write-Host $_.Exception.Message
    Write-Host "Log:" $Log
    Write-Host "Statusdatei:" $Status

    exit 1
}