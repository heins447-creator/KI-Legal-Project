# UI08 – Posteingang / Importstrecke – Visuelle Arbeitsübersicht
# Autolauf: Selbsttest → Hauptlauf → Browser
# ROTE LINIE: Demo-Ausbaustufe. Keine Produktivfreigabe.

$ErrorActionPreference = "Stop"
$BaseDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Runner = Join-Path $BaseDir "Scripts\python_runner\ui08_posteingang_importstrecke.py"
$Config = Join-Path $BaseDir "Config\ui08_posteingang_importstrecke_v1.json"
$HtmlOut = Join-Path $BaseDir "Windows_App\Pruefseiten\UI08_Posteingang_Uebersicht.html"
$LogDir = Join-Path $BaseDir "Windows_App\Logs"

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $Message"
    Write-Host $line
    $line | Out-File (Join-Path $LogDir "UI08_Posteingang.log") -Append -Encoding utf8
}

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

Write-Log "========================================"
Write-Log "UI08 Posteingang / Importstrecke – AUTOLAUF"
Write-Log "========================================"
Write-Log "WARNUNG: Demo-Ausbaustufe. Keine Produktivfreigabe."
Write-Log ""

# Python
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) {
    Write-Log "FEHLER: Python nicht gefunden."
    exit 1
}
Write-Log "Python: $($py.Source)"

# Config
if (-not (Test-Path $Config)) {
    Write-Log "FEHLER: Config nicht gefunden: $Config"
    exit 1
}
Write-Log "Config OK"

# Runner
if (-not (Test-Path $Runner)) {
    Write-Log "FEHLER: Runner nicht gefunden: $Runner"
    exit 1
}
Write-Log "Runner OK"

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
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    Write-Log "WARNUNG: Hauptlauf meldet Fehler (Exit $exitCode)."
} else {
    Write-Log "Hauptlauf OK."
}

# Posteingang-Übersicht öffnen
Write-Log ""
Write-Log "[3/3] Posteingang-Übersicht öffnen..."
if (Test-Path $HtmlOut) {
    Start-Process $HtmlOut
    Write-Log "Posteingang-Übersicht geöffnet: $HtmlOut"
} else {
    Write-Log "WARNUNG: HTML nicht gefunden: $HtmlOut"
}

Write-Log ""
Write-Log "========================================"
Write-Log "UI08 Autolauf abgeschlossen."
Write-Log "Demo-Ausbaustufe. Keine Produktivfreigabe."
Write-Log "========================================"
