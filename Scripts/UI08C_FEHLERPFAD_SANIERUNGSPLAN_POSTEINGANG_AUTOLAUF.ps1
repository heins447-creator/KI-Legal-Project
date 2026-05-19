# UI08c – Fehlerpfad-Sanierungsplan Posteingang
# Autolauf: Check → Runner → Check
# Rote Linie: produktiv_freigegeben=false, nur_musterdaten=true

param(
    [switch]$SkipCheck,
    [switch]$SkipRunner
)

$ErrorActionPreference = "Stop"
$Base = Split-Path $PSScriptRoot -Parent

function Write-Header($text) {
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host $text -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
}

function Write-Status($text, $ok) {
    if ($ok) {
        Write-Host "[OK]   $text" -ForegroundColor Green
    } else {
        Write-Host "[FEHLER] $text" -ForegroundColor Red
    }
}

# 1. Git-Status
Write-Header "1. Git-Status"
$gitStatus = git -C $Base status --short 2>$null
if ($gitStatus) {
    Write-Host "Uncommitted Änderungen:" -ForegroundColor Yellow
    $gitStatus | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
} else {
    Write-Status "Git-Status sauber" $true
}

# 2. Vorab-Check
if (-not $SkipCheck) {
    Write-Header "2. Vorab-Check UI08c"
    $checkScript = Join-Path $Base "Scripts\python_runner\check_ui08c_fehlerpfad_sanierungsplan_posteingang.py"
    if (Test-Path $checkScript) {
        python $checkScript
        if ($LASTEXITCODE -ne 0) {
            Write-Status "Vorab-Check FEHLGESCHLAGEN" $false
            exit 1
        }
    } else {
        Write-Status "Check-Script nicht gefunden: $checkScript" $false
        exit 1
    }
}

# 3. Runner
if (-not $SkipRunner) {
    Write-Header "3. Runner UI08c"
    $runner = Join-Path $Base "Scripts\python_runner\ui08c_fehlerpfad_sanierungsplan_posteingang.py"
    if (Test-Path $runner) {
        python $runner
        if ($LASTEXITCODE -ne 0) {
            Write-Status "Runner FEHLGESCHLAGEN" $false
            exit 1
        }
    } else {
        Write-Status "Runner nicht gefunden: $runner" $false
        exit 1
    }
}

# 4. Nach-Check
if (-not $SkipCheck) {
    Write-Header "4. Nach-Check UI08c"
    $checkScript = Join-Path $Base "Scripts\python_runner\check_ui08c_fehlerpfad_sanierungsplan_posteingang.py"
    python $checkScript
    if ($LASTEXITCODE -ne 0) {
        Write-Status "Nach-Check FEHLGESCHLAGEN" $false
        exit 1
    }
}

# 5. Ausgabedateien
Write-Header "5. Ausgabedateien"
$ausgaben = @(
    "Windows_App\Logs\UI08C_SANIERUNGSPLAN_BERICHT.txt",
    "Windows_App\Logs\UI08C_SANIERUNGSSTATUS.json",
    "Windows_App\Logs\UI08C_SANIERUNGSPLAN.html",
    "Windows_App\Logs\UI08C_MASSNAHMEN.csv"
)
foreach ($rel in $ausgaben) {
    $pfad = Join-Path $Base $rel
    Write-Status "$rel existiert" (Test-Path $pfad)
}

# 6. Abschluss
Write-Header "UI08c AUTOLAUF ABGESCHLOSSEN"
Write-Host "Rote Linie: produktiv_freigegeben=false | nur_musterdaten=true" -ForegroundColor Magenta
Write-Host "Demo-Betriebsstrecke UI03-UI07b bleibt eingefroren." -ForegroundColor Magenta
