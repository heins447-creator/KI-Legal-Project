# UI12 – Kombinierter Master-Adapter Autolauf
# Führt UI10 (Profil-Leseadapter) und UI11 (Register-Leseadapter) zusammen
# Erzeugt: Master-Adapter JSON, HTML-Bericht, Konsistenzlog, Text-Bericht
# Rote Linie: Demo-Modus, keine Produktivfreigabe, keine echten Mandantendaten

$ErrorActionPreference = "Stop"

# Pfade ermitteln
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$pythonRunner = Join-Path $projectRoot "Scripts\python_runner\ui12_master_adapter.py"
$checkFile    = Join-Path $projectRoot "Scripts\python_runner\check_ui12_master_adapter.py"
$configFile   = Join-Path $projectRoot "Config\ui12_master_adapter_v1.json"
$logDir       = Join-Path $projectRoot "Windows_App\Logs"

function Test-Prerequisites {
    Write-Host "=== UI12 Master-Adapter Autolauf ===" -ForegroundColor Cyan
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

    # Python-Version prüfen
    try {
        $pyVersion = python --version 2>&1
        Write-Host "[OK] Python erkannt: $pyVersion" -ForegroundColor Green
    } catch {
        Write-Error "Python nicht verfügbar."
        exit 1
    }

    # Log-Verzeichnis sicherstellen
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        Write-Host "[OK] Log-Verzeichnis erstellt: $logDir" -ForegroundColor Green
    }
}

function Run-SelfTest {
    Write-Host "`nStarte Selbsttest..." -ForegroundColor Yellow
    $result = python $checkFile
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Selbsttest fehlgeschlagen."
        exit 1
    }
    Write-Host "[OK] Selbsttest bestanden." -ForegroundColor Green
}

function Run-MasterAdapter {
    Write-Host "`nStarte UI12 Master-Adapter..." -ForegroundColor Yellow
    $result = python $pythonRunner
    if ($LASTEXITCODE -ne 0) {
        Write-Error "UI12 Master-Adapter fehlgeschlagen."
        exit 1
    }
    Write-Host "[OK] UI12 Master-Adapter abgeschlossen." -ForegroundColor Green
}

function Show-Results {
    Write-Host "`n=== Ergebnisse ===" -ForegroundColor Cyan

    $jsonFile = Join-Path $logDir "UI12_MASTER_ADAPTER.json"
    $htmlFile = Join-Path $logDir "UI12_MASTER_ADAPTER.html"
    $reportFile = Join-Path $logDir "UI12_MASTER_ADAPTER_BERICHT.txt"

    if (Test-Path $jsonFile) {
        Write-Host "[OK] Master-Adapter JSON: $jsonFile" -ForegroundColor Green
    } else {
        Write-Warning "Master-Adapter JSON nicht gefunden."
    }

    if (Test-Path $htmlFile) {
        Write-Host "[OK] HTML-Bericht: $htmlFile" -ForegroundColor Green
    } else {
        Write-Warning "HTML-Bericht nicht gefunden."
    }

    if (Test-Path $reportFile) {
        Write-Host "[OK] Text-Bericht: $reportFile" -ForegroundColor Green
        Write-Host "`n--- Bericht-Auszug ---" -ForegroundColor Gray
        Get-Content $reportFile -Head 20 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
    } else {
        Write-Warning "Text-Bericht nicht gefunden."
    }

    Write-Host "`nHinweis: Alle Ausgaben basieren auf Musterdaten (Demo-Modus)." -ForegroundColor Cyan
    Write-Host "Keine Produktivfreigabe. UI03-UI07b werden nicht berührt." -ForegroundColor Cyan
}

# Hauptablauf
Test-Prerequisites
Run-SelfTest
Run-MasterAdapter
Show-Results

Write-Host "`nUI12 Autolauf erfolgreich abgeschlossen." -ForegroundColor Green
