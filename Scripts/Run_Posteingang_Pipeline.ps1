param(
    [string]$CaseTemplate = "TEMPLATE_SE_ARBEITSRECHT"
)

Set-Location -LiteralPath "I:\KI_Legal_Project"

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new() } catch {}

$Root = "I:\KI_Legal_Project"
$Python = Join-Path $Root "Tools\Python312\python.exe"
$Pipeline = Join-Path $Root "Scripts\python_runner\014_posteingang_pipeline_v1.py"
$Status = Join-Path $Root "Scripts\python_runner\016_posteingang_betriebsstatus_v1.py"
$LogDir = Join-Path $Root "Windows_App\Logs"
$Ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$Report = Join-Path $LogDir "RUN_POSTEINGANG_PRODUKTIONSLAUF_$Ts.txt"
$Failed = $false

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function W {
    param([string]$Text = "")
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    $Line | Tee-Object -FilePath $Report -Append
}

try {
    W "POSTEINGANG PRODUKTIONSLAUF gestartet."
    W "Root: $Root"
    W "Fallvorlage: $CaseTemplate"
    W "Report: $Report"

    if (-not (Test-Path -LiteralPath $Python)) {
        $CmdPy = Get-Command python.exe -ErrorAction SilentlyContinue
        if ($CmdPy -and $CmdPy.Source) {
            $Python = $CmdPy.Source
        } else {
            throw "Python wurde nicht gefunden."
        }
    }

    if (-not (Test-Path -LiteralPath $Pipeline)) {
        throw "Posteingang-Pipeline fehlt: $Pipeline"
    }

    if (-not (Test-Path -LiteralPath $Status)) {
        throw "Betriebsstatus-Skript fehlt: $Status"
    }

    W ""
    W "1. Betriebsstatus vor Verarbeitung"
    W "----------------------------------------"
    & $Python $Status 2>&1 | Tee-Object -FilePath $Report -Append
    if ($LASTEXITCODE -ne 0) {
        throw "Betriebsstatus vor Verarbeitung fehlgeschlagen."
    }

    W ""
    W "2. Pipeline ausführen"
    W "----------------------------------------"
    & $Python $Pipeline --case-template $CaseTemplate 2>&1 | Tee-Object -FilePath $Report -Append
    if ($LASTEXITCODE -ne 0) {
        throw "Posteingang-Pipeline fehlgeschlagen."
    }

    W ""
    W "3. Betriebsstatus nach Verarbeitung"
    W "----------------------------------------"
    & $Python $Status 2>&1 | Tee-Object -FilePath $Report -Append
    if ($LASTEXITCODE -ne 0) {
        throw "Betriebsstatus nach Verarbeitung fehlgeschlagen."
    }

    W ""
    W "POSTEINGANG PRODUKTIONSLAUF abgeschlossen."

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

    if ($Failed) {
        Write-Host "Fehlerbericht prüfen. Danach nächsten vollständigen PowerShell-Block hier einfügen."
    } else {
        Write-Host "Produktionslauf beendet. Neue Dateien gehören nach Posteingang\00_Roh_Eingang."
    }
}
