param(
    [ValidateSet("Gesamtstatus","Produktionslauf","Pipeline","Arbeitsliste","Entscheidung","Aktenmaterial","Schlusskontrolle","Alles")]
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

$GesamtstatusPy = Join-Path $Root "Scripts\python_runner\020_posteingang_gesamtstatus_v1.py"
$PipelinePs1 = Join-Path $Root "Scripts\Run_Posteingang_Pipeline.ps1"
$ArbeitslistePs1 = Join-Path $Root "Scripts\Run_Vorzimmer_Arbeitsliste.ps1"
$EntscheidungPs1 = Join-Path $Root "Scripts\Run_Vorzimmer_Entscheidung.ps1"
$AktenmaterialPy = Join-Path $Root "Scripts\python_runner\027_posteingang_aktenmaterial_freigabeliste_v1.py"
$SchlussPs1 = Join-Path $Root "Scripts\Run_Posteingang_Schlusskontrolle.ps1"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function W {
    param([string]$Text = "")
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    $Line | Tee-Object -FilePath $Report -Append
}

function Run-PythonFile {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Python-Datei fehlt: $Path"
    }

    & $Python $Path 2>&1 | Tee-Object -FilePath $Report -Append
    if ($LASTEXITCODE -ne 0) {
        throw "Python-Lauf fehlgeschlagen: $Path"
    }
}

function Run-PsFile {
    param(
        [string]$Path,
        [string[]]$Args = @()
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "PowerShell-Datei fehlt: $Path"
    }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Path @Args 2>&1 | Tee-Object -FilePath $Report -Append
    if ($LASTEXITCODE -ne 0) {
        throw "PowerShell-Lauf fehlgeschlagen: $Path"
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

    if ($Aktion -eq "Gesamtstatus") {
        Run-PythonFile -Path $GesamtstatusPy
    }
    elseif ($Aktion -eq "Produktionslauf" -or $Aktion -eq "Pipeline") {
        Run-PsFile -Path $PipelinePs1 -Args @("-CaseTemplate", $CaseTemplate)
    }
    elseif ($Aktion -eq "Arbeitsliste") {
        Run-PsFile -Path $ArbeitslistePs1
    }
    elseif ($Aktion -eq "Entscheidung") {
        Run-PsFile -Path $EntscheidungPs1
    }
    elseif ($Aktion -eq "Aktenmaterial") {
        Run-PythonFile -Path $AktenmaterialPy
    }
    elseif ($Aktion -eq "Schlusskontrolle") {
        Run-PsFile -Path $SchlussPs1
    }
    elseif ($Aktion -eq "Alles") {
        Run-PsFile -Path $PipelinePs1 -Args @("-CaseTemplate", $CaseTemplate)
        Run-PsFile -Path $SchlussPs1
        Run-PsFile -Path $ArbeitslistePs1
        Run-PythonFile -Path $AktenmaterialPy
        Run-PythonFile -Path $GesamtstatusPy
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
