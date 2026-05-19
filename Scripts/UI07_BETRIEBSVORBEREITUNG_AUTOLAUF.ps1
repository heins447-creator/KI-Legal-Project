# UI07 – Betriebsvorbereitung ohne Produktivfreigabe
# Autolauf: Startet den Python-Runner und öffnet die Prüfstartseite
# ROTE LINIE: betriebsbereit vorbereiten, aber NICHT produktiv setzen

$ErrorActionPreference = "Stop"
$BaseDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Runner = Join-Path $BaseDir "Scripts\python_runner\ui07_betriebsvorbereitung.py"
$Config = Join-Path $BaseDir "Config\ui07_betriebsvorbereitung_v1.json"
$HtmlOut = Join-Path $BaseDir "Windows_App\Pruefseiten\UI07_Betriebsvorbereitung.html"
$LogDir = Join-Path $BaseDir "Windows_App\Logs"

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $Message"
    Write-Host $line
    $line | Out-File (Join-Path $LogDir "UI07_Betriebsvorbereitung.log") -Append -Encoding utf8
}

# Verzeichnisse sicherstellen
@("Windows_App\Logs","Windows_App\Pruefseiten","Windows_App\Backup","Windows_App\Temp","Windows_App\Daten") | ForEach-Object {
    $d = Join-Path $BaseDir $_
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

Write-Log "========================================"
Write-Log "UI07 Betriebsvorbereitung – AUTOLAUF"
Write-Log "========================================"
Write-Log "WARNUNG: Dies ist eine Vorbereitung. KEINE Produktivfreigabe."
Write-Log ""

# Python-Prüfung
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) {
    Write-Log "FEHLER: Python nicht gefunden."
    exit 1
}
Write-Log "Python gefunden: $($py.Source)"

# Config-Prüfung
if (-not (Test-Path $Config)) {
    Write-Log "FEHLER: Config nicht gefunden: $Config"
    exit 1
}
Write-Log "Config OK: $Config"

# Runner-Prüfung
if (-not (Test-Path $Runner)) {
    Write-Log "FEHLER: Runner nicht gefunden: $Runner"
    exit 1
}
Write-Log "Runner OK: $Runner"

# Selbsttest
Write-Log ""
Write-Log "[1/3] Selbsttest..."
& $py $Runner --check
if ($LASTEXITCODE -ne 0) {
    Write-Log "FEHLER: Selbsttest fehlgeschlagen."
    exit 1
}
Write-Log "Selbsttest OK."

# Hauptlauf
Write-Log ""
Write-Log "[2/3] Hauptlauf..."
Set-Location $BaseDir
& $py $Runner
if ($LASTEXITCODE -ne 0) {
    Write-Log "WARNUNG: Hauptlauf meldet Fehler (Exit $LASTEXITCODE)."
} else {
    Write-Log "Hauptlauf OK."
}

# Prüfstartseite öffnen
Write-Log ""
Write-Log "[3/3] Prüfstartseite öffnen..."
if (Test-Path $HtmlOut) {
    Start-Process $HtmlOut
    Write-Log "Prüfstartseite geöffnet: $HtmlOut"
} else {
    Write-Log "WARNUNG: Prüfstartseite nicht gefunden: $HtmlOut"
}

Write-Log ""
Write-Log "========================================"
Write-Log "UI07 Autolauf abgeschlossen."
Write-Log "HINWEIS: System ist vorbereitet, aber NICHT produktiv freigegeben."
Write-Log "========================================"
