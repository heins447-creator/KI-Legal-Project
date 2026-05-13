<#
.SYNOPSIS
    KM14 – Maschinenformat / Fundstellenstruktur
.DESCRIPTION
    Liest KM12 (Arbeitsabbildungen, Koordinaten) und KM13 (OCR).
    Erzeugt maschinenlesbare Fundstellenstruktur.
    KEINE Originalaenderung, KEINE OCR-Neuausfuehrung,
    KEINE Uebersetzung, KEINE Rechtsbewertung.
#>
param(
    [switch]$OnlySelfTest,
    [switch]$SkipSelfTest,
    [switch]$SkipCheck
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0
try { chcp.com 65001 | Out-Null } catch {}
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}
$ProjectRoot = "I:\KI_Legal_Project"
$LogRoot = Join-Path $ProjectRoot "Agentensteuerung\14_Maschinenformat_Fundstellenstruktur\90_RunLogs"
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogRoot "RUN_KM14_$Stamp.log"
if ($PSVersionTable.PSVersion.Major -lt 6) { $Host.UI.RawUI.WindowTitle = "KM14" }
$Python = Join-Path $ProjectRoot "Tools\Python312\python.exe"
$Runner = Join-Path $ProjectRoot "Scripts\python_runner\km14_maschinenformat_fundstellenstruktur.py"
$Check  = Join-Path $ProjectRoot "Scripts\python_runner\check_km14_maschinenformat_fundstellenstruktur.py"
Push-Location -LiteralPath $ProjectRoot
$BOM = [System.Text.Encoding]::UTF8.GetString([System.Text.Encoding]::UTF8.GetPreamble())
Add-Content -LiteralPath $LogFile -Value "KM14 START" -Encoding UTF8
if (-not (Test-Path $Python)) { throw "Python nicht gefunden: $Python" }
if (-not (Test-Path $Runner)) { throw "Runner fehlt: $Runner" }
if (-not (Test-Path $Check))  { throw "Check fehlt: $Check" }
try {
    & $Python -m py_compile $Runner 2>&1 | Out-File -LiteralPath $LogFile -Append -Encoding UTF8
    if ($LASTEXITCODE -ne 0) { throw "py_compile fehlgeschlagen" }
    if ($OnlySelfTest) {
        & $Python $Runner --selftest 2>&1 | Tee-Object -FilePath $LogFile -Append
        if ($LASTEXITCODE -ne 0) { throw "Selbsttest fehlgeschlagen" }
        Pop-Location
        exit 0
    }
    if (-not $SkipSelfTest) {
        & $Python $Runner --selftest 2>&1 | Tee-Object -FilePath $LogFile -Append
        if ($LASTEXITCODE -ne 0) { throw "Selbsttest fehlgeschlagen" }
    }
    & $Python $Runner 2>&1 | Tee-Object -FilePath $LogFile -Append
    if ($LASTEXITCODE -ne 0) { throw "Hauptlauf fehlgeschlagen" }
    if (-not $SkipCheck) {
        & $Python $Check 2>&1 | Tee-Object -FilePath $LogFile -Append
        if ($LASTEXITCODE -ne 0) { throw "Pruefdatei fehlgeschlagen" }
    }
    Add-Content -LiteralPath $LogFile -Value "KM14 ERFOLGREICH" -Encoding UTF8
    Write-Host "KM14 ERFOLGREICH" -ForegroundColor Green
    Write-Host "Log: $LogFile"
    Write-Host "Naechster: KM15 oder KM13b"
    Pop-Location
    exit 0
}
catch {
    Add-Content -LiteralPath $LogFile -Value "KM14 FEHLER: $_" -Encoding UTF8
    Write-Host "KM14 FEHLER: $_" -ForegroundColor Red
    Write-Host "Log: $LogFile"
    Pop-Location
    exit 1
}
