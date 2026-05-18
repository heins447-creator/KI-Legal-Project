# UI13 – Abnahme- und Entscheidungsübersicht UI08–UI12 Autolauf
# Erzeugt eine HTML-/Browser-Übersicht über den Status von UI08 bis UI12
# Rote Linie: Demo-Modus, keine Produktivfreigabe, keine echten Mandantendaten

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$pythonRunner = Join-Path $projectRoot "Scripts\python_runner\ui13_abnahme_entscheidungsuebersicht.py"
$checkFile    = Join-Path $projectRoot "Scripts\python_runner\check_ui13_abnahme_entscheidungsuebersicht.py"
$configFile   = Join-Path $projectRoot "Config\ui13_abnahme_entscheidungsuebersicht_v1.json"
$logDir       = Join-Path $projectRoot "Windows_App\Logs"

function Test-Prerequisites {
    Write-Host "=== UI13 Abnahme- und Entscheidungsübersicht Autolauf ===" -ForegroundColor Cyan
    Write-Host "Prüfe Voraussetzungen..."

    if (-not (Test-Path $pythonRunner)) {
        Write-Error "Python-Runner nicht gefunden: $pythonRunner"
        exit 1
    }
    Write-Host "[OK] Python-Runner vorhanden." -ForegroundColor Green

    if (-not (Test-Path $checkFile)) {
        Write-Error "Prüfdatei nicht gefunden: $checkFile"
        exit 1
    }
    Write-Host "[OK] Prüfdatei vorhanden." -ForegroundColor Green

    if (-not (Test-Path $configFile)) {
        Write-Error "Config nicht gefunden: $configFile"
        exit 1
    }
    Write-Host "[OK] Config vorhanden." -ForegroundColor Green

    try {
        $pyVersion = python --version 2>$null
        if (-not $pyVersion) {
            $py = Join-Path $projectRoot "Tools\Python312\python.exe"
            if (Test-Path $py) {
                $pyVersion = & $py --version 2>$null
                Write-Host "[OK] Projekt-Python erkannt: $pyVersion" -ForegroundColor Green
            } else {
                Write-Error "Python nicht verfügbar."
                exit 1
            }
        } else {
            Write-Host "[OK] Python erkannt: $pyVersion" -ForegroundColor Green
        }
    } catch {
        Write-Error "Python nicht verfügbar."
        exit 1
    }

    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        Write-Host "[OK] Log-Verzeichnis erstellt: $logDir" -ForegroundColor Green
    }
}

function Run-SelfTest {
    Write-Host "`nStarte Selbsttest..." -ForegroundColor Yellow
    $py = Join-Path $projectRoot "Tools\Python312\python.exe"
    if (Test-Path $py) {
        & $py $checkFile
    } else {
        python $checkFile
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Selbsttest fehlgeschlagen."
        exit 1
    }
    Write-Host "[OK] Selbsttest bestanden." -ForegroundColor Green
}

function Run-Overview {
    Write-Host "`nStarte UI13 Entscheidungsübersicht..." -ForegroundColor Yellow
    $py = Join-Path $projectRoot "Tools\Python312\python.exe"
    if (Test-Path $py) {
        & $py $pythonRunner
    } else {
        python $pythonRunner
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Error "UI13 Entscheidungsübersicht fehlgeschlagen."
        exit 1
    }
    Write-Host "[OK] UI13 abgeschlossen." -ForegroundColor Green
}

function Show-Results {
    Write-Host "`n=== Ergebnisse ===" -ForegroundColor Cyan

    $htmlFile = Join-Path $logDir "UI13_ENTSCHEIDUNGSUEBERSICHT.html"
    $jsonFile = Join-Path $logDir "UI13_ENTSCHEIDUNGSUEBERSICHT.json"
    $reportFile = Join-Path $logDir "UI13_ENTSCHEIDUNGSUEBERSICHT_BERICHT.txt"

    if (Test-Path $htmlFile) {
        Write-Host "[OK] HTML-Übersicht: $htmlFile" -ForegroundColor Green
    } else {
        Write-Warning "HTML-Übersicht nicht gefunden."
    }

    if (Test-Path $jsonFile) {
        Write-Host "[OK] JSON-Übersicht: $jsonFile" -ForegroundColor Green
    } else {
        Write-Warning "JSON-Übersicht nicht gefunden."
    }

    if (Test-Path $reportFile) {
        Write-Host "[OK] Text-Bericht: $reportFile" -ForegroundColor Green
        Write-Host "`n--- Bericht-Auszug ---" -ForegroundColor Gray
        Get-Content $reportFile -Head 20 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
    } else {
        Write-Warning "Text-Bericht nicht gefunden."
    }

    Write-Host "`nHinweis: Alle Ausgaben basieren auf Musterdaten (Demo-Modus)." -ForegroundColor Cyan
    Write-Host "UI03–UI07b werden nicht berührt." -ForegroundColor Cyan
}

# Hauptablauf
Test-Prerequisites
Run-SelfTest
Run-Overview
Show-Results

Write-Host "`nUI13 Autolauf erfolgreich abgeschlossen." -ForegroundColor Green
