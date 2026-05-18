# UI14 – Ausführungs- und Nachlaufzentrale UI08–UI13 Autolauf
# Führt UI08, UI08b, UI08c, UI09, UI10, UI11, UI12, UI13 in Reihenfolge aus
# Öffnet abschließend UI13 als zentrale HTML-Entscheidungsseite
# Rote Linie: Demo-Modus, keine Produktivfreigabe, keine echten Mandantendaten

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$pythonRunner = Join-Path $projectRoot "Scripts\python_runner\ui14_ausfuehrungs_nachlaufzentrale.py"
$checkFile    = Join-Path $projectRoot "Scripts\python_runner\check_ui14_ausfuehrungs_nachlaufzentrale.py"
$configFile   = Join-Path $projectRoot "Config\ui14_ausfuehrungs_nachlaufzentrale_v1.json"
$logDir       = Join-Path $projectRoot "Windows_App\Logs"

function Test-Prerequisites {
    Write-Host "=== UI14 Ausführungs- und Nachlaufzentrale Autolauf ===" -ForegroundColor Cyan
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

    $py = Join-Path $projectRoot "Tools\Python312\python.exe"
    if (Test-Path $py) {
        $pyVersion = & $py --version 2>$null
        Write-Host "[OK] Projekt-Python erkannt: $pyVersion" -ForegroundColor Green
    } else {
        try {
            $pyVersion = python --version 2>$null
            Write-Host "[OK] System-Python erkannt: $pyVersion" -ForegroundColor Green
        } catch {
            Write-Error "Python nicht verfügbar."
            exit 1
        }
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

function Run-Zentrale {
    Write-Host "`nStarte UI14 Ausführungs- und Nachlaufzentrale..." -ForegroundColor Yellow
    $py = Join-Path $projectRoot "Tools\Python312\python.exe"
    if (Test-Path $py) {
        & $py $pythonRunner
    } else {
        python $pythonRunner
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Error "UI14 Zentrale fehlgeschlagen."
        exit 1
    }
    Write-Host "[OK] UI14 abgeschlossen." -ForegroundColor Green
}

function Show-Results {
    Write-Host "`n=== Ergebnisse ===" -ForegroundColor Cyan

    $reportFile = Join-Path $logDir "UI14_NACHLAUFZENTRALE_BERICHT.txt"
    $summaryFile = Join-Path $logDir "UI14_ZUSAMMENFASSUNG.json"
    $htmlFile = Join-Path $logDir "UI13_ENTSCHEIDUNGSUEBERSICHT.html"

    if (Test-Path $reportFile) {
        Write-Host "[OK] Bericht: $reportFile" -ForegroundColor Green
        Write-Host "`n--- Bericht-Auszug ---" -ForegroundColor Gray
        Get-Content $reportFile -Head 30 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
    } else {
        Write-Warning "Bericht nicht gefunden."
    }

    if (Test-Path $summaryFile) {
        Write-Host "[OK] Zusammenfassung JSON: $summaryFile" -ForegroundColor Green
    } else {
        Write-Warning "Zusammenfassung JSON nicht gefunden."
    }

    if (Test-Path $htmlFile) {
        Write-Host "[OK] UI13-Entscheidungsseite: $htmlFile" -ForegroundColor Green
    } else {
        Write-Warning "UI13-HTML nicht gefunden."
    }

    Write-Host "`nHinweis: Alle Ausführungen basieren auf Musterdaten (Demo-Modus)." -ForegroundColor Cyan
    Write-Host "UI03–UI07b werden nicht berührt." -ForegroundColor Cyan
}

# Hauptablauf
Test-Prerequisites
Run-SelfTest
Run-Zentrale
Show-Results

Write-Host "`nUI14 Autolauf erfolgreich abgeschlossen." -ForegroundColor Green
