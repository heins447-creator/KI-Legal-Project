param(
    [ValidateSet(
        "Gesamtstatus",
        "Produktionslauf",
        "Schlusskontrolle",
        "Arbeitsliste",
        "Entscheidung",
        "Aktenmaterial",
        "Kommunikation",
        "Alles"
    )]
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
$Report = Join-Path $LogDir "RUN_POSTEINGANG_ZENTRALE_${Aktion}_$Ts.txt"
$Failed = $false

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function W {
    param([string]$Text = "")
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    $Line | Tee-Object -FilePath $Report -Append
}

function Invoke-Native {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [string[]]$ArgumentList = @()
    )

    W ("BEFEHL: " + $FilePath + " " + ($ArgumentList -join " "))
    $Output = & $FilePath @ArgumentList 2>&1
    $Code = $LASTEXITCODE

    if ($Output) {
        $Output | Tee-Object -FilePath $Report -Append
    }

    return [pscustomobject]@{
        ExitCode = $Code
        Output = ($Output | Out-String)
    }
}

function Require-File {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Pflichtdatei fehlt: $Path"
    }
}

function Run-Python {
    param(
        [string]$File,
        [string[]]$Args = @()
    )

    Require-File $File
    $Run = Invoke-Native -FilePath $Python -ArgumentList (@($File) + $Args)
    if ($Run.ExitCode -ne 0) {
        throw "Python-Lauf fehlgeschlagen: $File"
    }
}

function Run-PowerShell {
    param(
        [string]$File,
        [string[]]$Args = @()
    )

    Require-File $File
    $Run = Invoke-Native -FilePath "powershell.exe" -ArgumentList (@(
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        $File
    ) + $Args)

    if ($Run.ExitCode -ne 0) {
        throw "PowerShell-Lauf fehlgeschlagen: $File"
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

    $GesamtstatusPy = Join-Path $Root "Scripts\python_runner\020_posteingang_gesamtstatus_v1.py"
    $PipelinePs1 = Join-Path $Root "Scripts\Run_Posteingang_Pipeline.ps1"
    $SchlussPs1 = Join-Path $Root "Scripts\Run_Posteingang_Schlusskontrolle.ps1"
    $ArbeitslistePs1 = Join-Path $Root "Scripts\Run_Vorzimmer_Arbeitsliste.ps1"
    $EntscheidungPs1 = Join-Path $Root "Scripts\Run_Vorzimmer_Entscheidung.ps1"
    $AktenmaterialPs1 = Join-Path $Root "Scripts\Run_Aktenmaterial_Freigabeliste.ps1"
    $AktenmaterialPy = Join-Path $Root "Scripts\python_runner\027_posteingang_aktenmaterial_freigabeliste_v1.py"
    $KommunikationPs1 = Join-Path $Root "Scripts\Run_Vorzimmer_Kommunikationsparameter.ps1"

    switch ($Aktion) {
        "Gesamtstatus" {
            Run-Python -File $GesamtstatusPy
        }

        "Produktionslauf" {
            Run-PowerShell -File $PipelinePs1 -Args @("-CaseTemplate", $CaseTemplate)
        }

        "Schlusskontrolle" {
            Run-PowerShell -File $SchlussPs1
        }

        "Arbeitsliste" {
            Run-PowerShell -File $ArbeitslistePs1
        }

        "Entscheidung" {
            Run-PowerShell -File $EntscheidungPs1
        }

        "Aktenmaterial" {
            if (Test-Path -LiteralPath $AktenmaterialPs1) {
                Run-PowerShell -File $AktenmaterialPs1
            } else {
                Run-Python -File $AktenmaterialPy
            }
        }

        "Kommunikation" {
            Run-PowerShell -File $KommunikationPs1
        }

        "Alles" {
            Run-Python -File $GesamtstatusPy
            Run-PowerShell -File $KommunikationPs1
            Run-PowerShell -File $PipelinePs1 -Args @("-CaseTemplate", $CaseTemplate)
            Run-PowerShell -File $SchlussPs1
            Run-PowerShell -File $ArbeitslistePs1

            if (Test-Path -LiteralPath $AktenmaterialPs1) {
                Run-PowerShell -File $AktenmaterialPs1
            } elseif (Test-Path -LiteralPath $AktenmaterialPy) {
                Run-Python -File $AktenmaterialPy
            }

            Run-Python -File $GesamtstatusPy
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
        exit 1
    } else {
        Write-Host "Zentrale beendet."
        exit 0
    }
}
