param()

Set-Location -LiteralPath "I:\KI_Legal_Project"

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new() } catch {}

$Root = "I:\KI_Legal_Project"
$Python = Join-Path $Root "Tools\Python312\python.exe"
$PyFile = Join-Path $Root "Scripts\python_runner\046_agent_sachverhaltsbezug_v1.py"
$LogDir = Join-Path $Root "Windows_App\Logs"
$Ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$Report = Join-Path $LogDir "RUN_AGENT_SACHVERHALTSBEZUG_$Ts.txt"
$Failed = $false

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function W {
    param([string]$Text = "")
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    $Line | Tee-Object -FilePath $Report -Append
}

try {
    W "AGENT SACHVERHALTSBEZUG gestartet."
    W "Root: $Root"
    W "Report: $Report"

    if (-not (Test-Path -LiteralPath $Python)) {
        $CmdPy = Get-Command python.exe -ErrorAction SilentlyContinue
        if ($CmdPy -and $CmdPy.Source) {
            $Python = $CmdPy.Source
        } else {
            throw "Python wurde nicht gefunden."
        }
    }

    if (-not (Test-Path -LiteralPath $PyFile)) {
        throw "Python-Datei fehlt: $PyFile"
    }

    & $Python $PyFile 2>&1 | Tee-Object -FilePath $Report -Append

    if ($LASTEXITCODE -ne 0) {
        throw "Agent Sachverhaltsbezug fehlgeschlagen."
    }

    W "AGENT SACHVERHALTSBEZUG abgeschlossen."

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
        exit 1
    } else {
        Write-Host "Agent Sachverhaltsbezug beendet."
        exit 0
    }
}
