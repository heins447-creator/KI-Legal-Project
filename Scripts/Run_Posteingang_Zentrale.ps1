param(
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
$SafeAktion = ($Aktion -replace '[^A-Za-z0-9_-]', '_')
$Report = Join-Path $LogDir "RUN_POSTEINGANG_ZENTRALE_${SafeAktion}_$Ts.txt"
$Failed = $false

$StatusPy = Join-Path $Root "Scripts\python_runner\020_posteingang_gesamtstatus_v1.py"
$PipelinePs1 = Join-Path $Root "Scripts\Run_Posteingang_Pipeline.ps1"
$ArbeitslistePs1 = Join-Path $Root "Scripts\Run_Vorzimmer_Arbeitsliste.ps1"
$EntscheidungPs1 = Join-Path $Root "Scripts\Run_Vorzimmer_Entscheidung.ps1"
$VorschlagPy = Join-Path $Root "Scripts\python_runner\023_vorzimmer_entscheidungsvorschlag_v1.py"
$AktenmaterialPy = Join-Path $Root "Scripts\python_runner\027_posteingang_aktenmaterial_freigabeliste_v1.py"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function W {
    param([string]$Text = "")
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    $Line | Tee-Object -FilePath $Report -Append
}

function Run-Native {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$FilePath,
        [string[]]$ArgumentList = @()
    )

    W ""
    W $Name
    W ("-" * 80)
    W ("BEFEHL: " + $FilePath + " " + ($ArgumentList -join " "))

    $Output = & $FilePath @ArgumentList 2>&1
    $Code = $LASTEXITCODE

    if ($Output) {
        $Output | Tee-Object -FilePath $Report -Append
    }

    if ($Code -ne 0) {
        throw "$Name fehlgeschlagen. Exitcode: $Code"
    }
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
            Run-Native "Gesamtstatus" $Python @($StatusPy)
        }

        "Pipeline" {
            Run-Native "Posteingang-Pipeline" "powershell.exe" @(
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                $PipelinePs1,
                "-CaseTemplate",
                $CaseTemplate
            )
        }

        "Arbeitsliste" {
            Run-Native "Vorzimmer-Arbeitsliste" "powershell.exe" @(
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                $ArbeitslistePs1
            )
        }

        "Entscheidung" {
            Run-Native "Vorzimmer-Entscheidung" "powershell.exe" @(
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                $EntscheidungPs1
            )
        }

        "Entscheidungsvorschlag" {
            Run-Native "Vorzimmer-Entscheidungsvorschlag" $Python @($VorschlagPy)
        }

        "Aktenmaterial" {
            Run-Native "Aktenmaterial-Freigabeliste" $Python @($AktenmaterialPy)
        }

        "Alle" {
            Run-Native "Gesamtstatus vor Lauf" $Python @($StatusPy)
            Run-Native "Posteingang-Pipeline" "powershell.exe" @(
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                $PipelinePs1,
                "-CaseTemplate",
                $CaseTemplate
            )
            Run-Native "Vorzimmer-Arbeitsliste" "powershell.exe" @(
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                $ArbeitslistePs1
            )
            Run-Native "Vorzimmer-Entscheidungsvorschlag" $Python @($VorschlagPy)
            Run-Native "Aktenmaterial-Freigabeliste" $Python @($AktenmaterialPy)
            Run-Native "Gesamtstatus nach Lauf" $Python @($StatusPy)
        }

        default {
            throw "Unbekannte Aktion: $Aktion"
        }
    }

    W ""
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
        exit 1
    } else {
        Write-Host "Zentrale beendet."
        exit 0
    }
}
