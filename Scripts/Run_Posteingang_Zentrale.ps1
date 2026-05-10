param(
    [ValidateSet("Gesamtstatus", "Status", "Produktionslauf", "Arbeitsliste", "Entscheidung")]
    [string]$Aktion = "Gesamtstatus",

    [string]$CaseTemplate = "TEMPLATE_SE_ARBEITSRECHT"
)

Set-Location -LiteralPath "I:\KI_Legal_Project"

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new() } catch {}

$Root = "I:\KI_Legal_Project"
$Python = Join-Path $Root "Tools\Python312\python.exe"
$LogDir = Join-Path $Root "Windows_App\Logs"
$Ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$Report = Join-Path $LogDir "RUN_POSTEINGANG_ZENTRALE_$Aktion`_$Ts.txt"
$Failed = $false

$Gesamtstatus = Join-Path $Root "Scripts\python_runner\020_posteingang_gesamtstatus_v1.py"
$Betriebsstatus = Join-Path $Root "Scripts\python_runner\016_posteingang_betriebsstatus_v1.py"
$Pipeline = Join-Path $Root "Scripts\Run_Posteingang_Pipeline.ps1"
$Arbeitsliste = Join-Path $Root "Scripts\Run_Vorzimmer_Arbeitsliste.ps1"
$Entscheidung = Join-Path $Root "Scripts\Run_Vorzimmer_Entscheidung.ps1"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function W {
    param([string]$Text = "")
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    $Line | Tee-Object -FilePath $Report -Append
}

try {
    W "POSTEINGANG ZENTRALE gestartet."
    W "Aktion: $Aktion"
    W "Fallvorlage: $CaseTemplate"
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

    switch ($Aktion) {
        "Gesamtstatus" {
            if (-not (Test-Path -LiteralPath $Gesamtstatus)) { throw "Gesamtstatus fehlt: $Gesamtstatus" }
            & $Python $Gesamtstatus 2>&1 | Tee-Object -FilePath $Report -Append
            if ($LASTEXITCODE -ne 0) { throw "Gesamtstatus fehlgeschlagen." }
        }

        "Status" {
            if (-not (Test-Path -LiteralPath $Betriebsstatus)) { throw "Betriebsstatus fehlt: $Betriebsstatus" }
            & $Python $Betriebsstatus 2>&1 | Tee-Object -FilePath $Report -Append
            if ($LASTEXITCODE -ne 0) { throw "Betriebsstatus fehlgeschlagen." }
        }

        "Produktionslauf" {
            if (-not (Test-Path -LiteralPath $Pipeline)) { throw "Produktionsstarter fehlt: $Pipeline" }
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Pipeline -CaseTemplate $CaseTemplate 2>&1 | Tee-Object -FilePath $Report -Append
            if ($LASTEXITCODE -ne 0) { throw "Produktionslauf fehlgeschlagen." }
        }

        "Arbeitsliste" {
            if (-not (Test-Path -LiteralPath $Arbeitsliste)) { throw "Arbeitslistenstarter fehlt: $Arbeitsliste" }
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Arbeitsliste 2>&1 | Tee-Object -FilePath $Report -Append
            if ($LASTEXITCODE -ne 0) { throw "Arbeitsliste fehlgeschlagen." }
        }

        "Entscheidung" {
            if (-not (Test-Path -LiteralPath $Entscheidung)) { throw "Entscheidungsstarter fehlt: $Entscheidung" }
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Entscheidung 2>&1 | Tee-Object -FilePath $Report -Append
            if ($LASTEXITCODE -ne 0) { throw "Entscheidungslauf fehlgeschlagen." }
        }
    }

    W "POSTEINGANG ZENTRALE abgeschlossen."

    Write-Host ""
    Write-Host "FERTIG"
    Write-Host "Aktion:"
    Write-Host $Aktion
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
        Write-Host "Zentrale beendet."
    }
}
