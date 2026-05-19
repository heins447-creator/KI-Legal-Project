Set-Location -LiteralPath "I:\KI_Legal_Project"

$ErrorActionPreference = "Stop"
try { $PSNativeCommandUseErrorActionPreference = $false } catch {}
try { chcp.com 65001 | Out-Null } catch {}
try { [Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false) } catch {}
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false) } catch {}

$Root = "I:\KI_Legal_Project"
$Python = Join-Path $Root "Tools\Python312\python.exe"
$Runner = Join-Path $Root "Scripts\python_runner\048_agenten_kontext_skill_register_v1.py"
$Fixer = Join-Path $Root "Scripts\python_runner\050_fix_agenten_kontext_skill_bindings_v1.py"
$Checker = Join-Path $Root "Scripts\python_runner\049_check_agenten_kontext_skill_register_v1.py"
$LogDir = Join-Path $Root "Windows_App\Logs"
$Ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$Report = Join-Path $LogDir "RUN_Agenten_Kontext_Skill_Register_$Ts.txt"
$Failed = $false

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function W {
    param([string]$Text = "")
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    $Line | Tee-Object -FilePath $Report -Append
}

function Invoke-PythonStep {
    param(
        [Parameter(Mandatory=$true)][string]$Label,
        [Parameter(Mandatory=$true)][string]$File
    )

    if (-not (Test-Path -LiteralPath $File)) {
        throw "$Label fehlt: $File"
    }

    W "Starte $Label"
    $Out = & $Python $File 2>&1
    $Code = $LASTEXITCODE

    if ($Out) {
        $Out | ForEach-Object { W ([string]$_) }
    }

    if ($Code -ne 0) {
        throw "$Label fehlgeschlagen. Exitcode: $Code"
    }

    W "OK: $Label"
}

try {
    W "AGENTEN KONTEXT SKILL REGISTER gestartet."
    W "Root: $Root"
    W "Python: $Python"
    W "Report: $Report"

    if (-not (Test-Path -LiteralPath $Python)) { throw "Python fehlt: $Python" }

    Invoke-PythonStep -Label "Agenten-Runner 048" -File $Runner
    Invoke-PythonStep -Label "Agenten-Bindungsfix 050" -File $Fixer
    Invoke-PythonStep -Label "Agenten-Prüfung 049" -File $Checker

    W "OK: Agenten-Kontext- und Skill-Register abgeschlossen."

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