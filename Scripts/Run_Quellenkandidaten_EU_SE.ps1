Set-Location -LiteralPath "I:\KI_Legal_Project"

$ErrorActionPreference = "Stop"
try { $PSNativeCommandUseErrorActionPreference = $false } catch {}
try { chcp.com 65001 | Out-Null } catch {}
try { [Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false) } catch {}
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false) } catch {}

$Root = "I:\KI_Legal_Project"
$Python = Join-Path $Root "Tools\Python312\python.exe"
$Runner = Join-Path $Root "Scripts\python_runner\051_quellenkandidaten_eu_se_v1.py"
$Checker = Join-Path $Root "Scripts\python_runner\052_check_quellenkandidaten_eu_se_v1.py"
$LogDir = Join-Path $Root "Windows_App\Logs"
$Ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$Report = Join-Path $LogDir "RUN_Quellenkandidaten_EU_SE_$Ts.txt"
$Failed = $false

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function W {
    param([string]$Text = "")
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    $Line | Tee-Object -FilePath $Report -Append
}

try {
    W "QUELLENKANDIDATEN EU SE OFFICIAL SOURCES V1 gestartet."
    W "Root: $Root"
    W "Python: $Python"
    W "Report: $Report"

    if (-not (Test-Path -LiteralPath $Python)) { throw "Python fehlt: $Python" }
    if (-not (Test-Path -LiteralPath $Runner)) { throw "Runner fehlt: $Runner" }
    if (-not (Test-Path -LiteralPath $Checker)) { throw "Checker fehlt: $Checker" }

    W "Starte Python-Läufer."
    $RunnerOut = & $Python $Runner 2>&1
    $RunnerCode = $LASTEXITCODE
    if ($RunnerOut) { $RunnerOut | ForEach-Object { W ([string]$_) } }
    if ($RunnerCode -ne 0) { throw "Python-Läufer fehlgeschlagen. Exitcode: $RunnerCode" }

    W "Starte Prüfdatei."
    $CheckOut = & $Python $Checker 2>&1
    $CheckCode = $LASTEXITCODE
    if ($CheckOut) { $CheckOut | ForEach-Object { W ([string]$_) } }
    if ($CheckCode -ne 0) { throw "Prüfdatei fehlgeschlagen. Exitcode: $CheckCode" }

    W "OK: Quellenkandidaten EU SE Official Sources V1 abgeschlossen."

    Write-Host ""
    Write-Host "FERTIG"
    Write-Host "Report:"
    Write-Host $Report
}
catch {
    $Failed = $true
    W ("FEHLER: " + $_.Exception.Message)

    Write-Host ""
    Write-Host "FEHLER"
    Write-Host $_.Exception.Message
    Write-Host "Report:"
    Write-Host $Report
}
finally {
    Set-Location -LiteralPath $Root

    Write-Host ""
    Write-Host "EINSTIEGSPUNKT:"
    Write-Host (Get-Location)

    if ($Failed) { exit 1 } else { exit 0 }
}
